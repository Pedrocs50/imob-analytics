from __future__ import annotations

import os
import time
import warnings
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA

from src.analysis.utils import md, salvar_fig
from src.timeseries.panel import carregar_wide, montar_paineis

REPORT = os.path.join("reports", "results", "arima.md")
TAB_DIR = os.path.join("reports", "results", "arima")
HORIZONTES = (1, 3, 6, 12)  # meses a frente da ULTIMA OBSERVACAO disponivel
MAX_P, MAX_Q = 3, 3
BENCHMARKS = ("ingenuo (ultimo valor)", "tendencia (crescimento medio de 12 meses)", "tendencia (ultimo crescimento)")


@dataclass(frozen=True)
class Alvo:
    nome: str
    coluna: str
    d: int  # ordem de diferenciacao (definida na analise exploratoria)
    tendencia: str  # "n" sem constante (d = 2), "c" com constante (d = 0)
    treino_inicial: int  # observacoes usadas para escolher a ordem e iniciar o walk-forward
    unidade: str


ALVOS = (
    Alvo("nacional (nominal)", "fipezap_nacional_res_venda_preco_m2", 2, "n", 84, "R$/m2"),
    Alvo("SJC (nominal)", "fipezap_sjc_res_venda_preco_m2", 2, "n", 60, "R$/m2"),
    Alvo("nacional (real)", "fipezap_nacional_res_venda_preco_m2_real", 0, "c", 84, "R$/m2 constantes de 2008"),
)


# ----------------------------------------------------------------------------- ajuste
def _ajustar(y: pd.Series, ordem: tuple[int, int, int], tendencia: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ARIMA(y, order=ordem, trend=tendencia).fit()


def selecionar_ordem(y: pd.Series, alvo: Alvo) -> pd.DataFrame:
    """Grade de (p, q) por AIC usando so a janela inicial de treino."""
    linhas = []
    for p in range(MAX_P + 1):
        for q in range(MAX_Q + 1):
            try:
                res = _ajustar(y, (p, alvo.d, q), alvo.tendencia)
                linhas.append({"ordem (p,d,q)": f"({p},{alvo.d},{q})", "p": p, "q": q, "AIC": res.aic, "BIC": res.bic})
            except Exception:
                continue
    return pd.DataFrame(linhas).sort_values("AIC").reset_index(drop=True)


# ----------------------------------------------------------------------------- walk-forward
def walk_forward(y: pd.Series, alvo: Alvo, ordem: tuple[int, int, int]) -> pd.DataFrame:
    """Em cada origem reajusta o modelo com os dados ate ela e preve ate 12 meses. Os
    benchmarks usam a mesma informacao. Retorna uma linha por (origem, horizonte)."""
    n = len(y)
    linhas = []
    for i in range(alvo.treino_inicial - 1, n - 1):
        passado = y.iloc[: i + 1]
        try:
            previsao = _ajustar(passado, ordem, alvo.tendencia).forecast(steps=max(HORIZONTES)).to_numpy()
        except Exception:
            continue
        ultimo, cresc_ult = passado.iloc[-1], passado.iloc[-1] - passado.iloc[-2]
        cresc_12 = passado.diff().iloc[-12:].mean()
        for h in HORIZONTES:
            if i + h >= n:
                continue
            real = y.iloc[i + h]
            linhas.append({
                "origem": y.index[i], "h": h, "real": real, "ultimo": ultimo,
                "arima": previsao[h - 1], BENCHMARKS[0]: ultimo,
                BENCHMARKS[1]: ultimo + h * cresc_12, BENCHMARKS[2]: ultimo + h * cresc_ult,
            })
    return pd.DataFrame(linhas)


def metricas(wf: pd.DataFrame) -> pd.DataFrame:
    """Metricas por horizonte na escala do preco (exp do log): RMSE, MAE, MAPE e R2 da
    variacao acumulada em log (previsto x observado em relacao a ultima observacao)."""
    modelos = ["arima", *BENCHMARKS]
    linhas = []
    for h, g in wf.groupby("h"):
        real = np.exp(g["real"])
        variacao_real = g["real"] - g["ultimo"]
        for m in modelos:
            prev = np.exp(g[m])
            erro = real - prev
            sst = ((variacao_real - variacao_real.mean()) ** 2).sum()
            linhas.append({
                "h (meses)": h, "modelo": m, "n origens": len(g), "RMSE": float(np.sqrt((erro ** 2).mean())),
                "MAE": float(erro.abs().mean()), "MAPE (%)": float((erro.abs() / real).mean() * 100),
                "R2 da variacao": float(1 - ((variacao_real - (g[m] - g["ultimo"])) ** 2).sum() / sst) if sst > 0 else np.nan,
            })
    tab = pd.DataFrame(linhas)
    ref = tab[tab["modelo"] == BENCHMARKS[0]].set_index("h (meses)")["RMSE"]
    tab["RMSE relativo ao ingenuo"] = tab["RMSE"] / tab["h (meses)"].map(ref)
    return tab


def diebold_mariano(wf: pd.DataFrame, h: int, contra: str) -> dict:
    """Teste de Diebold-Mariano (erro quadratico) com variancia de Newey-West de h-1 defasagens
    e correcao de Harvey. H0: mesma acuracia. Estatistica negativa = ARIMA melhor."""
    g = wf[wf["h"] == h]
    d = (g["real"] - g["arima"]) ** 2 - (g["real"] - g[contra]) ** 2
    n = len(d)
    media = d.mean()
    dc = d - media
    var = (dc ** 2).sum() / n
    for k in range(1, h):
        var += 2 * (1 - k / h) * (dc.iloc[k:].to_numpy() * dc.iloc[:-k].to_numpy()).sum() / n
    estat = media / np.sqrt(var / n) if var > 0 else np.nan
    estat *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)  # correcao de Harvey et al.
    return {"h (meses)": h, "contra": contra, "estatistica DM": float(estat), "p (bilateral)": float(2 * stats.t.sf(abs(estat), n - 1)), "n": n}


# ----------------------------------------------------------------------------- ajuste final e previsao
def ajuste_final(y: pd.Series, alvo: Alvo, ordem: tuple[int, int, int]) -> dict:
    res = _ajustar(y, ordem, alvo.tendencia)
    params = pd.DataFrame({"parametro": res.params.index, "coef": res.params.values, "erro-padrao": res.bse.values, "p": res.pvalues.values})
    lb = acorr_ljungbox(res.resid.iloc[max(ordem[0] + ordem[1], 1):], lags=[12], return_df=True)["lb_pvalue"].iloc[0]
    fc = res.get_forecast(steps=12)
    ic = fc.conf_int(alpha=0.05)
    previsao = pd.DataFrame({
        "mes de referencia": fc.predicted_mean.index, "previsao": np.exp(fc.predicted_mean.values),
        "limite inferior (95%)": np.exp(ic.iloc[:, 0].values), "limite superior (95%)": np.exp(ic.iloc[:, 1].values),
    })
    return {"params": params, "aic": res.aic, "bic": res.bic, "ljung_box_p12": float(lb), "previsao": previsao, "n": len(y)}


# ----------------------------------------------------------------------------- figuras
def figura_previsao(y_all: dict[str, pd.Series], finais: dict[str, dict]) -> str:
    fig, eixos = plt.subplots(1, len(finais), figsize=(5.4 * len(finais), 4.2))
    for eixo, (nome, f) in zip(np.atleast_1d(eixos), finais.items()):
        hist = np.exp(y_all[nome]).iloc[-48:]
        p = f["previsao"]
        eixo.plot(hist.index, hist.values, color="#1f5f99", label="observado")
        eixo.plot(p["mes de referencia"], p["previsao"], color="#d9822b", label="previsao")
        eixo.fill_between(p["mes de referencia"], p["limite inferior (95%)"], p["limite superior (95%)"], color="#d9822b", alpha=0.2, label="IC 95%")
        eixo.set_title(f"{nome}: ARIMA, 12 meses a frente", fontsize=10)
        eixo.grid(alpha=0.3)
        eixo.legend(fontsize=8)
        eixo.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return salvar_fig(fig, "arima_previsao.png")


def figura_erros(tabelas: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, len(tabelas), figsize=(5.4 * len(tabelas), 4.2), sharey=True)
    for eixo, (nome, t) in zip(np.atleast_1d(eixos), tabelas.items()):
        piv = t.pivot(index="h (meses)", columns="modelo", values="RMSE relativo ao ingenuo")[["arima", *BENCHMARKS[1:]]]
        piv.plot.bar(ax=eixo, rot=0, color=["#1f5f99", "#7a7a7a", "#bdbdbd"], width=0.8)
        eixo.axhline(1, color="k", lw=1, ls="--")
        eixo.set_title(f"{nome}: RMSE relativo ao ingenuo", fontsize=10)
        eixo.set_xlabel("horizonte (meses)")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend(fontsize=7)
    np.atleast_1d(eixos)[0].set_ylabel("RMSE / RMSE do ingenuo (menor e melhor)")
    fig.tight_layout()
    return salvar_fig(fig, "arima_erros_por_horizonte.png")


# ----------------------------------------------------------------------------- orquestracao
def executar() -> dict:
    inicio = time.time()
    wide, meta = carregar_wide()
    ref = montar_paineis(wide, meta).mensal_referencia
    os.makedirs(TAB_DIR, exist_ok=True)

    resultados: dict[str, dict] = {}
    for alvo in ALVOS:
        y = np.log(ref[alvo.coluna].dropna())
        y.index = pd.DatetimeIndex(y.index, freq="MS")
        grade = selecionar_ordem(y.iloc[: alvo.treino_inicial], alvo)
        melhor = grade.iloc[0]
        ordem = (int(melhor["p"]), alvo.d, int(melhor["q"]))
        t0 = time.time()
        wf = walk_forward(y, alvo, ordem)
        met = metricas(wf)
        dm = pd.DataFrame([diebold_mariano(wf, h, b) for h in HORIZONTES for b in BENCHMARKS])
        final = ajuste_final(y, alvo, ordem)
        resultados[alvo.nome] = {"alvo": alvo, "y": y, "grade": grade, "ordem": ordem, "wf": wf, "met": met, "dm": dm, "final": final}
        slug = alvo.nome.replace(" ", "_").replace("(", "").replace(")", "")
        for nome, df in {"grade": grade, "metricas": met, "diebold_mariano": dm, "previsao": final["previsao"], "parametros": final["params"]}.items():
            df.to_csv(os.path.join(TAB_DIR, f"arima_{slug}_{nome}.csv"), index=False, encoding="utf-8")
        print(f"[ARIMA] {alvo.nome}: ordem {ordem}, {wf['origem'].nunique()} origens, walk-forward em {time.time() - t0:.0f}s")

    figuras = [figura_previsao({k: v["y"] for k, v in resultados.items()}, {k: v["final"] for k, v in resultados.items()}),
               figura_erros({k: v["met"] for k, v in resultados.items()})]
    escrever_relatorio(resultados, figuras, time.time() - inicio)
    print(f"[ARIMA] concluido em {time.time() - inicio:.0f}s")
    return resultados


def escrever_relatorio(res: dict[str, dict], figuras: list[str], segundos: float) -> None:
    L = ["# ARIMA do FipeZAP (meta 4)", "",
         "Gerado por `python main.py arima`. Nao editar manualmente. Leitura em `docs/MODELOS_TEMPORAIS.md`.", "",
         "Alvo em **log** do preco medio de venda do FipeZAP (painel de referencia, 224 meses no nacional, 104 em SJC). "
         "Ordem de diferenciacao da analise exploratoria: `d = 2` nos nominais (sem constante) e `d = 0` com constante no preco "
         "real. A ordem `(p, q)` e escolhida por AIC (p e q de 0 a 3) **so na janela inicial de treino**.", "",
         "Avaliacao por **walk-forward** com janela expansiva: em cada mes de origem o modelo e reajustado com os dados ate ela "
         "(a ordem fica fixa) e preve 1, 3, 6 e 12 meses a frente da ultima observacao disponivel. Como o FipeZAP do mes `t` "
         "so e publicado em `t+1`, na pratica o primeiro mes que se consegue prever a partir do fim do mes `t` e `t+2`. "
         "Metricas na escala do preco (RMSE e MAE em R$/m2, MAPE em %), e R2 da variacao acumulada em log.", "",
         "Benchmarks: " + "; ".join(BENCHMARKS) + ". Um ARIMA so se justifica se superar a tendencia simples.", "",
         f"Tempo total de execucao: {segundos:.0f} s.", ""]
    for nome, r in res.items():
        a, f, ordem = r["alvo"], r["final"], r["ordem"]
        L += [f"## {nome} ({a.unidade})", "", f"Treino inicial: {a.treino_inicial} meses; ordem escolhida: **ARIMA{ordem}**"
              f"{' com constante' if a.tendencia == 'c' else ''}; {r['wf']['origem'].nunique()} origens no walk-forward.", "",
              "### Selecao de ordem (5 menores AIC, janela inicial)", "", md(r["grade"].head(5).round(2)), "",
              "### Desempenho fora da amostra", "", md(r["met"].round(3)), "",
              "### Teste de Diebold-Mariano (estatistica negativa: ARIMA melhor)", "", md(r["dm"].round(3)), "",
              f"### Ajuste na amostra toda (n = {f['n']})", "", f"AIC {f['aic']:.1f}; BIC {f['bic']:.1f}; Ljung-Box (12 lags) nos residuos: p = {f['ljung_box_p12']:.3f}.", "",
              md(f["params"].round(4), 4), "", "### Previsao para os proximos 12 meses (R$/m2; IC de 95%)", "", md(f["previsao"].round({"previsao": 1, "limite inferior (95%)": 1, "limite superior (95%)": 1}), 1), ""]
    L += ["## Figuras", ""] + [f"- `{x}`" for x in figuras]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
