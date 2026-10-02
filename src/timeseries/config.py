from __future__ import annotations

import os

# banco proprio das series temporais, separado do imoveis.db do scraper
DB_PATH = os.path.join("data", "database", "series_temporais.db")

# respostas originais das APIs, preservadas (nunca sobrescritas)
RAW_MACRO_DIR = os.path.join("data", "raw", "macro")

FIPEZAP_XLSX = os.path.join("data", "raw", "fipezap-serieshistoricas (2).xlsx")

PROCESSED_DIR = os.path.join("data", "processed", "series")
QUALITY_REPORT = os.path.join("reports", "results", "series_qualidade.md")
