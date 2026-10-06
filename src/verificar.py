"""`python main.py verificar`: confere ambiente, dados de entrada e resultados ja gerados, e diz quais comandos podem rodar.
So le o disco (nao altera nada)."""
from __future__ import annotations

import importlib
import os
import sys

from src.timeseries.config import DB_PATH as DB_SERIES, FIPEZAP_XLSX
from src.vivareal.config import DEFAULT_DB_PATH as DB_VIVAREAL

BIBLIOTECAS = ["pandas", "numpy", "sklearn", "statsmodels", "geopandas", "torch", "lightgbm", "catboost", "optuna", "plotly", "folium", "markdown", "matplotlib", "openpyxl"]
IBGE = os.path.join("data", "raw", "ibge")
PROC = os.path.join("data", "processed")
RES = os.path.join("reports", "results")
ENTRADAS = {
    "Base VivaReal do orientador (.db)": DB_VIVAREAL,
    "Excel do FipeZAP": FIPEZAP_XLSX,
    "Setores de Jacareí (IBGE, .gpkg)": os.path.join(IBGE, "jacarei_setores_2022.gpkg"),
    "Censo 2022 de Jacareí (.csv)": os.path.join(IBGE, "jacarei_censo2022_setores.csv"),
}
SAIDAS = {
    "datasets VivaReal limpos": os.path.join(PROC, "vivareal", "casa.csv"),
    "banco de séries temporais": DB_SERIES,
    "painéis de séries (as-of)": os.path.join(PROC, "series", "painel_mensal_referencia.csv"),
    "ARIMA": os.path.join(RES, "arima", "arima_nacional_nominal_metricas.csv"),
    "LSTM em painel": os.path.join(RES, "lstm", "lstm_SJC_metricas.csv"),
    "modelos finais (Optuna)": os.path.join(RES, "modelos_avancados", "params.json"),
    "sensibilidade": os.path.join(RES, "eda", "sens_grupos.csv"),
    "projeção de preço": os.path.join(PROC, "vivareal", "projecao_anuncios.csv"),
    "painel interativo": os.path.join("reports", "figures", "painel_interativo.html"),
    "relatório analítico": os.path.join("reports", "relatorio_analitico.md"),
}
# comando -> (o que precisa existir, rotulo da entrada/saida)
COMANDOS = {
    "vivareal-prep": ["Base VivaReal do orientador (.db)"],
    "series-coletar": [],
    "series-fipezap": ["Excel do FipeZAP"],
    "series-painel": ["banco de séries temporais"],
    "arima / arima-plus / lstm": ["painéis de séries (as-of)"],
    "reg-linear / reg-geo / ajuste-gb": ["datasets VivaReal limpos", "Setores de Jacareí (IBGE, .gpkg)", "Censo 2022 de Jacareí (.csv)"],
    "modelos-avancados (~70 min)": ["datasets VivaReal limpos", "Setores de Jacareí (IBGE, .gpkg)", "Censo 2022 de Jacareí (.csv)"],
    "sensibilidade / projecao / prever": ["modelos finais (Optuna)", "painéis de séries (as-of)"],
    "painel / relatorio (usam o que existir; o que faltar vira aviso no cartão)": [],
}


def _existe(rotulo: str) -> bool:
    return os.path.exists({**ENTRADAS, **SAIDAS}[rotulo])


def executar() -> int:
    print("== Ambiente ==")
    ok_py = sys.version_info >= (3, 11)
    print(f"  {'OK   ' if ok_py else 'FALTA'} Python {sys.version.split()[0]} (requer 3.11 ou superior)")
    faltam = []
    for lib in BIBLIOTECAS:
        try:
            m = importlib.import_module(lib)
            print(f"  OK    {lib} {getattr(m, '__version__', '')}")
        except Exception:  # biblioteca ausente ou quebrada
            faltam.append(lib)
            print(f"  FALTA {lib}")
    print("\n== Dados de entrada ==")
    for nome, caminho in ENTRADAS.items():
        print(f"  {'OK   ' if os.path.exists(caminho) else 'FALTA'} {nome}: {caminho}")
    print("\n== Resultados já gerados ==")
    for nome, caminho in SAIDAS.items():
        print(f"  {'OK   ' if os.path.exists(caminho) else '-    '} {nome}: {caminho}")
    print("\n== O que pode rodar agora ==")
    for cmd, req in COMANDOS.items():
        pend = [r for r in req if not _existe(r)]
        print(f"  {'PODE' if not pend else 'NÃO '} {cmd}" + (f"  (falta: {', '.join(pend)})" if pend else ""))
    if faltam:
        print(f"\nInstale as bibliotecas que faltam: python -m pip install -r requirements.txt  ({', '.join(faltam)})")
    if not os.path.exists(DB_VIVAREAL):
        print("\nSem a base do orientador não dá para refazer os modelos, mas você ainda pode abrir os resultados já versionados em reports/ e docs/.")
    return 0 if ok_py and not faltam else 1
