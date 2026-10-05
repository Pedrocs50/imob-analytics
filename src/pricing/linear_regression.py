from __future__ import annotations

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from statsmodels.stats.diagnostic import het_breuschpagan

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.vivareal.config import DEFAULT_OUTPUT_DIR

REPORT = os.path.join("reports", "results", "regressao_linear.md")
SEGMENTOS = ("apartamento", "casa", "residencial")
SEMENTE = 42
MIN_ANUNCIOS_BAIRRO = 30  # bairros com menos anuncios (no treino) viram uma categoria unica
# O IPTU fica de fora enquanto a unidade do campo nao for confirmada (docs/ANALISE_EXPLORATORIA.md).
VARIANTES = {
    "base": "area, comodos, comodidades, tipo e bairro",
    "+ condominio informado": "base + indicador de que a taxa de condominio existe",
    "+ valor do condominio": "base + indicador + valor da taxa (ausente imputado pela mediana)",
}


def carregar(segmento: str, pasta: str = DEFAULT_OUTPUT_DIR) -> pd.DataFrame:
    caminho = os.path.join(pasta, f"{segmento}.csv")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"{caminho} nao existe. Rode antes `python main.py vivareal-prep`.")
    df = pd.read_csv(caminho, parse_dates=["created_at"])
    df["created_at"] = df["created_at"].dt.tz_convert(None)
    return df


def _variaveis(df: pd.DataFrame, segmento: str, variante: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Monta X. Retorna (X, colunas numericas, colunas categoricas)."""
    x = pd.DataFrame({
        "log_area": np.log(df["usable_area_m2"]),
        "quartos": df["bedrooms"], "banheiros": df["bathrooms"], "suites": df["suites"],
        "vagas": df["parking_spaces"], "comodidades": df["amenities_count"],
    }, index=df.index)
    numericas = list(x.columns)
    # Cada informacao entra uma unica vez, senao ha colinearidade perfeita: nas casas,
    # em_condominio == (tipo == CONDOMINIUM); no residencial, o tipo ja distingue apartamento,
    # casa e casa em condominio.
    if segmento == "casa":
        x["em_condominio"] = df["em_condominio"]
        numericas.append("em_condominio")
    if variante in ("+ condominio informado", "+ valor do condominio"):
        x["condominio_informado"] = df["condominio_informado"]
        numericas.append("condominio_informado")
    if variante == "+ valor do condominio":
        x["valor_condominio"] = df["monthly_condo"]
        numericas.append("valor_condominio")
    x["bairro"] = df["neighborhood"].fillna("DESCONHECIDO")
    categoricas = ["bairro"]
    if segmento != "casa":
        x["tipo"] = df["property_type"]
        categoricas.append("tipo")
    return x, numericas, categoricas


def _preprocessador(numericas: list[str], categoricas: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", SimpleImputer(strategy="median", add_indicator=True), numericas),
        ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=MIN_ANUNCIOS_BAIRRO,
                              drop="first", sparse_output=False), categoricas),
    ])


def _modelo(numericas: list[str], categoricas: list[str], log_alvo: bool) -> TransformedTargetRegressor | Pipeline:
    pipe = Pipeline([("prep", _preprocessador(numericas, categoricas)), ("ols", LinearRegression())])
    if not log_alvo:
        return pipe
    return TransformedTargetRegressor(regressor=pipe, func=np.log, inverse_func=np.exp)


def _metricas(y: pd.Series, previsto: np.ndarray) -> dict[str, float]:
    return {"RMSE": float(np.sqrt(mean_squared_error(y, previsto))), "MAE": float(mean_absolute_error(y, previsto)),
            "MAPE (%)": float(mean_absolute_percentage_error(y, previsto) * 100), "R2": float(r2_score(y, previsto))}


def _baseline_bairro(treino: pd.DataFrame, teste: pd.DataFrame) -> np.ndarray:
    """Baseline ingenuo: mediana de preco_m2 do bairro no treino (mediana geral se o bairro e novo)."""
    medianas = treino.groupby("neighborhood")["preco_m2"].median()
    return teste["neighborhood"].map(medianas).fillna(treino["preco_m2"].median()).to_numpy()


def _avaliar(df: pd.DataFrame, segmento: str, variante: str, log_alvo: bool) -> list[dict]:
    x, num, cat = _variaveis(df, segmento, variante)
    y = df["preco_m2"]
    linhas = []

    def registrar(validacao: str, real: pd.Series, previsto: np.ndarray, n_treino: int) -> None:
        linhas.append({"segmento": segmento, "variante": variante, "alvo": "log" if log_alvo else "nivel",
                       "validacao": validacao, "n treino": n_treino, "n teste": len(real), **_metricas(real, previsto)})

    # 1) holdout aleatorio 80/20
    i_tr, i_te = train_test_split(df.index, test_size=0.2, random_state=SEMENTE)
    m = _modelo(num, cat, log_alvo).fit(x.loc[i_tr], y.loc[i_tr])
    registrar("holdout aleatorio (20%)", y.loc[i_te], m.predict(x.loc[i_te]), len(i_tr))

    # 2) validacao cruzada de 5 particoes sobre toda a base
    previsto = cross_val_predict(_modelo(num, cat, log_alvo), x, y, cv=KFold(5, shuffle=True, random_state=SEMENTE))
    registrar("5-fold", y, previsto, int(len(df) * 0.8))

    # 3) divisao temporal: treina nos anuncios mais antigos e testa nos 25% mais recentes
    corte = df["created_at"].quantile(0.75)
    i_tr, i_te = df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte]
    m = _modelo(num, cat, log_alvo).fit(x.loc[i_tr], y.loc[i_tr])
    registrar(f"temporal (teste apos {corte:%Y-%m-%d})", y.loc[i_te], m.predict(x.loc[i_te]), len(i_tr))
    return linhas


def _baseline_linhas(df: pd.DataFrame, segmento: str) -> list[dict]:
    y = df["preco_m2"]
    linhas = []

    def registrar(validacao: str, tr: pd.DataFrame, te: pd.DataFrame) -> None:
        linhas.append({"segmento": segmento, "variante": "baseline: mediana do bairro", "alvo": "-", "validacao": validacao,
                       "n treino": len(tr), "n teste": len(te), **_metricas(te["preco_m2"], _baseline_bairro(tr, te))})

    i_tr, i_te = train_test_split(df.index, test_size=0.2, random_state=SEMENTE)
    registrar("holdout aleatorio (20%)", df.loc[i_tr], df.loc[i_te])
    prev = np.zeros(len(df))
    for tr, te in KFold(5, shuffle=True, random_state=SEMENTE).split(df):
        prev[te] = _baseline_bairro(df.iloc[tr], df.iloc[te])
    linhas.append({"segmento": segmento, "variante": "baseline: mediana do bairro", "alvo": "-", "validacao": "5-fold",
                   "n treino": int(len(df) * 0.8), "n teste": len(df), **_metricas(y, prev)})
    corte = df["created_at"].quantile(0.75)
    registrar(f"temporal (teste apos {corte:%Y-%m-%d})", df[df["created_at"] <= corte], df[df["created_at"] > corte])
    return linhas


def coeficientes(df: pd.DataFrame, segmento: str, variante: str) -> tuple[pd.DataFrame, dict]:
    """OLS sobre log(preco_m2) na base inteira, com erros-padrao robustos (HC3). Os coeficientes
    sao aproximadamente a variacao percentual do R$/m2 por unidade da variavel."""
    x, num, cat = _variaveis(df, segmento, variante)
    prep = _preprocessador(num, cat)
    xt = pd.DataFrame(prep.fit_transform(x), columns=prep.get_feature_names_out(), index=df.index)
    xt.columns = [c.replace("num__", "").replace("cat__", "") for c in xt.columns]
    y = np.log(df["preco_m2"])
    res = sm.OLS(y, sm.add_constant(xt)).fit(cov_type="HC3")
    tab = pd.DataFrame({"variavel": res.params.index, "coef": res.params.values, "erro-padrao (HC3)": res.bse.values,
                        "p": res.pvalues.values})
    tab["variacao aprox. no R$/m2 (%)"] = (np.exp(tab["coef"]) - 1) * 100
    bp = het_breuschpagan(res.resid, sm.add_constant(xt))
    return tab, {"R2 (na base toda, log)": res.rsquared, "R2 ajustado": res.rsquared_adj, "n": int(res.nobs),
                 "colunas": xt.shape[1], "Breusch-Pagan p": float(bp[1])}


def figura(df: pd.DataFrame, segmento: str) -> str:
    x, num, cat = _variaveis(df, segmento, "+ condominio informado")
    y = df["preco_m2"]
    i_tr, i_te = train_test_split(df.index, test_size=0.2, random_state=SEMENTE)
    m = _modelo(num, cat, True).fit(x.loc[i_tr], y.loc[i_tr])
    prev = m.predict(x.loc[i_te])
    real = y.loc[i_te]
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.6))
    eixos[0].scatter(real, prev, s=5, alpha=0.3, color="#1f5f99")
    lim = [min(real.min(), prev.min()), max(real.max(), prev.max())]
    eixos[0].plot(lim, lim, "k--", lw=1)
    eixos[0].set_xlabel("R$/m2 real"); eixos[0].set_ylabel("R$/m2 previsto")
    eixos[0].set_title(f"{segmento}: real x previsto (holdout)")
    eixos[1].scatter(prev, real - prev, s=5, alpha=0.3, color="#d9822b")
    eixos[1].axhline(0, color="k", lw=1)
    eixos[1].set_xlabel("R$/m2 previsto"); eixos[1].set_ylabel("residuo (real - previsto)")
    eixos[1].set_title(f"{segmento}: residuos")
    for e in eixos:
        e.grid(alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, f"reg_linear_{segmento}.png")


def executar() -> dict:
    warnings.filterwarnings("ignore")
    todas, coefs, resumo, figuras = [], {}, {}, []
    for segmento in SEGMENTOS:
        df = carregar(segmento)
        for variante in VARIANTES:
            for log_alvo in (True, False):
                todas += _avaliar(df, segmento, variante, log_alvo)
        todas += _baseline_linhas(df, segmento)
        coefs[segmento], resumo[segmento] = coeficientes(df, segmento, "+ condominio informado")
        figuras.append(figura(df, segmento))
        print(f"[REGRESSAO] {segmento}: {len(df)} anuncios")

    metricas = pd.DataFrame(todas)
    salvar_tab(metricas, "regressao_linear_metricas.csv")
    for segmento, tab in coefs.items():
        salvar_tab(tab, f"regressao_linear_coef_{segmento}.csv")
    escrever_relatorio(metricas, coefs, resumo, figuras)
    return {"metricas": metricas, "coefs": coefs, "resumo": resumo, "figuras": figuras}


def escrever_relatorio(metricas: pd.DataFrame, coefs: dict, resumo: dict, figuras: list[str]) -> None:
    L = ["# Regressao linear multipla de preco_m2 (VivaReal)", "",
         "Gerado por `python main.py reg-linear`. Nao editar manualmente. Base: `data/processed/vivareal/*.csv`.", "",
         "Variaveis: log da area, quartos, banheiros, suites, vagas, comodidades e bairro (bairros com menos de "
         f"{MIN_ANUNCIOS_BAIRRO} anuncios no treino viram uma categoria); tipo (apartamento e residencial) ou `em_condominio` (casas). Valores "
         "ausentes sao imputados pela mediana com indicador de ausencia. **O IPTU nao entra** (unidade nao confirmada).", "",
         "Variantes: " + "; ".join(f"**{k}** ({v})" for k, v in VARIANTES.items()) + ".", "",
         "Validacoes: holdout aleatorio de 20%; validacao cruzada de 5 particoes; e divisao **temporal** (treino nos 75% "
         "de anuncios mais antigos pela data de criacao, teste nos 25% mais recentes). Metricas em R$/m2 (RMSE e MAE), "
         "% (MAPE) e R2, sempre na escala original, tambem quando o modelo e ajustado em log.", "",
         "Cuidado: anuncios do mesmo predio ou loteamento sao parecidos e podem estar no treino e no teste, o que "
         "favorece a validacao aleatoria. A divisao temporal e a mais exigente.", ""]
    for segmento in SEGMENTOS:
        m = metricas[metricas["segmento"] == segmento].drop(columns="segmento")
        L += [f"## {segmento}", "", "### Desempenho", "", md(m.round(3), 3), "", "### Coeficientes (variante `+ condominio informado`, alvo log)", ""]
        r, tab = resumo[segmento], coefs[segmento]
        L += [f"R2 na base toda (log): {r['R2 (na base toda, log)']:.3f}; R2 ajustado: {r['R2 ajustado']:.3f}; n = {r['n']}; "
              f"colunas: {r['colunas']}; Breusch-Pagan p = {r['Breusch-Pagan p']:.4f} "
              f"({'heterocedasticidade: usar erros robustos, como feito' if r['Breusch-Pagan p'] < 0.05 else 'sem sinal de heterocedasticidade'}).", ""]
        sem_bairro = tab[~tab["variavel"].str.startswith("bairro_")]
        bairros = tab[tab["variavel"].str.startswith("bairro_")]
        L += [md(sem_bairro, 4), "",
              f"Efeitos de bairro (vs. categoria de referencia): {len(bairros)} coeficientes; de "
              f"{bairros['variacao aprox. no R$/m2 (%)'].min():.0f}% a {bairros['variacao aprox. no R$/m2 (%)'].max():.0f}% "
              f"(tabela completa em `reports/results/eda/regressao_linear_coef_{segmento}.csv`).", ""]
    L += ["## Figuras", ""] + [f"- `{f}`" for f in figuras]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
