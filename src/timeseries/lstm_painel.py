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
import torch.nn as nn
from sklearn.ensemble import HistGradientBoostingRegressor

from src.analysis.utils import md, salvar_fig
from src.timeseries.arima import diebold_mariano
from src.timeseries.arima_plus import ORDEM, _arima_log, ler_cidades
from src.timeseries.panel import carregar_wide, montar_paineis

REPORT = os.path.join("reports", "results", "lstm.md")
TAB_DIR = os.path.join("reports", "results", "lstm")
HORIZONTES = (1, 3, 6, 12)
JANELA = 12  # meses de crescimento usados como entrada
H = 12  # meses previstos (saida direta)
K_PARECIDAS = 10
REAJUSTE_A_CADA = 12  # origens entre reajustes dos modelos
SEMENTES = (11, 22, 33)
ALVOS = {"SJC (nominal)": ("fipezap_sjc_res_venda_preco_m2", 60), "nacional (nominal)": ("fipezap_nacional_res_venda_preco_m2", 84)}
REF, TEND = "ARIMA(0,2,3)", "Tendencia (12 meses)"
LSTM_CONTROLE = "LSTM controle (so o alvo)"
LSTM_TODAS = "LSTM painel (todas as cidades)"
LSTM_PARECIDAS = f"LSTM painel ({K_PARECIDAS} mais parecidas)"
LSTM_PONDERADO = "LSTM painel ponderado por semelhanca"
GB_TODAS = "GB global (todas as cidades)"
GB_PARECIDAS = f"GB global ({K_PARECIDAS} mais parecidas)"
MODELOS = [REF, TEND, LSTM_CONTROLE, LSTM_TODAS, LSTM_PARECIDAS, LSTM_PONDERADO, GB_TODAS, GB_PARECIDAS]

torch.set_num_threads(4)


# ----------------------------------------------------------------------------- dados
class Rede(nn.Module):
    def __init__(self, oculto: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(1, oculto, batch_first=True)
        self.drop = nn.Dropout(0.1)
        self.saida = nn.Linear(oculto, H)

    def forward(self, x):
        o, _ = self.lstm(x)
        return self.saida(self.drop(o[:, -1, :]))


def amostras(g: pd.DataFrame, cidades: list[str], pesos: dict[str, float] | None = None):
    """Janelas (12 meses de crescimento padronizado -> proximos 12 meses) das cidades dadas.
    O desvio-padrao de cada cidade vem so do periodo de treino (g ja esta cortado na origem)."""
    X, Y, W, D = [], [], [], []
    for c in cidades:
        s = g[c].dropna()
        sd = s.std()
        if len(s) < JANELA + H + 5 or not np.isfinite(sd) or sd == 0:
            continue
        z = (s / sd).to_numpy()
        datas = s.index.to_numpy()
        for t in range(JANELA, len(z) - H + 1):
            X.append(z[t - JANELA:t]); Y.append(z[t:t + H]); W.append(1.0 if pesos is None else pesos.get(c, 0.0)); D.append(datas[t + H - 1])
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32), np.array(W, dtype=np.float32), np.array(D)


def semelhanca(precos_log: pd.DataFrame, alvo_log: pd.Series, T: pd.Timestamp) -> pd.Series:
    """Correlacao do crescimento de 12 meses de cada cidade com o do alvo, usando so dados ate T."""
    a = alvo_log.loc[:T].diff(12)
    corr = {}
    for c in precos_log.columns:
        par = pd.concat([a, precos_log[c].loc[:T].diff(12)], axis=1).dropna()
        corr[c] = par.iloc[:, 0].corr(par.iloc[:, 1]) if len(par) >= 24 else np.nan
    return pd.Series(corr)


def treinar_lstm(X, Y, W, D, semente: int) -> Rede:
    torch.manual_seed(semente)
    np.random.seed(semente)
    ordem = np.argsort(D)
    X, Y, W = X[ordem], Y[ordem], W[ordem]
    n_val = max(int(len(X) * 0.15), 3)
    tr, va = slice(0, len(X) - n_val), slice(len(X) - n_val, len(X))  # validacao = amostras mais recentes
    xt, yt, wt = torch.tensor(X[tr]).unsqueeze(-1), torch.tensor(Y[tr]), torch.tensor(W[tr])
    xv, yv, wv = torch.tensor(X[va]).unsqueeze(-1), torch.tensor(Y[va]), torch.tensor(W[va])
    rede = Rede()
    otim = torch.optim.Adam(rede.parameters(), lr=2e-3, weight_decay=1e-4)
    melhor, estado, paciencia = np.inf, None, 0
    for _ in range(120):
        rede.train()
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 128):
            b = perm[i:i + 128]
            perda = (((rede(xt[b]) - yt[b]) ** 2).mean(dim=1) * wt[b]).sum() / wt[b].sum().clamp(min=1e-6)
            otim.zero_grad(); perda.backward(); otim.step()
        rede.eval()
        with torch.no_grad():
            v = float((((rede(xv) - yv) ** 2).mean(dim=1) * wv).sum() / wv.sum().clamp(min=1e-6))
        if v < melhor - 1e-6:
            melhor, estado, paciencia = v, {k: t.clone() for k, t in rede.state_dict().items()}, 0
        else:
            paciencia += 1
            if paciencia >= 12:
                break
    rede.load_state_dict(estado)
    return rede.eval()


def treinar_gb(X, Y, W) -> dict[int, HistGradientBoostingRegressor]:
    feats = np.column_stack([X, X.sum(axis=1), X.std(axis=1)])
    modelos = {}
    for h in HORIZONTES:
        m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
        m.fit(feats, Y[:, :h].sum(axis=1), sample_weight=W if W.sum() > 0 else None)
        modelos[h] = m
    return modelos


class Conjunto:
    """Modelos treinados numa origem de reajuste (varias sementes no LSTM) e as constantes de escala."""
    def __init__(self, redes=None, gbs=None, sd_alvo=1.0):
        self.redes, self.gbs, self.sd_alvo = redes, gbs, sd_alvo

    def prever(self, g_alvo: pd.Series) -> dict[int, float]:
        """Variacao acumulada em log (nao em %) prevista para cada horizonte, a partir dos ultimos 12 meses."""
        z = (g_alvo.iloc[-JANELA:] / self.sd_alvo).to_numpy(dtype=np.float32)
        if self.redes:
            with torch.no_grad():
                yz = np.mean([r(torch.tensor(z).view(1, JANELA, 1)).numpy()[0] for r in self.redes], axis=0)
            cum = np.cumsum(yz)
            return {h: float(cum[h - 1] * self.sd_alvo / 100) for h in HORIZONTES}
        feats = np.concatenate([z, [z.sum(), z.std()]]).reshape(1, -1)
        return {h: float(self.gbs[h].predict(feats)[0] * self.sd_alvo / 100) for h in HORIZONTES}


def reajustar(g: pd.DataFrame, g_alvo: pd.Series, precos_log: pd.DataFrame, alvo_log: pd.Series, T: pd.Timestamp, cidades: list[str]) -> dict[str, Conjunto]:
    gT, galvoT = g.loc[:T], g_alvo.loc[:T]
    sd_alvo = float(galvoT.std())
    corr = semelhanca(precos_log, alvo_log, T)
    validas = [c for c in cidades if np.isfinite(corr.get(c, np.nan))]
    parecidas = list(corr[validas].sort_values(ascending=False).head(K_PARECIDAS).index)
    pesos = {c: max(float(corr[c]), 0.0) for c in validas}
    conjuntos: dict[str, Conjunto] = {}

    # controle: so a serie do alvo
    gc = pd.DataFrame({"alvo": galvoT})
    Xc, Yc, Wc, Dc = amostras(gc, ["alvo"])
    conjuntos[LSTM_CONTROLE] = Conjunto(redes=[treinar_lstm(Xc, Yc, Wc, Dc, s) for s in SEMENTES], sd_alvo=sd_alvo)

    gp = gT.copy()
    gp["alvo"] = galvoT  # o alvo participa dos paineis (so o passado)
    for nome, lista, p in ((LSTM_TODAS, cidades + ["alvo"], None), (LSTM_PARECIDAS, parecidas + ["alvo"], None), (LSTM_PONDERADO, cidades + ["alvo"], {**pesos, "alvo": 1.0})):
        X, Y, W, D = amostras(gp, lista, p)
        conjuntos[nome] = Conjunto(redes=[treinar_lstm(X, Y, W, D, s) for s in SEMENTES], sd_alvo=sd_alvo)
    for nome, lista in ((GB_TODAS, cidades + ["alvo"]), (GB_PARECIDAS, parecidas + ["alvo"])):
        X, Y, W, D = amostras(gp, lista)
        conjuntos[nome] = Conjunto(gbs=treinar_gb(X, Y, W), sd_alvo=sd_alvo)
    conjuntos["_parecidas"] = Conjunto()
    conjuntos["_parecidas"].lista = parecidas
    conjuntos["_parecidas"].corr = corr[parecidas]
    return conjuntos


# ----------------------------------------------------------------------------- walk-forward
def walk_forward(y: pd.Series, n0: int, precos: pd.DataFrame, nome_alvo: str) -> tuple[pd.DataFrame, list[tuple]]:
    n = len(y)
    precos = precos.reindex(y.index.union(precos.index)).sort_index()
    log_p = np.log(precos)
    g = log_p.diff() * 100
    g_alvo = y.diff() * 100
    cidades = [c for c in precos.columns if not (nome_alvo.startswith("SJC") and c.startswith("São José dos Campos"))]
    linhas, registros = [], []
    conj: dict[str, Conjunto] = {}
    for i in range(n0 - 1, n - 1):
        T = y.index[i]
        if (i - (n0 - 1)) % REAJUSTE_A_CADA == 0:
            t0 = time.time()
            conj = reajustar(g, g_alvo, log_p, y, T, cidades)
            registros.append((T, conj["_parecidas"].lista, conj["_parecidas"].corr.round(3).tolist()))
            print(f"[LSTM] {nome_alvo}: reajuste em {T:%Y-%m} ({time.time() - t0:.0f}s)", flush=True)
        passado = y.iloc[: i + 1]
        arima, _, _ = _arima_log(passado)
        c12 = passado.diff().iloc[-12:].mean()
        gprev = g_alvo.iloc[: i + 1]
        previsoes = {m: conj[m].prever(gprev) for m in MODELOS if m not in (REF, TEND)}
        for h in HORIZONTES:
            if i + h >= n:
                continue
            linha = {"origem": T, "h": h, "real": y.iloc[i + h], "ultimo": passado.iloc[-1], REF: arima[h - 1], TEND: passado.iloc[-1] + h * c12}
            linha.update({m: passado.iloc[-1] + v[h] for m, v in previsoes.items()})
            linhas.append(linha)
    return pd.DataFrame(linhas), registros


# ----------------------------------------------------------------------------- avaliacao
def metricas(wf: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for h, gh in wf.groupby("h"):
        real = np.exp(gh["real"])
        for m in MODELOS:
            erro = real - np.exp(gh[m])
            linhas.append({"h (meses)": h, "modelo": m, "n origens": len(gh), "MAPE (%)": float((erro.abs() / real).mean() * 100), "RMSE": float(np.sqrt((erro ** 2).mean()))})
    t = pd.DataFrame(linhas)
    base = t[t["modelo"] == REF].set_index("h (meses)")["RMSE"]
    t["RMSE relativo ao ARIMA"] = t["RMSE"] / t["h (meses)"].map(base)
    return t


def dm(wf: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Diebold-Mariano de `a` contra `b` (estatistica negativa: a e melhor)."""
    linhas = []
    for h in HORIZONTES:
        g = wf[wf["h"] == h].copy()
        g["arima"], g["contra"] = g[a], g[b]
        r = diebold_mariano(g, h, "contra")
        linhas.append({"modelo": a, "contra": b, "h (meses)": h, "estatistica DM": r["estatistica DM"], "p (bilateral)": r["p (bilateral)"]})
    return pd.DataFrame(linhas)


def figura(res: dict) -> str:
    fig, eixos = plt.subplots(1, len(res), figsize=(7.2 * len(res), 5))
    for eixo, (nome, r) in zip(np.atleast_1d(eixos), res.items()):
        piv = r["met"].pivot(index="h (meses)", columns="modelo", values="RMSE relativo ao ARIMA")[[m for m in MODELOS if m != REF]]
        piv.plot.bar(ax=eixo, rot=0, width=0.85)
        eixo.axhline(1, color="k", ls="--", lw=1)
        eixo.set_title(f"{nome}: RMSE relativo ao ARIMA(0,2,3)", fontsize=10)
        eixo.set_xlabel("horizonte (meses)")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend(fontsize=6)
    fig.tight_layout()
    return salvar_fig(fig, "lstm_comparacao.png")


def executar() -> dict:
    warnings.filterwarnings("ignore")
    inicio = time.time()
    wide, meta = carregar_wide()
    ref = montar_paineis(wide, meta).mensal_referencia
    precos = ler_cidades()
    os.makedirs(TAB_DIR, exist_ok=True)
    res = {}
    for nome, (col, n0) in ALVOS.items():
        y = np.log(ref[col].dropna())
        y.index = pd.DatetimeIndex(y.index, freq="MS")
        wf, regs = walk_forward(y, n0, precos, nome)
        slug = nome.split()[0]
        wf.to_csv(os.path.join(TAB_DIR, f"lstm_{slug}_previsoes.csv"), index=False)
        met = metricas(wf)
        dms = pd.concat([dm(wf, m, REF) for m in MODELOS if m != REF] + [dm(wf, m, LSTM_CONTROLE) for m in (LSTM_TODAS, LSTM_PARECIDAS, LSTM_PONDERADO)], ignore_index=True)
        met.to_csv(os.path.join(TAB_DIR, f"lstm_{slug}_metricas.csv"), index=False)
        dms.to_csv(os.path.join(TAB_DIR, f"lstm_{slug}_dm.csv"), index=False)
        res[nome] = {"met": met, "dm": dms, "regs": regs, "n_origens": wf["origem"].nunique()}
    fig = figura(res)
    escrever_relatorio(res, fig, time.time() - inicio, precos.shape[1])
    print(f"[LSTM] concluido em {(time.time() - inicio) / 60:.1f} min")
    return res


def escrever_relatorio(res: dict, fig: str, segundos: float, n_cidades: int) -> None:
    L = ["# LSTM e modelos globais em painel (FipeZAP)", "",
         "Gerado por `python main.py lstm`. Nao editar manualmente. Leitura em `docs/MODELOS_LSTM.md`.", "",
         f"Experimento: as {n_cidades} cidades do Excel do FipeZAP (preco medio de venda residencial). Modelos de **crescimento mensal** (em log), "
         f"padronizado pelo desvio-padrao de cada cidade **calculado so no treino**: o nivel do preco de cada cidade e eliminado. Entrada: ultimos {JANELA} "
         f"meses; saida direta de {H} meses. Alvos: SJC (proxy de Jacarei) e indice nacional.", "",
         f"- **Controle:** LSTM so com a serie do alvo.\n- **Painel (todas):** todas as cidades juntas.\n- **Mais parecidas:** so as {K_PARECIDAS} cidades "
         "com maior correlacao do crescimento de 12 meses com o alvo.\n- **Ponderado:** todas, com peso = correlacao (negativas valem 0).\n"
         "- **GB global:** gradient boosting em painel (comparador).",
         "A semelhanca usa **so dados ate a origem de cada reajuste** (sem olhar o futuro). Os modelos sao reajustados a cada "
         f"{REAJUSTE_A_CADA} meses (o ARIMA, todo mes) e os LSTM sao a media de {len(SEMENTES)} sementes. Walk-forward com janela expansiva, "
         "mesmos horizontes e metricas do ARIMA.", "", f"Tempo total: {segundos / 60:.1f} min.", ""]
    for nome, r in res.items():
        L += [f"## {nome} ({r['n_origens']} origens)", "", "### Erro por horizonte", "", md(r["met"].round(3), 3), "",
              "### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)", "", md(r["dm"].round(3), 3), "",
              "### Cidades escolhidas como mais parecidas em cada reajuste (cidade: correlacao)", ""]
        for T, lista, corrs in r["regs"]:
            L.append(f"- {T:%Y-%m}: " + ", ".join(f"{c} ({v})" for c, v in zip(lista[:6], corrs[:6])) + " ...")
        L.append("")
    L += ["## Figura", "", f"- `{fig}`", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
