from __future__ import annotations

import json
import os
import time
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.censo import FEATURES_CENSO
from src.pricing.geo import Cfg, _construir, _montar_x
from src.pricing.linear_regression import SEMENTE, _metricas, carregar

REPORT = os.path.join("reports", "results", "modelos_avancados.md")
SEGMENTOS = ("apartamento", "casa", "residencial")
CFG = Cfg("gb", "imputadas", vizinhanca=True, setor=True, censo=True, extras=True)
TRIALS = {"HistGradientBoosting": 40, "LightGBM": 40, "CatBoost": 8}  # CatBoost e bem mais lento; menos tentativas
CV = 3


# ----------------------------------------------------------------------------- preparacao
def preparar(df: pd.DataFrame, segmento: str):
    x, num, cat = _montar_x(df, segmento)
    extras = x.attrs.get("extras", [])
    prep = _construir(CFG, num, cat, extras).named_steps["prep"]
    n_num = len(num) + len(FEATURES_CENSO) + len(extras)
    n_cat = len(cat) + 1  # + setor
    return x, prep, list(range(n_num, n_num + n_cat))


def matrizes(prep, x: pd.DataFrame, y: pd.Series, tr, te):
    """Pre-processamento ajustado so em `tr` (vizinhos leave-one-out no treino, so o treino no teste)."""
    p = clone(prep)
    xt = p.fit_transform(x.loc[tr], y.loc[tr])
    return np.asarray(xt, dtype=float), np.asarray(p.transform(x.loc[te]), dtype=float)


# ----------------------------------------------------------------------------- modelos e espacos de busca
def construir(nome: str, trial: optuna.Trial | None, params: dict | None, cat_idx: list[int]):
    if trial is not None:
        if nome == "HistGradientBoosting":
            params = {"learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True), "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 8, 96),
                      "min_samples_leaf": trial.suggest_int("min_samples_leaf", 5, 80), "l2_regularization": trial.suggest_float("l2_regularization", 1e-3, 30, log=True),
                      "max_features": trial.suggest_float("max_features", 0.3, 1.0)}
        elif nome == "LightGBM":
            params = {"learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True), "num_leaves": trial.suggest_int("num_leaves", 8, 128),
                      "min_child_samples": trial.suggest_int("min_child_samples", 5, 80), "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                      "colsample_bytree": trial.suggest_float("colsample_bytree", 0.2, 1.0), "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 50, log=True),
                      "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True), "n_estimators": trial.suggest_int("n_estimators", 150, 1200),
                      "objective": trial.suggest_categorical("objective", ["regression", "regression_l1", "huber"])}
        else:
            params = {"depth": trial.suggest_int("depth", 4, 7), "learning_rate": trial.suggest_float("learning_rate", 0.05, 0.25, log=True),
                      "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1, 30, log=True), "iterations": trial.suggest_int("iterations", 150, 450)}
    if nome == "HistGradientBoosting":
        return HistGradientBoostingRegressor(categorical_features=cat_idx, max_iter=1000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=25, random_state=SEMENTE, **params), params
    if nome == "LightGBM":
        return LGBMRegressor(subsample_freq=1, random_state=SEMENTE, verbosity=-1, n_jobs=4, **params), params
    base = {"iterations": 400, "depth": 6, "learning_rate": 0.08}  # padrao reduzido (o oficial usa 1000 iteracoes)
    return CatBoostRegressor(random_seed=SEMENTE, verbose=0, thread_count=6, border_count=64, **{**base, **params}), params


def ajustar_e_prever(nome: str, modelo, Xtr, ytr, Xte, cat_idx):
    if nome == "LightGBM":
        modelo.fit(Xtr, ytr, categorical_feature=cat_idx)
    elif nome == "CatBoost":
        a, b = pd.DataFrame(Xtr), pd.DataFrame(Xte)
        for c in cat_idx:
            a[c], b[c] = a[c].astype(int), b[c].astype(int)
        modelo.fit(a, ytr, cat_features=cat_idx)
        return modelo.predict(b)
    else:
        modelo.fit(Xtr, ytr)
    return modelo.predict(Xte)


def buscar(nome: str, folds, cat_idx: list[int]) -> dict:
    """Busca bayesiana (TPE) minimizando o erro medio absoluto na validacao cruzada interna (so no treino)."""
    def objetivo(trial):
        erros = []
        for Xtr, ytr, Xva, yva in folds:
            modelo, _ = construir(nome, trial, None, cat_idx)
            erros.append(np.mean(np.abs(yva - ajustar_e_prever(nome, modelo, Xtr, ytr, Xva, cat_idx))))
        return float(np.mean(erros))

    estudo = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEMENTE))
    estudo.optimize(objetivo, n_trials=TRIALS[nome], show_progress_bar=False)
    return {"params": estudo.best_params, "mae_cv": estudo.best_value, "trials": len(estudo.trials)}


# ----------------------------------------------------------------------------- execucao por segmento
def segmento(df: pd.DataFrame, nome_seg: str) -> dict:
    x, prep, cat_idx = preparar(df, nome_seg)
    y = df["preco_m2"]
    corte = df["created_at"].quantile(0.75)
    tr, te = df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte]

    # particoes internas (so no treino) com pre-processamento ja calculado
    folds, idx_cv = [], []
    for a, b in KFold(CV, shuffle=True, random_state=SEMENTE).split(tr):
        Xa, Xb = matrizes(prep, x, y, tr[a], tr[b])
        folds.append((Xa, y.loc[tr[a]].to_numpy(), Xb, y.loc[tr[b]].to_numpy()))
        idx_cv.append(tr[b])
    Xtr, Xte = matrizes(prep, x, y, tr, te)
    ytr, yte = y.loc[tr].to_numpy(), y.loc[te].to_numpy()

    linhas, previsoes, cv_prev, achados = [], {}, {}, {}
    for nome in TRIALS:
        t0 = time.time()
        padrao, _ = construir(nome, None, {}, cat_idx)
        prev_padrao = ajustar_e_prever(nome, padrao, Xtr, ytr, Xte, cat_idx)
        r = buscar(nome, folds, cat_idx)
        modelo, _ = construir(nome, None, r["params"], cat_idx)
        prev = ajustar_e_prever(nome, modelo, Xtr, ytr, Xte, cat_idx)
        previsoes[nome] = prev
        # previsoes fora da amostra no treino (validacao cruzada interna) para calibrar os intervalos
        oof = np.zeros(len(tr))
        for k, (Xa, ya, Xb, yb) in enumerate(folds):
            m, _ = construir(nome, None, r["params"], cat_idx)
            oof[np.searchsorted(tr, idx_cv[k])] = ajustar_e_prever(nome, m, Xa, ya, Xb, cat_idx)
        cv_prev[nome] = oof
        achados[nome] = r
        linhas.append({"segmento": nome_seg, "modelo": f"{nome}, parametros padrao", **_metricas(pd.Series(yte), prev_padrao)})
        linhas.append({"segmento": nome_seg, "modelo": f"{nome}, ajustado (Optuna)", **_metricas(pd.Series(yte), prev)})
        print(f"[AVANCADOS] {nome_seg} {nome}: MAE CV {r['mae_cv']:.0f} | teste MAE {np.mean(np.abs(yte - prev)):.0f} ({time.time() - t0:.0f}s)", flush=True)

    conjunto = np.mean([previsoes[n] for n in TRIALS], axis=0)
    linhas.append({"segmento": nome_seg, "modelo": "Conjunto (media dos 3 ajustados)", **_metricas(pd.Series(yte), conjunto)})
    # intervalos conformais pelo erro relativo fora da amostra no treino (validacao cruzada interna)
    oof = np.mean([cv_prev[n] for n in TRIALS], axis=0)
    rel = np.abs(ytr - oof) / np.maximum(oof, 1.0)
    intervalos = []
    for nivel in (0.8, 0.9):
        q = float(np.quantile(rel, nivel))
        dentro = np.abs(yte - conjunto) <= q * conjunto
        intervalos.append({"segmento": nome_seg, "nivel nominal": nivel, "cobertura no teste temporal": float(dentro.mean()),
                           "largura media (R$/m2)": float(2 * q * conjunto.mean()), "erro relativo no quantil": q})
    return {"metricas": pd.DataFrame(linhas), "params": achados, "intervalos": pd.DataFrame(intervalos),
            "teste": pd.DataFrame({"preco_m2": yte, "previsto": conjunto, "created_at": df.loc[te, "created_at"].to_numpy()})}


def executar() -> dict:
    warnings.filterwarnings("ignore")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    inicio = time.time()
    res = {s: segmento(carregar(s), s) for s in SEGMENTOS}
    metricas = pd.concat([r["metricas"] for r in res.values()], ignore_index=True)
    intervalos = pd.concat([r["intervalos"] for r in res.values()], ignore_index=True)
    salvar_tab(metricas, "modelos_avancados_metricas.csv")
    salvar_tab(intervalos, "modelos_avancados_intervalos.csv")
    os.makedirs(os.path.join("reports", "results", "modelos_avancados"), exist_ok=True)
    with open(os.path.join("reports", "results", "modelos_avancados", "params.json"), "w", encoding="utf-8") as f:
        json.dump({s: {n: r["params"] for n, r in v["params"].items()} for s, v in res.items()}, f, indent=1)
    fig = figura(res)
    escrever_relatorio(metricas, intervalos, {s: r["params"] for s, r in res.items()}, fig, time.time() - inicio)
    print(f"[AVANCADOS] concluido em {(time.time() - inicio) / 60:.1f} min")
    return res


def figura(res: dict) -> str:
    fig, eixos = plt.subplots(1, len(res), figsize=(5.4 * len(res), 5))
    for eixo, (seg, r) in zip(np.atleast_1d(eixos), res.items()):
        t = r["teste"]
        eixo.scatter(t["preco_m2"], t["previsto"], s=4, alpha=0.3, color="#1f5f99")
        lim = [t[["preco_m2", "previsto"]].min().min(), t[["preco_m2", "previsto"]].max().max()]
        eixo.plot(lim, lim, "k--", lw=1)
        eixo.set_title(f"{seg}: real x previsto (conjunto, teste temporal)", fontsize=9)
        eixo.set_xlabel("R$/m2 real"); eixo.set_ylabel("R$/m2 previsto"); eixo.grid(alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "modelos_avancados_real_previsto.png")


def escrever_relatorio(metricas: pd.DataFrame, intervalos: pd.DataFrame, params: dict, fig: str, segundos: float) -> None:
    L = ["# Modelos avancados de precificacao: busca bayesiana, conjunto e intervalos", "",
         "Gerado por `python main.py modelos-avancados`. Nao editar manualmente.", "",
         "Conjunto de informacao completo: imovel, terreno e palavras do anuncio, coordenadas (imputadas), preco dos vizinhos, setor IBGE e Censo 2022. "
         "Divisao **temporal** (teste nos 25% mais recentes). Busca de parametros bayesiana (Optuna/TPE) minimizando o erro medio na validacao cruzada "
         f"de {CV} particoes **so no treino**; tentativas: " + ", ".join(f"{k} {v}" for k, v in TRIALS.items()) + ". O conjunto e a media dos tres modelos ajustados. "
         "Os intervalos sao conformais pelo erro relativo fora da amostra no treino.", "", f"Tempo total: {segundos / 60:.1f} min.", ""]
    for seg in SEGMENTOS:
        L += [f"## {seg}", "", md(metricas[metricas["segmento"] == seg].drop(columns="segmento").round(3), 3), "",
              "Melhores parametros encontrados:", ""] + [f"- {n}: {r['params']} (MAE na validacao interna {r['mae_cv']:.0f})" for n, r in params[seg].items()]
        L += ["", "Intervalos de previsao (R$/m2):", "", md(intervalos[intervalos["segmento"] == seg].drop(columns="segmento").round(3), 3), ""]
    L += ["## Figura", "", f"- `{fig}`", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
