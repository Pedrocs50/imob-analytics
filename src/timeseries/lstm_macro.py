from __future__ import annotations

import os
import time
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.analysis.utils import md, salvar_fig
from src.timeseries.arima_plus import _arima_log, ler_cidades
from src.timeseries.lstm_painel import ALVOS, H, HORIZONTES, JANELA, REAJUSTE_A_CADA, dm, treinar_lstm
from src.timeseries.panel import carregar_wide, montar_paineis

REPORT = os.path.join("reports", "results", "lstm_macro.md")
REPORT_TESTE = os.path.join("reports", "results", "lstm_macro_teste.md")
TAB_DIR = os.path.join("reports", "results", "lstm_macro")
SEMENTES = (11, 22, 33, 44, 55)
ALFA_RIDGE = 5.0
ORIGENS_TESTE = 14  # no modo rapido: so as primeiras origens (2 reajustes) de SJC

# preditores macro (painel "as-of": cada mes so contem o que ja estava publicado) e a transformacao que os torna estacionarios
MACRO = {
    "bcb_selic_meta": "dif",
    "bcb_ipca": "nivel",
    "bcb_incc": "nivel",
    "bcb_ptax": "pct",
    "bcb_ibcbr": "pct",
    "bcb_credimob_saldo": "pct",
    "ipea_icc": "dif",
    "selic_real_mes": "nivel",
}
# subconjuntos definidos antes deste experimento (ARIMAX de `arima_plus.py`), nao ajustados aos resultados daqui
SUBCONJUNTOS = {
    "juros e confianca": ["bcb_selic_meta", "ipea_icc"],
    "credito + juros + confianca + IBC-Br": ["bcb_credimob_saldo", "bcb_selic_meta", "ipea_icc", "bcb_ibcbr"],
}
REF, TEND = "ARIMA(0,2,3)", "Tendencia (12 meses)"
RL_ALVO = "Regressao linear (so o alvo)"
RL_MACRO = "Regressao linear (alvo + macro)"
RL_SUB = {n: f"Regressao linear (alvo + {n})" for n in SUBCONJUNTOS}
LSTM_SEM = "LSTM painel (sem macro)"
LSTM_COM = "LSTM painel + macro"
LSTM_SUB = {n: f"LSTM painel + {n}" for n in SUBCONJUNTOS}
# nome da rede -> colunas de macro usadas (None = sem macro)
REDES = {LSTM_SEM: None, LSTM_COM: list(MACRO), **{LSTM_SUB[n]: c for n, c in SUBCONJUNTOS.items()}}
REGRESSOES = {RL_ALVO: None, RL_MACRO: list(MACRO), **{RL_SUB[n]: c for n, c in SUBCONJUNTOS.items()}}
MODELOS = [REF, TEND, *REGRESSOES, *REDES]

torch.set_num_threads(4)


# ----------------------------------------------------------------------------- dados
def macro_as_of(mensal: pd.DataFrame) -> pd.DataFrame:
    """Preditores macro estacionarios, calculados so com o passado (ffill e diferencas nao olham o futuro)."""
    colunas = {}
    for col, tipo in MACRO.items():
        s = mensal[col].ffill()
        colunas[col] = s.diff() if tipo == "dif" else s.pct_change(fill_method=None) * 100 if tipo == "pct" else s
    return pd.DataFrame(colunas)


def amostras(g: pd.DataFrame, macro_z: pd.DataFrame, cidades: list[str], colunas: list[str] | None):
    """Janelas (12 meses de crescimento padronizado [+ macro padronizado] -> proximos 12 meses). Cada janela de uma
    cidade usa o macro das MESMAS datas: o macro e comum a todas, o que multiplica os exemplos sem inventar dados."""
    X, Y, D = [], [], []
    for c in cidades:
        s = g[c].dropna()
        sd = s.std()
        if len(s) < JANELA + H + 5 or not np.isfinite(sd) or sd == 0:
            continue
        z = (s / sd).to_numpy(dtype=np.float32)
        feats = np.column_stack([z, macro_z[colunas].reindex(s.index).to_numpy(dtype=np.float32)]) if colunas else z[:, None]
        datas = s.index.to_numpy()
        for t in range(JANELA, len(z) - H + 1):
            x = feats[t - JANELA:t]
            if np.isfinite(x).all():
                X.append(x); Y.append(z[t:t + H]); D.append(datas[t + H - 1])
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32), np.ones(len(X), dtype=np.float32), np.array(D)


def prever_lstm(redes, g_alvo: pd.Series, macro_z: pd.DataFrame, sd_alvo: float, colunas: list[str] | None) -> dict[int, float]:
    janela = g_alvo.iloc[-JANELA:]
    z = (janela / sd_alvo).to_numpy(dtype=np.float32)
    x = np.column_stack([z, macro_z[colunas].reindex(janela.index).to_numpy(dtype=np.float32)]) if colunas else z[:, None]
    with torch.no_grad():
        yz = np.mean([r(torch.tensor(x).unsqueeze(0)).numpy()[0] for r in redes], axis=0)
    cum = np.cumsum(yz)
    return {h: float(cum[h - 1] * sd_alvo / 100) for h in HORIZONTES}


def reajustar(g: pd.DataFrame, g_alvo: pd.Series, macro: pd.DataFrame, T: pd.Timestamp, cidades: list[str], sementes) -> dict:
    """Treina as redes (sem macro, com todo o macro e com cada subconjunto) so com dados ate T. A escala do macro vem so do treino."""
    gT, galvoT, macroT = g.loc[:T], g_alvo.loc[:T], macro.loc[:T]
    macro_z = (macro - macroT.mean()) / macroT.std().replace(0, 1)
    gp = gT.copy()
    gp["alvo"] = galvoT
    lista = cidades + ["alvo"]
    redes = {}
    for nome, colunas in REDES.items():
        X, Y, W, D = amostras(gp, macro_z, lista, colunas)
        redes[nome] = [treinar_lstm(X, Y, W, D, s) for s in sementes]
        redes[nome + "_n"] = len(X)
    return {"redes": redes, "macro_z": macro_z, "sd_alvo": float(galvoT.std())}


# ----------------------------------------------------------------------------- regressao tradicional
def atributos_regressao(g_alvo: pd.Series, macro: pd.DataFrame) -> pd.DataFrame:
    """Crescimento recente do alvo (3 e 12 meses, so passado) e macro do mes."""
    return pd.DataFrame({"cresc_3m": g_alvo.rolling(3).sum(), "cresc_12m": g_alvo.rolling(12).sum()}).join(macro)


def regressao(y: pd.Series, F: pd.DataFrame, i: int, macro_cols: list[str] | None) -> dict[int, float]:
    """Ridge direto por horizonte: variacao acumulada em log nos proximos h meses ~ atributos no mes t.
    Treina so com pares (t, t+h) ja observados ate a origem i (janela expansiva)."""
    cols = ["cresc_3m", "cresc_12m"] + (macro_cols or [])
    saida = {}
    for h in HORIZONTES:
        t = np.arange(0, i - h + 1)
        X = F[cols].iloc[t]
        r = y.iloc[t + h].to_numpy() - y.iloc[t].to_numpy()
        ok = X.notna().all(axis=1).to_numpy()
        esc = StandardScaler().fit(X[ok])
        modelo = Ridge(alpha=ALFA_RIDGE).fit(esc.transform(X[ok]), r[ok])
        saida[h] = float(modelo.predict(esc.transform(F[cols].iloc[[i]]))[0])
    return saida


# ----------------------------------------------------------------------------- walk-forward
def walk_forward(y: pd.Series, n0: int, precos: pd.DataFrame, macro: pd.DataFrame, nome_alvo: str, sementes, limite: int | None = None):
    n = len(y)
    precos = precos.reindex(y.index.union(precos.index)).sort_index()
    g = np.log(precos).diff() * 100
    g_alvo = y.diff() * 100
    macro = macro.reindex(g.index)
    F = atributos_regressao(g_alvo, macro.reindex(y.index))
    cidades = [c for c in precos.columns if not (nome_alvo.startswith("SJC") and c.startswith("São José dos Campos"))]
    linhas, tamanhos = [], []
    conj = None
    fim = n - 1 if limite is None else min(n - 1, n0 - 1 + limite)
    for i in range(n0 - 1, fim):
        T = y.index[i]
        if (i - (n0 - 1)) % REAJUSTE_A_CADA == 0:
            t0 = time.time()
            conj = reajustar(g, g_alvo, macro, T, cidades, sementes)
            tamanhos.append((T, conj["redes"][LSTM_SEM + "_n"], conj["redes"][LSTM_COM + "_n"]))  # amostras (sem / com macro)
            print(f"[LSTM-MACRO] {nome_alvo}: reajuste em {T:%Y-%m} ({time.time() - t0:.0f}s)", flush=True)
        passado = y.iloc[: i + 1]
        arima, _, _ = _arima_log(passado)
        c12 = passado.diff().iloc[-12:].mean()
        gprev = g_alvo.iloc[: i + 1]
        rl = {m: regressao(y, F, i, cols) for m, cols in REGRESSOES.items()}
        rn = {m: prever_lstm(conj["redes"][m], gprev, conj["macro_z"], conj["sd_alvo"], cols) for m, cols in REDES.items()}
        for h in HORIZONTES:
            if i + h >= n:
                continue
            linha = {"origem": T, "h": h, "real": y.iloc[i + h], "ultimo": passado.iloc[-1], REF: arima[h - 1], TEND: passado.iloc[-1] + h * c12}
            linha.update({m: passado.iloc[-1] + v[h] for m, v in {**rl, **rn}.items()})
            linhas.append(linha)
    return pd.DataFrame(linhas), tamanhos


# ----------------------------------------------------------------------------- avaliacao
def metricas(wf: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for h, gh in wf.groupby("h"):
        real = np.exp(gh["real"])
        for m in MODELOS:
            erro = real - np.exp(gh[m])
            linhas.append({"h (meses)": h, "modelo": m, "n origens": len(gh), "MAE": float(erro.abs().mean()),
                           "RMSE": float(np.sqrt((erro ** 2).mean())), "MAPE (%)": float((erro.abs() / real).mean() * 100)})
    t = pd.DataFrame(linhas)
    base = t[t["modelo"] == REF].set_index("h (meses)")["RMSE"]
    t["RMSE relativo ao ARIMA"] = t["RMSE"] / t["h (meses)"].map(base)
    return t


def comparacoes(wf: pd.DataFrame) -> pd.DataFrame:
    pares = [(m, REF) for m in (*REDES, *REGRESSOES) if m != RL_ALVO] + [(m, LSTM_SEM) for m in REDES if m != LSTM_SEM]
    pares += [(m, RL_ALVO) for m in REGRESSOES if m != RL_ALVO]
    return pd.concat([dm(wf, a, b) for a, b in pares], ignore_index=True)


def figura(res: dict) -> str:
    fig, eixos = plt.subplots(1, len(res), figsize=(7.2 * len(res), 5))
    for eixo, (nome, r) in zip(np.atleast_1d(eixos), res.items()):
        piv = r["met"].pivot(index="h (meses)", columns="modelo", values="MAPE (%)")[MODELOS]
        piv.plot.bar(ax=eixo, rot=0, width=0.85)
        eixo.set_title(f"{nome}: MAPE por horizonte", fontsize=10)
        eixo.set_xlabel("horizonte (meses)")
        eixo.set_ylabel("MAPE (%)")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend(fontsize=6)
    fig.tight_layout()
    return salvar_fig(fig, "lstm_macro_comparacao.png")


def executar(rapido: bool = False) -> dict:
    warnings.filterwarnings("ignore")
    inicio = time.time()
    wide, meta = carregar_wide()
    paineis = montar_paineis(wide, meta)
    ref, macro = paineis.mensal_referencia, macro_as_of(paineis.mensal)
    precos = ler_cidades()
    alvos = {k: v for k, v in ALVOS.items() if k.startswith("SJC")} if rapido else ALVOS
    sementes = SEMENTES[:1] if rapido else SEMENTES
    os.makedirs(TAB_DIR, exist_ok=True)
    res = {}
    for nome, (col, n0) in alvos.items():
        y = np.log(ref[col].dropna())
        y.index = pd.DatetimeIndex(y.index, freq="MS")
        wf, tamanhos = walk_forward(y, n0, precos, macro, nome, sementes, ORIGENS_TESTE if rapido else None)
        slug = nome.split()[0] + ("_teste" if rapido else "")
        wf.to_csv(os.path.join(TAB_DIR, f"lstm_macro_{slug}_previsoes.csv"), index=False)
        met, dms = metricas(wf), comparacoes(wf)
        met.to_csv(os.path.join(TAB_DIR, f"lstm_macro_{slug}_metricas.csv"), index=False)
        dms.to_csv(os.path.join(TAB_DIR, f"lstm_macro_{slug}_dm.csv"), index=False)
        res[nome] = {"met": met, "dm": dms, "tamanhos": tamanhos, "n_origens": wf["origem"].nunique()}
    fig = figura(res) if not rapido else None
    escrever_relatorio(res, fig, time.time() - inicio, len(sementes), rapido)
    print(f"[LSTM-MACRO] concluido em {(time.time() - inicio) / 60:.1f} min")
    return res


def escrever_relatorio(res: dict, fig: str | None, segundos: float, n_sementes: int, rapido: bool) -> None:
    L = ["# LSTM com indicadores macroeconomicos x regressao tradicional e ARIMA", "",
         "Gerado por `python main.py lstm-macro`. Nao editar manualmente." + (" **MODO TESTE: poucas origens e 1 semente; nao usar os numeros.**" if rapido else ""), "",
         f"Alvos: crescimento do preco medio de venda residencial do FipeZAP em **SJC** (proxy de Jacarei, que nao esta no FipeZAP) e no **indice nacional**. "
         f"Entrada do LSTM: ultimos {JANELA} meses de crescimento padronizado de **50 cidades** (painel) e, na variante com macro, "
         f"{len(MACRO)} indicadores do BCB e do IPEA ({', '.join(MACRO)}); saida direta de {H} meses. Media de {n_sementes} sementes; "
         f"reajuste a cada {REAJUSTE_A_CADA} meses; walk-forward com janela expansiva (mesmos horizontes, ARIMA e testes dos demais relatorios).", "",
         "- **Sem vazamento:** o macro vem do painel *as-of* (cada mes so contem o que ja estava publicado) e sua escala e calculada so com o treino de cada reajuste.",
         f"- **Regressao tradicional:** Ridge (alfa {ALFA_RIDGE}) direta por horizonte, com crescimento de 3 e 12 meses do alvo (e o macro do mes, na variante com macro), reajustada todo mes.",
         "- **Ablacao:** todas as redes usam a mesma construcao e as mesmas sementes; a diferenca para `LSTM painel (sem macro)` e o efeito do macro. "
         "Alem do conjunto completo, testam-se dois subconjuntos definidos antes (ARIMAX de `arima_plus.py`): "
         + "; ".join(f"{n} ({', '.join(c)})" for n, c in SUBCONJUNTOS.items()) + ". Todos os modelos testados estao reportados.",
         "- **Caracteristicas dos imoveis:** entram pelo modelo de precificacao de Jacarei (R$/m2 por anuncio, `docs/MODELOS_AVANCADOS.md`), combinado com a tendencia "
         "prevista aqui em `docs/PROJECAO_JACAREI.md`. O VivaReal e uma fotografia de um unico mes; nao ha historico de anuncios para alimentar o LSTM.", "",
         f"Tempo total: {segundos / 60:.1f} min.", ""]
    for nome, r in res.items():
        L += [f"## {nome} ({r['n_origens']} origens)", "", "### Erro por horizonte (MAE e RMSE em R$/m2; MAPE em %)", "", md(r["met"].round(3), 3), "",
              "### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)", "", md(r["dm"].round(3), 3), "",
              "### Amostras de treino por reajuste (sem macro / com macro)", ""]
        L += [f"- {T:%Y-%m}: {a} / {b}" for T, a, b in r["tamanhos"]]
        L.append("")
    if fig:
        L += ["## Figura", "", f"- `{fig}`", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT_TESTE if rapido else REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
