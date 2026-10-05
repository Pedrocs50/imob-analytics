from __future__ import annotations

import os
import time
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import loguniform
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.censo import FEATURES_CENSO
from src.pricing.geo import MIN_ANUNCIOS_SETOR, Cfg, _construir, _montar_x
from src.pricing.linear_regression import SEMENTE, _metricas, carregar

REPORT = os.path.join("reports", "results", "ajuste_gradient_boosting.md")
SEGMENTOS = ("apartamento", "casa", "residencial")
N_ITER_BUSCA = 20
CV_INTERNO = 3
# Conjunto completo de informacao: coordenadas (imputadas), vizinhos, setor IBGE e Censo 2022. Definido a priori,
# sem escolher o melhor conjunto olhando o teste.
CFG = Cfg("gb", "imputadas", vizinhanca=True, setor=True, censo=True, extras=True)

ESPACO = {
    "reg__learning_rate": loguniform(0.02, 0.15),
    "reg__max_leaf_nodes": [8, 15, 31, 63],
    "reg__min_samples_leaf": [10, 20, 40, 80],
    "reg__l2_regularization": [0.0, 1.0, 5.0, 20.0],
    "reg__max_features": [0.5, 0.75, 1.0],
}

NOMES = {"log_area": "area (log)", "quartos": "quartos", "banheiros": "banheiros", "suites": "suites", "vagas": "vagas",
         "comodidades": "comodidades", "em_condominio": "casa em condominio", "condominio_informado": "condominio informado",
         "bairro": "bairro", "lat": "latitude real (vizinhos)", "lon": "longitude real (vizinhos)", "tipo": "tipo do imovel", "lat_i": "latitude", "lon_i": "longitude", "coord_origem": "origem da coordenada",
         "setor": "setor IBGE", "renda_responsavel_media": "renda media do setor", "renda_responsavel_mediana": "renda mediana do setor",
         "densidade_hab_km2": "densidade (hab/km2)", "densidade_domicilios_km2": "densidade (dom/km2)",
         "moradores_por_domicilio": "moradores por domicilio", "pct_domicilios_vagos": "% domicilios vagos", "pessoas": "pessoas no setor"}


def _com_early_stopping(modelo: Pipeline, **params) -> Pipeline:
    modelo.set_params(reg__early_stopping=True, reg__validation_fraction=0.15, reg__n_iter_no_change=25, reg__max_iter=1000, **params)
    return modelo


def _random_forest(num: list[str], cat: list[str]) -> Pipeline:
    """O Random Forest do baseline original, agora com as mesmas variaveis e as mesmas divisoes."""
    prep = ColumnTransformer([("num", "passthrough", num),
                              ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat)])
    return Pipeline([("prep", prep), ("reg", RandomForestRegressor(n_estimators=300, min_samples_leaf=3, max_features=0.5,
                                                                    n_jobs=-1, random_state=SEMENTE))])


def ajustar_segmento(df: pd.DataFrame, segmento: str) -> dict:
    x, num, cat = _montar_x(df, segmento)
    y = df["preco_m2"]
    corte = df["created_at"].quantile(0.75)
    divisoes = {
        "holdout aleatorio (20%)": train_test_split(df.index, test_size=0.2, random_state=SEMENTE),
        f"temporal (teste apos {corte:%Y-%m-%d})": (df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte]),
    }
    linhas, melhores, importancias = [], {}, None
    for nome_div, (tr, te) in divisoes.items():
        padrao = _construir(CFG, num, cat, x.attrs.get("extras")).fit(x.loc[tr], y.loc[tr])
        t0 = time.time()
        busca = RandomizedSearchCV(_com_early_stopping(_construir(CFG, num, cat, x.attrs.get("extras"))), ESPACO, n_iter=N_ITER_BUSCA, cv=KFold(CV_INTERNO, shuffle=True, random_state=SEMENTE),
                                   scoring="neg_mean_absolute_error", random_state=SEMENTE, n_jobs=1, refit=True)
        busca.fit(x.loc[tr], y.loc[tr])  # busca SO no treino desta divisao
        modelos = {"Gradient boosting, parametros padrao": padrao, "Gradient boosting, parametros ajustados": busca.best_estimator_}
        for rotulo, m in modelos.items():
            linhas.append({"segmento": segmento, "validacao": nome_div, "modelo": rotulo, "n treino": len(tr), "n teste": len(te),
                           **_metricas(y.loc[te], m.predict(x.loc[te]))})
        melhores[nome_div] = {k.replace("reg__", ""): (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in busca.best_params_.items()}
        melhores[nome_div]["MAE interno (CV, treino)"] = round(-busca.best_score_, 1)
        melhores[nome_div]["segundos"] = round(time.time() - t0)
        if nome_div.startswith("temporal"):
            imp = permutation_importance(busca.best_estimator_, x.loc[te], y.loc[te], scoring="neg_mean_absolute_error",
                                         n_repeats=5, random_state=SEMENTE, n_jobs=1)
            importancias = pd.DataFrame({"variavel": [NOMES.get(c, c) for c in x.columns], "coluna": x.columns,
                                         "aumento do MAE ao embaralhar (R$/m2)": imp.importances_mean,
                                         "desvio": imp.importances_std}).sort_values("aumento do MAE ao embaralhar (R$/m2)", ascending=False)
    return {"metricas": pd.DataFrame(linhas), "params": melhores, "importancias": importancias}


def _random_forest_linhas(df: pd.DataFrame, segmento: str) -> list[dict]:
    """Random Forest (baseline original) com as mesmas variaveis e divisoes, para comparacao justa."""
    x, num, cat = _montar_x(df, segmento)
    y = df["preco_m2"]
    corte = df["created_at"].quantile(0.75)
    divisoes = {"holdout aleatorio (20%)": train_test_split(df.index, test_size=0.2, random_state=SEMENTE),
                f"temporal (teste apos {corte:%Y-%m-%d})": (df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte])}
    colunas_num = num + ["lat_i", "lon_i", "coord_origem"] + FEATURES_CENSO
    colunas_cat = cat + ["setor"]
    linhas = []
    for nome, (tr, te) in divisoes.items():
        m = _random_forest(colunas_num, colunas_cat)
        xt = x[colunas_num + colunas_cat].copy()
        xt[colunas_num] = xt[colunas_num].fillna(xt.loc[tr, colunas_num].median())
        m.fit(xt.loc[tr], y.loc[tr])
        linhas.append({"segmento": segmento, "validacao": nome, "modelo": "Random Forest (baseline original, mesmas variaveis)", "n treino": len(tr),
                       "n teste": len(te), **_metricas(y.loc[te], m.predict(xt.loc[te]))})
    return linhas


def executar() -> dict:
    warnings.filterwarnings("ignore")
    inicio = time.time()
    todos, params, imps = [], {}, {}
    for segmento in SEGMENTOS:
        df = carregar(segmento)
        r = ajustar_segmento(df, segmento)
        todos.append(r["metricas"])
        todos.append(pd.DataFrame(_random_forest_linhas(df, segmento)))
        params[segmento], imps[segmento] = r["params"], r["importancias"]
        salvar_tab(r["importancias"], f"importancia_variaveis_{segmento}.csv")
        print(f"[AJUSTE] {segmento} concluido ({time.time() - inicio:.0f}s)", flush=True)
    tab = pd.concat(todos, ignore_index=True)
    salvar_tab(tab, "ajuste_gb_metricas.csv")
    fig = figura_importancia(imps)
    escrever_relatorio(tab, params, imps, fig, time.time() - inicio)
    return {"metricas": tab, "params": params}


def figura_importancia(imps: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, len(imps), figsize=(6 * len(imps), 5.4))
    for eixo, (seg, t) in zip(np.atleast_1d(eixos), imps.items()):
        top = t.head(10).iloc[::-1]
        eixo.barh(top["variavel"], top["aumento do MAE ao embaralhar (R$/m2)"], xerr=top["desvio"], color="#1f5f99")
        eixo.set_title(f"{seg}: importancia por permutacao", fontsize=10)
        eixo.set_xlabel("aumento do erro medio (R$/m2) ao embaralhar a variavel")
        eixo.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "importancia_variaveis.png")


def escrever_relatorio(tab: pd.DataFrame, params: dict, imps: dict, fig: str, segundos: float) -> None:
    L = ["# Ajuste de parametros do gradient boosting e importancia das variaveis", "",
         "Gerado por `python main.py ajuste-gb`. Nao editar manualmente.", "",
         "Conjunto de informacao fixado a priori: variaveis do imovel, coordenadas (imputadas), preco dos vizinhos, setor IBGE e Censo 2022 "
         f"(renda, densidade, domicilios). Busca aleatoria ({N_ITER_BUSCA} combinacoes, validacao cruzada de {CV_INTERNO} particoes) **apenas dentro do treino** "
         "de cada divisao, otimizando o erro medio; o teste so e usado para a avaliacao final. O numero de arvores e escolhido por parada antecipada.", "",
         "O Random Forest e o do baseline original do projeto, agora com as mesmas variaveis e divisoes (o R2 de 0,78 dos artefatos antigos nao e comparavel).", "",
         f"Tempo total: {segundos / 60:.1f} min.", ""]
    for seg in SEGMENTOS:
        t = tab[tab["segmento"] == seg].drop(columns="segmento")
        L += [f"## {seg}", "", md(t.round(3), 3), "", "Melhores parametros (por divisao):", ""]
        for div, p in params[seg].items():
            L.append(f"- {div}: {p}")
        L += ["", "Importancia das variaveis (permutacao no teste temporal; as 12 maiores):", "",
              md(imps[seg].head(12)[["variavel", "aumento do MAE ao embaralhar (R$/m2)", "desvio"]].round(2), 2), ""]
    L += ["## Figura", "", f"- `{fig}`", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
