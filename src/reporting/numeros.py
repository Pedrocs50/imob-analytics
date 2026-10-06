"""Todos os numeros citados no relatorio, lidos dos resultados salvos (nunca digitados). `coletar()` devolve um dicionario aninhado;
o que nao existir vira None e a secao correspondente mostra um aviso."""
from __future__ import annotations

import os
import re

import numpy as np
import pandas as pd

from src.visualization import dados

SEGMENTOS3 = ("apartamento", "casa", "residencial")
LIMPEZA = os.path.join("reports", "results", "vivareal_limpeza.md")
ETAPAS = [("OLS base (sem coordenadas)", "Regressão linear (variáveis do imóvel e bairro)"),
          ("OLS + vizinhos (coord. imputadas)", "Linear + preço dos vizinhos mais próximos"),
          ("Gradient boosting sem coordenadas", "Gradient boosting, sem coordenadas"),
          ("Gradient boosting com lat/lon imputadas", "+ coordenadas (imputadas pelo bairro)"),
          ("Gradient boosting imputadas + vizinhos + setor + Censo", "+ vizinhos, setor IBGE e Censo 2022"),
          ("GB completo + terreno e texto", "+ terreno e texto do anúncio"),
          ("LightGBM, ajustado (Optuna)", "LightGBM ajustado (Optuna)"),
          ("Conjunto (media dos 3 ajustados)", "Conjunto final de 3 modelos")]


def _contagens_limpeza() -> dict:
    if not os.path.exists(LIMPEZA):
        return {}
    t = open(LIMPEZA, encoding="utf-8").read()
    def pega(padrao):
        m = re.search(padrao, t)
        return int(m.group(1)) if m else None
    return {"bruto": pega(r"registros na tabela `listings` \| (\d+)"), "residencial": pega(r"usage_type = RESIDENTIAL \| (\d+)"),
            "duplicatas": pega(r"\((?:mantido[^)]*?; )?(\d+) removidas\)"), "dedup": pega(r"apos remover duplicatas[^|]*\| (\d+)")}


def _evolucao() -> pd.DataFrame | None:
    geo, av = dados.eda("regressao_geo_metricas.csv"), dados.eda("modelos_avancados_metricas.csv")
    if geo is None or av is None:
        return None
    temporal = geo[geo["validacao"].str.contains("temporal") & (geo["subconjunto"] == "todos os anuncios")]
    linhas = []
    for nome, rotulo in ETAPAS:
        linha = {"Etapa": rotulo}
        for seg in SEGMENTOS3:
            fonte = av if nome in ("LightGBM, ajustado (Optuna)", "Conjunto (media dos 3 ajustados)") else temporal
            r = fonte[(fonte["modelo"] == nome) & (fonte["segmento"] == seg)]
            linha[seg] = float(r["R2"].iloc[0]) if len(r) else np.nan
        linhas.append(linha)
    return pd.DataFrame(linhas)


def _r2_preco_total() -> dict:
    """R2 e MAPE do PRECO TOTAL (R$/m2 x area), por previsoes fora da amostra em 5 particoes aleatorias: comparavel ao que a literatura
    brasileira reporta (preco total, divisao aleatoria). Os modelos do projeto sao avaliados no R$/m2, mais exigente."""
    p = dados.projecao_anuncios()
    if p is None:
        return {}
    out = {}
    for seg in dados.SEGMENTOS:
        d = p[p["segmento"] == seg]
        real, est = d["preco_m2_pedido"] * d["area_m2"], d["preco_m2_estimado_mar2026"] * d["area_m2"]
        out[seg] = {"R2": float(1 - ((real - est) ** 2).sum() / ((real - real.mean()) ** 2).sum()), "MAPE": float((np.abs(real - est) / real).mean() * 100),
                    "erro_relativo_mediano": float((np.abs(d["preco_m2_pedido"] - d["preco_m2_estimado_mar2026"]) / d["preco_m2_estimado_mar2026"]).median() * 100),
                    "n": int(len(d))}
    return out


def _series() -> dict:
    out = {}
    for chave in ("nacional", "SJC"):
        m = dados.csv(os.path.join(dados.LSTM, f"lstm_{chave}_metricas.csv"))
        dm = dados.csv(os.path.join(dados.LSTM, f"lstm_{chave}_dm.csv"))
        ar = dados.csv(os.path.join(dados.ARIMA, f"arima_{chave}_nominal_metricas.csv"))
        out[chave] = {"modelos": m, "dm": dm, "arima": ar}
    return out


def coletar() -> dict:
    av = dados.eda("modelos_avancados_metricas.csv")
    n = {"limpeza": _contagens_limpeza(), "evolucao": _evolucao(), "avancados": av, "intervalos": dados.eda("modelos_avancados_intervalos.csv"),
         "preco_total": _r2_preco_total(), "series": _series(), "sens_grupos": dados.eda("sens_grupos.csv"), "sens_cenarios": dados.eda("sens_cenarios.csv"),
         "tendencias": dados.eda("projecao_cenarios_tendencia.csv"), "ajuste_gb": dados.eda("ajuste_gb_metricas.csv"),
         "anuncios": {s: dados.anuncios(s) for s in SEGMENTOS3}, "projecao": dados.projecao_anuncios(), "por_setor": dados.eda("projecao_por_setor.csv")}
    if av is not None:
        n["conjunto"] = {r["segmento"]: r for _, r in av[av["modelo"].str.startswith("Conjunto")].iterrows()}
        n["lightgbm"] = {r["segmento"]: r for _, r in av[av["modelo"] == "LightGBM, ajustado (Optuna)"].iterrows()}
    return n
