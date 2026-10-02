from __future__ import annotations

import contextlib
import io
import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, grangercausalitytests, kpss

from src.analysis.utils import md as _md, salvar_fig as _salvar_fig, salvar_tab as _salvar_tab
from src.timeseries.catalogo import SERIES_POR_ID
from src.timeseries.panel import Paineis, carregar_wide, montar_paineis

REPORT = os.path.join("reports", "results", "eda_series.md")

ALVOS = {
    "nacional (nominal)": "fipezap_nacional_res_venda_preco_m2",
    "nacional (real)": "fipezap_nacional_res_venda_preco_m2_real",
    "SJC (nominal)": "fipezap_sjc_res_venda_preco_m2",
    "SJC (real)": "fipezap_sjc_res_venda_preco_m2_real",
}
ALVOS_MODELO = ("nacional (nominal)", "SJC (nominal)")  # alvos da comparacao ARIMA x LSTM

# preditor -> (rotulo, transformacao inicial). Se, depois dela, ADF/KPSS ainda apontarem raiz
# unitaria, aplica-se mais uma diferenca (ver `estacionarizar`); o resultado fica na tabela 9.
PREDITORES = {
    "bcb_selic_meta": ("Selic meta", "diff"),
    "selic_real_mes": ("Selic real no mes", "nivel"),
    "bcb_ipca": ("IPCA mensal", "nivel"),
    "bcb_igpm": ("IGP-M mensal", "nivel"),
    "bcb_incc": ("INCC mensal", "nivel"),
    "bcb_ptax": ("Dolar PTAX", "dlog"),
    "bcb_ibcbr": ("IBC-Br", "dlog"),
    "bcb_credimob_saldo": ("Saldo cred. imob.", "dlog"),
    "bcb_credimob_juros_mercado": ("Juros financ. imob. (mercado)", "diff"),
    "bcb_credimob_juros_regulada": ("Juros financ. imob. (regulada)", "diff"),
    "ipea_icc": ("Confianca do consumidor", "diff"),
    "ipea_desocupacao_br_mensal": ("Desocupacao Brasil", "diff"),
}
NOME_TRANSFORMACAO = {"nivel": "nivel", "diff": "1a diferenca", "dlog": "var. % (dlog)"}
MAX_LAG_CCF = 12
MAX_LAG_GRANGER = 6
COR_ALVO, COR_REAL, COR_SJC, COR_MACRO = "#1f5f99", "#d9822b", "#2a9d8f", "#7a7a7a"


# ----------------------------------------------------------------------------- utilidades
def _dlog(s: pd.Series) -> pd.Series:
    return 100 * np.log(s).diff()


def _transformar(s: pd.Series, como: str) -> pd.Series:
    if como == "nivel":
        return s
    if como == "diff":
        return s.diff()
    return _dlog(s)


# ----------------------------------------------------------------------------- testes
def _adf(x: pd.Series, regressao: str = "c") -> float:
    x = x.dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(adfuller(x, regression=regressao, autolag="AIC", result_object=True).pvalue)


def _kpss(x: pd.Series, regressao: str = "c") -> float:
    x = x.dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(kpss(x, regression=regressao, nlags="auto", result_object=True).pvalue)


def estacionariedade(ref: pd.DataFrame) -> pd.DataFrame:
    """ADF (H0: raiz unitaria) e KPSS (H0: estacionaria) em cada transformacao. Uma serie
    e tratada como estacionaria quando o ADF rejeita (p<0,05) E o KPSS nao rejeita (p>0,05)."""
    linhas = []
    for nome, col in ALVOS.items():
        x = ref[col].dropna()
        versoes = {
            "log (nivel)": np.log(x),
            "d1: var. mensal (dlog)": _dlog(x),
            "d2: dif. da var. mensal": _dlog(x).diff(),
        }
        for etapa, s in versoes.items():
            adf_p, kpss_p = _adf(s), _kpss(s)
            linhas.append({
                "serie": nome, "transformacao": etapa, "n": int(s.notna().sum()),
                "ADF p": adf_p, "KPSS p": kpss_p,
                "estacionaria": "sim" if adf_p < 0.05 and kpss_p > 0.05 else
                                ("conflito" if (adf_p < 0.05) != (kpss_p > 0.05) else "nao"),
            })
    return pd.DataFrame(linhas)


def ordem_de_diferenciacao(tab: pd.DataFrame) -> dict[str, str]:
    saida = {}
    for nome, grupo in tab.groupby("serie", sort=False):
        ok = grupo[grupo["estacionaria"] == "sim"]
        saida[nome] = ok.iloc[0]["transformacao"] if len(ok) else "nenhuma (conflito entre os testes)"
    return saida


def estacionarizar(s: pd.Series, max_extra: int = 2) -> tuple[pd.Series, int, bool]:
    """Diferencia ate ADF rejeitar (p<0,05) e KPSS nao rejeitar (p>0,05). Retorna
    (serie, diferencas extras aplicadas, passou nos dois testes)."""
    atual = s
    for k in range(max_extra + 1):
        if _adf(atual) < 0.05 and _kpss(atual) > 0.05:
            return atual, k, True
        if k < max_extra:
            atual = atual.diff()
    return atual, max_extra, False


# ----------------------------------------------------------------------------- descricao
def descritiva(ref: pd.DataFrame, lags: dict[str, int]) -> pd.DataFrame:
    linhas = []
    def rotulo_nivel(col: str) -> str:
        if col in SERIES_POR_ID:
            d = SERIES_POR_ID[col]
            return f"{d.nome} ({d.unidade})"
        return "Selic real no mes (%)" if col == "selic_real_mes" else col

    itens = {**{k: v for k, v in ALVOS.items()}, **{rotulo_nivel(k): k for k in PREDITORES}}
    for rotulo, col in itens.items():
        s = ref[col].dropna()
        linhas.append({
            "serie": rotulo, "coluna": col, "n": len(s), "inicio": f"{s.index.min():%Y-%m}", "fim": f"{s.index.max():%Y-%m}",
            "media": s.mean(), "desvio": s.std(), "min": s.min(), "max": s.max(),
            "defasagem L": lags.get(col, ""),
        })
    return pd.DataFrame(linhas)


def crescimento_anual(ref: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "FipeZAP nacional (nominal)": _dlog(ref[ALVOS["nacional (nominal)"]]),
        "FipeZAP nacional (real)": _dlog(ref[ALVOS["nacional (real)"]]),
        "FipeZAP SJC (nominal)": _dlog(ref[ALVOS["SJC (nominal)"]]),
        "IPCA": ref["bcb_ipca"],
    })
    anual = df.groupby(df.index.year).mean()
    anual["Selic meta (media, % a.a.)"] = ref["bcb_selic_meta"].groupby(ref.index.year).mean()
    anual.index.name = "ano"
    return anual.reset_index().round(3)


def dormitorios(ref: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = {d: f"fipezap_nacional_res_venda_preco_m2{'' if d == 'total' else '_' + d}" for d in ("total", "1d", "2d", "3d", "4d")}
    niveis = pd.DataFrame({d: ref[c] for d, c in cols.items()})
    cresc = niveis.apply(_dlog)
    resumo = pd.DataFrame({
        "faixa": list(cols), "preco final / inicial": (niveis.iloc[-1] / niveis.iloc[0]).values,
        "crescimento mensal medio (%)": cresc.mean().values, "desvio (%)": cresc.std().values,
        "corr. com o total": cresc.corr()["total"].values,
    })
    return resumo, cresc.corr()


def outliers_de_crescimento(ref: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for nome in ALVOS_MODELO:
        g = _dlog(ref[ALVOS[nome]]).dropna()
        mad = (g - g.median()).abs().median() * 1.4826
        z = (g - g.median()) / mad
        for data, valor in g[z.abs() > 3.5].items():
            linhas.append({"serie": nome, "mes": f"{data:%Y-%m}", "var. mensal (%)": valor, "z robusto": z[data]})
    return pd.DataFrame(linhas, columns=["serie", "mes", "var. mensal (%)", "z robusto"])


# ----------------------------------------------------------------------------- alvo estacionario
def alvo_estacionario(ref: pd.DataFrame, nome: str) -> tuple[pd.Series, str, bool]:
    g = _dlog(ref[ALVOS[nome]]).dropna()
    y, extra, ok = estacionarizar(g)
    desc = {0: "var. mensal (dlog)", 1: "dif. da var. mensal (d2)"}.get(extra, f"dlog + {extra} dif.")
    return y.reindex(ref.index), desc, ok


# ----------------------------------------------------------------------------- autocorrelacao e sazonalidade
def autocorrelacao(ref: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """ACF da variacao mensal (evidencia de persistencia) e ACF/PACF da serie estacionaria
    (base para escolher p e q do ARIMA)."""
    linhas = []
    fig, eixos = plt.subplots(2, 3, figsize=(15, 6.5))
    for i, nome in enumerate(ALVOS_MODELO):
        g = _dlog(ref[ALVOS[nome]]).dropna()
        y, desc, _ = alvo_estacionario(ref, nome)
        y = y.dropna()
        lb_g = acorr_ljungbox(g, lags=[12], return_df=True)["lb_pvalue"].iloc[0]
        lb_y = acorr_ljungbox(y, lags=[12], return_df=True)["lb_pvalue"].iloc[0]
        linhas.append({"serie": nome, "transformacao estacionaria": desc, "autocorr. lag 1 (var. mensal)": g.autocorr(1),
                       "autocorr. lag 1 (estacionaria)": y.autocorr(1), "autocorr. lag 2 (estacionaria)": y.autocorr(2),
                       "autocorr. lag 3 (estacionaria)": y.autocorr(3), "Ljung-Box p12 (var. mensal)": lb_g,
                       "Ljung-Box p12 (estacionaria)": lb_y})
        lags = min(24, len(y) // 2 - 1)
        plot_acf(g, lags=lags, ax=eixos[i, 0], title=f"{nome}: ACF da var. mensal", zero=False)
        plot_acf(y, lags=lags, ax=eixos[i, 1], title=f"{nome}: ACF ({desc})", zero=False)
        plot_pacf(y, lags=lags, ax=eixos[i, 2], title=f"{nome}: PACF ({desc})", zero=False, method="ywm")
    fig.tight_layout()
    return pd.DataFrame(linhas), _salvar_fig(fig, "eda_acf_pacf_alvo.png")


def sazonalidade(ref: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    linhas, series = [], {}
    for nome in ALVOS_MODELO:
        g = _dlog(ref[ALVOS[nome]]).dropna()
        stl = STL(g, period=12, robust=True).fit()
        forca = max(0.0, 1 - stl.resid.var() / (stl.resid + stl.seasonal).var())
        grupos = [v.values for _, v in g.groupby(g.index.month)]
        kw = float(stats.kruskal(*grupos).pvalue)
        linhas.append({"serie": nome, "n": len(g), "forca sazonal (STL, 0-1)": forca, "Kruskal-Wallis p (mes do ano)": kw})
        series[nome] = (g, forca, kw)
    tab = pd.DataFrame(linhas)

    # so faz grafico se houver indicio de sazonalidade (forca >= 0,3 ou p < 0,05)
    if not any(f >= 0.3 or p < 0.05 for _, f, p in series.values()):
        return tab, None
    fig, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for eixo, (nome, (g, forca, kw)) in zip(eixos, series.items()):
        por_mes = g.groupby(g.index.month).agg(["mean", "sem"])
        eixo.bar(por_mes.index, por_mes["mean"], yerr=1.96 * por_mes["sem"], color=COR_ALVO, alpha=0.8)
        eixo.axhline(g.mean(), color="k", lw=0.8, ls="--")
        eixo.set_title(f"{nome}: forca sazonal {forca:.2f}, Kruskal p={kw:.3f}")
        eixo.set_xlabel("mes do ano"); eixo.set_xticks(range(1, 13))
    eixos[0].set_ylabel("var. mensal media (%)")
    fig.tight_layout()
    return tab, _salvar_fig(fig, "eda_sazonalidade.png")


# ----------------------------------------------------------------------------- SJC x nacional
def sjc_vs_nacional(ref: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    idx_n, idx_s = ref["fipezap_nacional_res_venda_indice"], ref["fipezap_sjc_res_venda_indice"]
    comum = pd.concat([idx_n, idx_s], axis=1).dropna()
    gn, gs = _dlog(comum.iloc[:, 0]).dropna(), _dlog(comum.iloc[:, 1]).dropna()
    en, _, _ = estacionarizar(gn)
    es, _, _ = estacionarizar(gs)

    linhas = []
    for k in range(-6, 7):
        par_e = pd.concat([es, en.shift(k)], axis=1).dropna()
        linhas.append({"lag (SJC em t x nacional em t-k)": k, "corr. var. mensal (nao estacionaria)": gs.corr(gn.shift(k)),
                       "corr. estacionaria (d2)": es.corr(en.shift(k)), "n (estacionaria)": len(par_e)})
    tab = pd.DataFrame(linhas)

    fig, eixos = plt.subplots(1, 2, figsize=(12, 4))
    base = comum / comum.iloc[0] * 100
    eixos[0].plot(base.index, base.iloc[:, 0], color=COR_ALVO, label="nacional")
    eixos[0].plot(base.index, base.iloc[:, 1], color=COR_SJC, label="Sao Jose dos Campos")
    eixos[0].set_title("Numero-indice de venda (base 100 = 2018-01)"); eixos[0].legend(); eixos[0].grid(alpha=0.3)
    eixos[1].plot(ref[ALVOS["nacional (nominal)"]].dropna(), color=COR_ALVO, label="nominal")
    eixos[1].plot(ref[ALVOS["nacional (real)"]].dropna(), color=COR_REAL, label="real (reais constantes de 2008)")
    eixos[1].set_title("Preco medio de venda, R$/m2 (nacional)"); eixos[1].legend(); eixos[1].grid(alpha=0.3)
    fig.tight_layout()
    return tab, _salvar_fig(fig, "eda_alvo_niveis.png")


# ----------------------------------------------------------------------------- crescimento x juros
def crescimento_e_selic(ref: pd.DataFrame) -> str:
    fig, eixo = plt.subplots(figsize=(11, 4))
    g_nom = _dlog(ref[ALVOS["nacional (nominal)"]]).rolling(12).mean()
    g_real = _dlog(ref[ALVOS["nacional (real)"]]).rolling(12).mean()
    eixo.plot(g_nom, color=COR_ALVO, label="FipeZAP nacional, nominal")
    eixo.plot(g_real, color=COR_REAL, label="FipeZAP nacional, real")
    eixo.axhline(0, color="k", lw=0.6)
    eixo.set_ylabel("var. mensal, media movel de 12 meses (%)"); eixo.grid(alpha=0.3)
    ax2 = eixo.twinx()
    ax2.plot(ref["bcb_selic_meta"], color=COR_MACRO, ls="--", label="Selic meta (eixo direito)")
    ax2.set_ylabel("Selic meta (% a.a.)")
    h1, l1 = eixo.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    eixo.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    eixo.set_title("Crescimento do preco e ciclo de juros")
    return _salvar_fig(fig, "eda_crescimento_selic.png")


# ----------------------------------------------------------------------------- preditores
def preditores_transformados(ref: pd.DataFrame) -> pd.DataFrame:
    """Transformacao inicial (sem diferenca extra)."""
    return pd.DataFrame({k: _transformar(ref[k], como) for k, (_, como) in PREDITORES.items()})


def preditores_estacionarios(ref: pd.DataFrame, lags: dict[str, int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    bruto = preditores_transformados(ref)
    saida, linhas = {}, []
    for col, (rotulo, como) in PREDITORES.items():
        s0 = bruto[col].dropna()
        x, extra, ok = estacionarizar(s0)
        saida[col] = x.reindex(ref.index)
        x = x.dropna()
        linhas.append({"preditor": rotulo, "coluna": col, "transformacao inicial": NOME_TRANSFORMACAO[como],
                       "diferencas extras": extra, "estacionaria": "sim" if ok else "nao", "n": len(x),
                       "inicio": f"{x.index.min():%Y-%m}", "defasagem L": lags[col],
                       "ADF p (antes)": _adf(s0), "KPSS p (antes)": _kpss(s0),
                       "ADF p (final)": _adf(x), "KPSS p (final)": _kpss(x)})
    return pd.DataFrame(saida, index=ref.index), pd.DataFrame(linhas)


def correlacao_preditores(x: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    rot = {k: v[0] for k, v in PREDITORES.items()}
    corr = x.rename(columns=rot).corr(method="spearman", min_periods=60)
    pares = [(a, b, corr.loc[a, b]) for i, a in enumerate(corr.columns) for b in corr.columns[i + 1:] if abs(corr.loc[a, b]) >= 0.5]
    altos = pd.DataFrame(sorted(pares, key=lambda t: -abs(t[2])), columns=["variavel A", "variavel B", "correlacao (Spearman)"])
    fig, eixo = plt.subplots(figsize=(9, 7.2))
    sns.heatmap(corr, cmap="RdBu_r", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", annot_kws={"size": 7},
                cbar_kws={"shrink": 0.7}, ax=eixo)
    eixo.set_title("Correlacao entre os preditores (ja estacionarios, Spearman)")
    fig.tight_layout()
    return corr, altos, _salvar_fig(fig, "eda_correlacao_preditores.png")


def correlacao_cruzada(y: pd.Series, x: pd.DataFrame, lags: dict[str, int]) -> pd.DataFrame:
    """corr(y_t, x_{t-l}) para l = 0..12, em data de referencia. `utilizavel` = l >= L + 1:
    para prever o mes t no fim do mes t-1, o preditor precisa ja ter sido publicado."""
    linhas = []
    for col, (rotulo, _) in PREDITORES.items():
        for k in range(0, MAX_LAG_CCF + 1):
            par = pd.concat([y, x[col].shift(k)], axis=1).dropna()
            n = len(par)
            r = par.iloc[:, 0].corr(par.iloc[:, 1]) if n >= 36 else np.nan
            # limiar conservador: o FipeZAP e media movel trimestral, entao usa-se n/3
            limiar = 1.96 / np.sqrt(max(n / 3, 1)) if n >= 36 else np.nan
            linhas.append({"preditor": rotulo, "coluna": col, "lag": k, "r": r, "n": n, "limiar": limiar,
                           "significativa": bool(abs(r) > limiar) if n >= 36 else False,
                           "utilizavel (lag >= L+1)": k >= lags[col] + 1})
    return pd.DataFrame(linhas)


def comparativo_espurio(bruta: pd.DataFrame, est: pd.DataFrame) -> pd.DataFrame:
    """Maior |r| (lags utilizaveis) com as series como vinham (nao estacionarias) e depois de
    estacionarizadas: mostra o quanto da correlacao era tendencia comum."""
    linhas = []
    for col, (rotulo, _) in PREDITORES.items():
        b = bruta[(bruta["coluna"] == col) & bruta["utilizavel (lag >= L+1)"]].dropna(subset=["r"])
        e = est[(est["coluna"] == col) & est["utilizavel (lag >= L+1)"]].dropna(subset=["r"])
        if b.empty or e.empty:
            continue
        ib, ie = b["r"].abs().idxmax(), e["r"].abs().idxmax()
        linhas.append({"preditor": rotulo, "maior |r| bruta": abs(b.loc[ib, "r"]), "lag (bruta)": int(b.loc[ib, "lag"]),
                       "maior |r| estacionaria": abs(e.loc[ie, "r"]), "lag (estacionaria)": int(e.loc[ie, "lag"])})
    return pd.DataFrame(linhas).sort_values("maior |r| bruta", ascending=False)


def heatmap_ccf(ccf: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, len(ccf), figsize=(6.2 * len(ccf), 5.2), sharey=True)
    eixos = np.atleast_1d(eixos)
    for eixo, (nome, tab) in zip(eixos, ccf.items()):
        m = tab.pivot(index="preditor", columns="lag", values="r").reindex([v[0] for v in PREDITORES.values()])
        sig = tab.pivot(index="preditor", columns="lag", values="significativa").reindex(m.index)
        anot = m.round(2).astype(object).where(sig, "")
        sns.heatmap(m, cmap="RdBu_r", center=0, vmin=-0.5, vmax=0.5, annot=anot, fmt="", annot_kws={"size": 7},
                    cbar=eixo is eixos[-1], ax=eixo)
        eixo.set_title(f"FipeZAP {nome} (estacionario)\nvalores exibidos: acima do limiar conservador")
        eixo.set_xlabel("defasagem do preditor (meses de referencia)"); eixo.set_ylabel("")
    fig.tight_layout()
    return _salvar_fig(fig, "eda_correlacao_cruzada.png")


def granger(y: pd.Series, x: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for col, (rotulo, _) in PREDITORES.items():
        d = pd.concat([y, x[col]], axis=1).dropna()
        if len(d) < 60:
            continue
        with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
            warnings.simplefilter("ignore")
            res = grangercausalitytests(d.values, maxlag=MAX_LAG_GRANGER)
        p = {k: float(res[k][0]["ssr_ftest"][1]) for k in range(1, MAX_LAG_GRANGER + 1)}
        melhor = min(p, key=p.get)
        linhas.append({"preditor": rotulo, "coluna": col, "n": len(d), "menor p": p[melhor], "no lag": melhor,
                       **{f"p lag {k}": v for k, v in p.items()}})
    tab = pd.DataFrame(linhas)
    limiar = 0.05 / (len(PREDITORES) * MAX_LAG_GRANGER)  # Bonferroni sobre todos os testes
    tab["p < 0,05"] = tab["menor p"] < 0.05
    tab["passa Bonferroni"] = tab["menor p"] < limiar
    tab.attrs["limiar_bonferroni"] = limiar
    return tab


def ccf_trimestral(p: Paineis) -> pd.DataFrame:
    tri = p.trimestral_referencia
    y_raw = _dlog(tri[ALVOS["nacional (nominal)"]]).dropna()
    y, extra_y, _ = estacionarizar(y_raw)
    itens = {
        "ibge_desocupacao_sp": ("Desocupacao SP", "diff"), "ibge_renda_sp": ("Renda SP", "dlog"),
        "bcb_selic_meta": ("Selic meta", "diff"), "bcb_ipca": ("IPCA (composto no trimestre)", "nivel"),
        "bcb_ibcbr": ("IBC-Br", "dlog"),
    }
    linhas = []
    for col, (rotulo, como) in itens.items():
        x, extra, ok = estacionarizar(_transformar(tri[col], como).dropna())
        for k in range(0, 5):
            par = pd.concat([y, x.shift(k)], axis=1).dropna()
            r = par.iloc[:, 0].corr(par.iloc[:, 1]) if len(par) >= 20 else np.nan
            linhas.append({"preditor": rotulo, "dif. extras": extra, "lag (trimestres)": k, "r": r, "n": len(par),
                           "limiar 95%": 1.96 / np.sqrt(len(par)) if len(par) else np.nan})
    tab = pd.DataFrame(linhas)
    tab.attrs["alvo_diferencas_extras"] = extra_y
    return tab


def baixa_frequencia(ref: pd.DataFrame, lags: dict[str, int]) -> pd.DataFrame:
    """Canal de baixa frequencia: variacao de 12 meses do preco contra niveis/variacoes de 12
    meses dos macros. A dupla diferenciacao usada acima apaga relacoes desse tipo (ex.: ciclo
    de juros). Janelas de 12 meses se sobrepoem, entao o limiar usa n/12 observacoes efetivas.
    Analise descritiva: nao prova causalidade."""
    def var12(s: pd.Series) -> pd.Series:
        return 100 * (np.log(s) - np.log(s.shift(12)))

    x = {
        "Selic meta (nivel)": (ref["bcb_selic_meta"], "bcb_selic_meta"),
        "Selic real, media de 12 meses": (ref["selic_real_mes"].rolling(12).mean(), "selic_real_mes"),
        "Saldo cred. imob. (var. 12 meses)": (var12(ref["bcb_credimob_saldo"]), "bcb_credimob_saldo"),
        "IBC-Br (var. 12 meses)": (var12(ref["bcb_ibcbr"]), "bcb_ibcbr"),
        "Dolar PTAX (var. 12 meses)": (var12(ref["bcb_ptax"]), "bcb_ptax"),
        "IPCA acumulado 12 meses": (ref["ipca_acum_12m"], "bcb_ipca"),
        "INCC acumulado 12 meses": (ref["bcb_incc_acum_12m"], "bcb_incc"),
        "Confianca do consumidor (nivel)": (ref["ipea_icc"], "ipea_icc"),
        "Desocupacao Brasil (nivel)": (ref["ipea_desocupacao_br_mensal"], "ipea_desocupacao_br_mensal"),
        "Juros financ. imob. mercado (nivel)": (ref["bcb_credimob_juros_mercado"], "bcb_credimob_juros_mercado"),
    }
    linhas = []
    for alvo in ("nacional (nominal)", "nacional (real)", "SJC (nominal)"):
        y = var12(ref[ALVOS[alvo]])
        for rotulo, (serie, base) in x.items():
            for k in (0, 3, 6, 9, 12):
                par = pd.concat([y, serie.shift(k)], axis=1).dropna()
                n = len(par)
                if n < 36:
                    continue
                r = par.iloc[:, 0].corr(par.iloc[:, 1])
                linhas.append({"alvo (var. 12 meses)": alvo, "preditor": rotulo, "lag": k, "r": r, "n": n,
                               "limiar (n/12)": 1.96 / np.sqrt(n / 12), "utilizavel (lag >= L+1)": k >= lags[base] + 1})
    tab = pd.DataFrame(linhas)
    tab["significativa"] = tab["r"].abs() > tab["limiar (n/12)"]
    return tab


def estabilidade_subperiodos(ref: pd.DataFrame) -> pd.DataFrame:
    """As correlacoes de baixa frequencia se mantem em subperiodos? Uma relacao estavel
    deveria sobreviver; se aparece so num ciclo, e tendencia comum e nao previsao."""
    def var12(s: pd.Series) -> pd.Series:
        return 100 * (np.log(s) - np.log(s.shift(12)))

    y = var12(ref[ALVOS["nacional (nominal)"]])
    x = {
        "Saldo cred. imob. (var. 12 meses, lag 3)": var12(ref["bcb_credimob_saldo"]).shift(3),
        "Confianca do consumidor (nivel, lag 3)": ref["ipea_icc"].shift(3),
        "Selic real, media de 12 meses (lag 6)": ref["selic_real_mes"].rolling(12).mean().shift(6),
        "INCC acumulado 12 meses (lag 6)": ref["bcb_incc_acum_12m"].shift(6),
    }
    periodos = {"2009-2014": ("2009-01", "2014-12"), "2015-2020": ("2015-01", "2020-12"),
                "2021-2026": ("2021-01", "2026-08"), "amostra toda": ("2009-01", "2026-08")}
    linhas = []
    for nome, serie in x.items():
        d = pd.concat([y, serie], axis=1).dropna()
        linha = {"preditor (contra a var. 12 meses do FipeZAP nacional)": nome}
        for rot, (a, b) in periodos.items():
            trecho = d.loc[a:b]
            linha[rot] = trecho.iloc[:, 0].corr(trecho.iloc[:, 1])
        linhas.append(linha)
    tab = pd.DataFrame(linhas)
    tab.attrs["autocorr_12"] = {"preco": y.autocorr(12), "credito": var12(ref["bcb_credimob_saldo"]).autocorr(12)}
    return tab


def suficiencia(ref: pd.DataFrame, x_est: pd.DataFrame, x_raw: pd.DataFrame, p: Paineis) -> pd.DataFrame:
    def n_completo(nome: str, colunas: list[str]) -> int:
        y, _, _ = alvo_estacionario(ref, nome)
        return len(pd.concat([y, x_est[colunas]], axis=1).dropna())

    historico_longo = [c for c in PREDITORES if x_raw[c].first_valid_index() <= pd.Timestamp("2008-03-01")]
    linhas = []
    for nome in ALVOS_MODELO:
        y, _, _ = alvo_estacionario(ref, nome)
        linhas.append({"cenario": f"ARIMA univariado, {nome}", "observacoes": int(y.notna().sum()), "variaveis": 1})
        linhas.append({"cenario": f"ARIMAX/LSTM, {nome}, {len(historico_longo)} preditores com historico desde 2008",
                       "observacoes": n_completo(nome, historico_longo), "variaveis": len(historico_longo)})
        linhas.append({"cenario": f"ARIMAX/LSTM, {nome}, todos os {len(PREDITORES)} preditores",
                       "observacoes": n_completo(nome, list(PREDITORES)), "variaveis": len(PREDITORES)})
        tri, _, _ = estacionarizar(_dlog(p.trimestral_referencia[ALVOS[nome]]).dropna())
        linhas.append({"cenario": f"Modelo trimestral univariado, {nome}", "observacoes": len(tri.dropna()), "variaveis": 1})
    t = p.trimestral_referencia
    y_tri, _, _ = estacionarizar(_dlog(t[ALVOS["nacional (nominal)"]]).dropna())
    ibge = pd.concat([y_tri, estacionarizar(t["ibge_desocupacao_sp"].diff().dropna())[0],
                      estacionarizar(_dlog(t["ibge_renda_sp"]).dropna())[0]], axis=1).dropna()
    linhas.append({"cenario": "Trimestral, nacional, com desocupacao e renda de SP (IBGE)", "observacoes": len(ibge), "variaveis": 2})
    tab = pd.DataFrame(linhas)
    tab["obs. por variavel"] = (tab["observacoes"] / tab["variaveis"]).round(1)
    return tab


# ----------------------------------------------------------------------------- cobertura
def grafico_disponibilidade(wide: pd.DataFrame, meta: pd.DataFrame) -> str:
    itens = [("FipeZAP nacional (venda)", "fipezap_nacional_res_venda_preco_m2", COR_ALVO),
             ("FipeZAP SJC (venda)", "fipezap_sjc_res_venda_preco_m2", COR_SJC)]
    itens += [(v[0], k, COR_MACRO) for k, v in PREDITORES.items() if k in wide.columns]
    itens += [("Desocupacao SP (trimestral)", "ibge_desocupacao_sp", COR_REAL), ("Renda SP (trimestral)", "ibge_renda_sp", COR_REAL)]
    fig, eixo = plt.subplots(figsize=(10, 6))
    for i, (rotulo, col, cor) in enumerate(reversed(itens)):
        s = wide[col].dropna()
        trimestral = meta.loc[col, "frequencia"] == "Q"
        eixo.plot(s.index, [i] * len(s), "|" if trimestral else "s", color=cor, markersize=6 if trimestral else 3)
    eixo.set_yticks(range(len(itens)))
    eixo.set_yticklabels([r for r, _, _ in reversed(itens)], fontsize=8)
    eixo.set_title("Disponibilidade das series (data de referencia)")
    eixo.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _salvar_fig(fig, "eda_disponibilidade.png")


# ----------------------------------------------------------------------------- orquestracao
def executar() -> dict:
    wide, meta = carregar_wide()
    p = montar_paineis(wide, meta)
    ref, lags = p.mensal_referencia, p.defasagem_mensal
    x_raw = preditores_transformados(ref)
    x_est, pred_tab = preditores_estacionarios(ref, lags)
    figuras: list[str] = []

    desc = descritiva(ref, lags)
    anual = crescimento_anual(ref)
    estac = estacionariedade(ref)
    d_rec = ordem_de_diferenciacao(estac)
    acf_tab, fig = autocorrelacao(ref)
    figuras.append(fig)
    saz_tab, fig = sazonalidade(ref)
    if fig:
        figuras.append(fig)
    sjc_tab, fig = sjc_vs_nacional(ref)
    figuras.append(fig)
    figuras.append(crescimento_e_selic(ref))
    dorm, _ = dormitorios(ref)
    outl = outliers_de_crescimento(ref)
    corr, altos, fig = correlacao_preditores(x_est)
    figuras.append(fig)

    y_est = {n: alvo_estacionario(ref, n)[0] for n in ALVOS_MODELO}
    y_bruto = {n: _dlog(ref[ALVOS[n]]) for n in ALVOS_MODELO}
    rotulo_y = {n: alvo_estacionario(ref, n)[1] for n in ALVOS_MODELO}
    ccf = {"nacional": correlacao_cruzada(y_est["nacional (nominal)"], x_est, lags),
           "SJC": correlacao_cruzada(y_est["SJC (nominal)"], x_est, lags)}
    ccf_b = {"nacional": correlacao_cruzada(y_bruto["nacional (nominal)"], x_raw, lags),
             "SJC": correlacao_cruzada(y_bruto["SJC (nominal)"], x_raw, lags)}
    espurio = {k: comparativo_espurio(ccf_b[k], ccf[k]) for k in ccf}
    figuras.append(heatmap_ccf(ccf))
    gr = {"nacional": granger(y_est["nacional (nominal)"], x_est), "SJC": granger(y_est["SJC (nominal)"], x_est)}
    tri = ccf_trimestral(p)
    baixa = baixa_frequencia(ref, lags)
    estab = estabilidade_subperiodos(ref)
    sufic = suficiencia(ref, x_est, x_raw, p)
    figuras.append(grafico_disponibilidade(wide, meta))

    for nome, df in {
        "descritiva.csv": desc, "crescimento_anual.csv": anual, "estacionariedade.csv": estac, "acf_ljungbox.csv": acf_tab,
        "sazonalidade.csv": saz_tab, "sjc_vs_nacional_ccf.csv": sjc_tab, "dormitorios.csv": dorm, "outliers_crescimento.csv": outl,
        "preditores.csv": pred_tab, "preditores_correlacao_alta.csv": altos, "suficiencia_amostral.csv": sufic,
        "ccf_trimestral.csv": tri, "baixa_frequencia.csv": baixa, "estabilidade_subperiodos.csv": estab, "ccf_nacional.csv": ccf["nacional"], "ccf_sjc.csv": ccf["SJC"],
        "ccf_bruta_nacional.csv": ccf_b["nacional"], "ccf_bruta_sjc.csv": ccf_b["SJC"],
        "espurio_nacional.csv": espurio["nacional"], "espurio_sjc.csv": espurio["SJC"],
        "granger_nacional.csv": gr["nacional"], "granger_sjc.csv": gr["SJC"],
    }.items():
        _salvar_tab(df, nome)

    resultado = dict(desc=desc, anual=anual, estac=estac, d_rec=d_rec, acf=acf_tab, saz=saz_tab, sjc=sjc_tab, dorm=dorm,
                     outl=outl, pred=pred_tab, altos=altos, ccf=ccf, espurio=espurio, granger=gr, tri=tri, baixa=baixa, estab=estab, sufic=sufic,
                     rotulo_y=rotulo_y, figuras=figuras)
    escrever_relatorio(resultado)
    return resultado


def _melhores_ccf(tab: pd.DataFrame, n: int = 6) -> pd.DataFrame:
    sel = tab[tab["significativa"] & tab["utilizavel (lag >= L+1)"]].copy()
    sel["|r|"] = sel["r"].abs()
    return sel.sort_values("|r|", ascending=False).head(n)[["preditor", "lag", "r", "n", "limiar"]]


def escrever_relatorio(r: dict) -> None:
    L = ["# Analise exploratoria: series temporais", "",
         "Gerado por `python main.py eda-series`. Nao editar manualmente. A leitura dos resultados esta em",
         "`docs/ANALISE_EXPLORATORIA.md`. Relacoes calculadas em data de **referencia** (painel `*_referencia`).",
         "Correlacao cruzada e Granger usam series **estacionarias** (secoes 3 e 9); a coluna `utilizavel`",
         "indica se o lag respeita a defasagem de publicacao (lag >= L+1 para prever o mes seguinte).", "",
         "## 1. Series usadas (em nivel)", "", _md(r["desc"]), "",
         "## 2. Crescimento medio por ano (% ao mes)", "", _md(r["anual"]), "",
         "## 3. Estacionariedade dos alvos (ADF e KPSS)", "",
         "Estacionaria = ADF rejeita a raiz unitaria (p<0,05) e KPSS nao rejeita a estacionariedade (p>0,05).", "",
         _md(r["estac"]), "", "Transformacao minima que passa nos dois testes:", ""]
    L += [f"- **{k}**: {v}" for k, v in r["d_rec"].items()]
    L += ["", "## 4. Autocorrelacao", "",
          "O FipeZAP e media movel trimestral e a variacao mensal e muito persistente; a serie estacionaria e a usada nos passos seguintes.", "",
          _md(r["acf"]), "", f"Figura: `{r['figuras'][0]}`", "", "## 5. Sazonalidade", "", _md(r["saz"]), ""]
    if any("sazonalidade" in f for f in r["figuras"]):
        L.append("Ha indicio de sazonalidade; ver `reports/figures/eda_sazonalidade.png`.")
    else:
        L.append("Nao ha indicio de sazonalidade (forca < 0,3 e Kruskal-Wallis p >= 0,05); nenhum grafico foi gerado.")
    L += ["", "## 6. Sao Jose dos Campos x indice nacional", "", _md(r["sjc"]), "",
          "## 7. Faixas de dormitorios (indice nacional)", "", _md(r["dorm"]), "",
          "## 8. Meses atipicos (z robusto > 3,5)", "", _md(r["outl"]) if len(r["outl"]) else "Nenhum.", "",
          "## 9. Preditores e estacionariedade", "",
          "Transformacao inicial e diferencas extras aplicadas ate ADF e KPSS concordarem.", "", _md(r["pred"]), "",
          "Pares de preditores (ja estacionarios) com |correlacao| >= 0,5:", "",
          _md(r["altos"]) if len(r["altos"]) else "Nenhum.", ""]
    for nome, tab in r["ccf"].items():
        chave = "nacional (nominal)" if nome == "nacional" else "SJC (nominal)"
        L += [f"## 10. Correlacao cruzada com o FipeZAP {nome} ({r['rotulo_y'][chave]})", "",
              "Maiores correlacoes significativas e utilizaveis (limiar conservador com n/3):", "",
              _md(_melhores_ccf(tab)) if len(_melhores_ccf(tab)) else "Nenhuma correlacao significativa e utilizavel.", "",
              "Comparativo: maior |r| com as series como vinham (nao estacionarias) e depois de estacionarizar:", "",
              _md(r["espurio"][nome]), ""]
    L += ["Figura: `reports/figures/eda_correlacao_cruzada.png`", ""]
    for nome, tab in r["granger"].items():
        limiar = tab.attrs.get("limiar_bonferroni", np.nan)
        L += [f"## 11. Causalidade de Granger, FipeZAP {nome} (series estacionarias)", "",
              f"Limiar de Bonferroni: p < {limiar:.5f} (sobre {len(PREDITORES)} preditores x {MAX_LAG_GRANGER} lags).", "",
              _md(tab[["preditor", "n", "menor p", "no lag", "p < 0,05", "passa Bonferroni"]], 4), ""]
    b = r["baixa"]
    b = b[b["significativa"] & b["utilizavel (lag >= L+1)"]].copy()
    b["|r|"] = b["r"].abs()
    L += ["## 11b. Canal de baixa frequencia (variacoes de 12 meses)", "",
          "Analise descritiva com janelas sobrepostas (limiar com n/12). Relacoes significativas e utilizaveis, por alvo:", ""]
    for alvo, grupo in b.groupby("alvo (var. 12 meses)", sort=False):
        L += [f"**{alvo}**", "", _md(grupo.sort_values("|r|", ascending=False).head(6)[["preditor", "lag", "r", "n", "limiar (n/12)"]]), ""]
    if b.empty:
        L += ["Nenhuma relacao significativa e utilizavel.", ""]
    ac = r["estab"].attrs.get("autocorr_12", {})
    L += ["## 11c. Estabilidade das relacoes de baixa frequencia por subperiodo", "",
          f"Autocorrelacao no lag 12 das variacoes de 12 meses: preco {ac.get('preco', float('nan')):.2f}, credito {ac.get('credito', float('nan')):.2f}"
          " (series muito persistentes: poucas observacoes independentes).", "", _md(r["estab"], 2), "",
          "## 12. Correlacao cruzada trimestral (nacional, series estacionarias)", "", _md(r["tri"]), "",
          "## 13. Suficiencia amostral (observacoes apos estacionarizar)", "", _md(r["sufic"]), "", "## Figuras geradas", ""]
    L += [f"- `{f}`" for f in r["figuras"]]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
