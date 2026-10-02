from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_JACAREI_DB_PATH = os.path.join(
    "data",
    "raw",
    "vivareal_jacarei",
    "vivareal_jacarei_20260324.db",
)

DEFAULT_JACAREI_MODEL_DIR = os.path.join("data", "models", "jacarei")


@dataclass(frozen=True, slots=True)
class JacareiModelConfig:
    db_path: str = DEFAULT_JACAREI_DB_PATH
    output_dir: str = DEFAULT_JACAREI_MODEL_DIR
    model_filename: str = "price_per_m2_model.pkl"
    metrics_filename: str = "price_per_m2_metrics.json"
    dataset_filename: str = "dataset_limpo.csv"
    plot_filename: str = "avaliacao_modelo.png"

    # limites de limpeza para apartamento
    sale_price_min: float = 100_000
    sale_price_max: float = 2_000_000 
    usable_area_min: float = 20
    usable_area_max: float = 300
    preco_m2_min: float = 2000
    preco_m2_max: float = 16_000

    # maximo de quartos: 4; banheiro: 4; estacionamento 4

    # limites de limpeza para casa
    # sale_price_min: float = 150_000
    # sale_price_max: float = 5_000_000 
    # usable_area_min: float = 40
    # usable_area_max: float = 1000
    # preco_m2_min: float = 2000
    # preco_m2_max: float = 15_000

    # maximo de quartos: 6; banheiro: 6; tirar a variavel de estacionamento


    # outliers por grupo (IQR dentro de cada property_type)
    outlier_group_col: str = "property_type"
    outlier_iqr_factor: float = 1.5

    # target encoding do bairro
    target_encoding_smoothing: float = 10.0
    target_encoding_splits: int = 5

    # hiperparametros do modelo
    n_estimators: int = 500
    min_samples_leaf: int = 2
    max_features: str = "sqrt"
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5

    @property
    def model_path(self) -> str:
        return os.path.join(self.output_dir, self.model_filename)

    @property
    def metrics_path(self) -> str:
        return os.path.join(self.output_dir, self.metrics_filename)

    @property
    def dataset_path(self) -> str:
        return os.path.join(self.output_dir, self.dataset_filename)

    @property
    def plot_path(self) -> str:
        return os.path.join(self.output_dir, self.plot_filename)