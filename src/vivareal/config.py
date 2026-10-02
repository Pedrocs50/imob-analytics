from __future__ import annotations

import os
from dataclasses import dataclass, field


DEFAULT_DB_PATH = os.path.join(
    "data",
    "raw",
    "vivareal_jacarei",
    "vivareal_jacarei_20260324.db",
)
DEFAULT_OUTPUT_DIR = os.path.join("data", "processed", "vivareal")
DEFAULT_REPORT_PATH = os.path.join("reports", "results", "vivareal_limpeza.md")


@dataclass(frozen=True, slots=True)
class SegmentoConfig:
    """Regras de limpeza de um segmento. Limites calibrados pelos percentis
    p0,5-p99,5 dos dados ja deduplicados (auditoria de 2026-09); ajustar aqui."""

    nome: str
    property_types: tuple[str, ...]
    sale_price: tuple[float, float]
    usable_area_m2: tuple[float, float]
    preco_m2: tuple[float, float]
    max_bedrooms: int
    max_bathrooms: int
    max_parking_spaces: int
    # Valores POSITIVOS fora da faixa viram ausentes (a linha e mantida). Zero significa
    # "sem taxa" e tambem e mantido. Faixas definidas na analise exploratoria (docs/ANALISE_EXPLORATORIA.md).
    monthly_condo_range: tuple[float, float] = (50, 5_000)
    yearly_iptu_range: tuple[float, float] = (50, 30_000)


APARTAMENTO = SegmentoConfig(
    nome="apartamento",
    property_types=("APARTMENT", "PENTHOUSE", "FLAT"),
    sale_price=(100_000, 3_000_000),
    usable_area_m2=(20, 300),
    preco_m2=(1_500, 20_000),
    max_bedrooms=5,
    max_bathrooms=6,
    max_parking_spaces=5,
)

# CONDOMINIUM no VivaReal e casa em condominio (titulos: "Casa Sobrado", ...).
CASA = SegmentoConfig(
    nome="casa",
    property_types=("HOME", "CONDOMINIUM", "TWO_STORY_HOUSE"),
    sale_price=(100_000, 6_000_000),
    usable_area_m2=(30, 1_500),
    preco_m2=(500, 20_000),
    max_bedrooms=8,
    max_bathrooms=8,
    max_parking_spaces=10,
)


@dataclass(frozen=True, slots=True)
class VivaRealConfig:
    db_path: str = DEFAULT_DB_PATH
    output_dir: str = DEFAULT_OUTPUT_DIR
    report_path: str = DEFAULT_REPORT_PATH
    usage_type: str = "RESIDENTIAL"
    segmentos: tuple[SegmentoConfig, ...] = field(default=(APARTAMENTO, CASA))

    # outliers de preco_m2 por IQR, calculados dentro de cada property_type
    outlier_iqr_factor: float = 1.5
