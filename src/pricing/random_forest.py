from __future__ import annotations

import json
import math
import os
import pickle
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.pricing.config import JacareiModelConfig


@dataclass(slots=True)
class JacareiModelResult:
    rows_loaded: int
    rows_after_filter: int
    rows_train: int
    rows_test: int
    mae: float
    rmse: float
    mape: float
    r2: float
    cv_mae_mean: float
    cv_mae_std: float
    model_path: str
    metrics_path: str
    dataset_path: str
    plot_path: str


class JacareiPricePerM2Model:
    """
    Baseline para prever preco por metro quadrado usando o banco VivaReal de Jacarei.
    Usa RandomForest com target encoding para bairro (com CV para evitar leakage),
    remocao de outliers por grupo (property_type) e validacao cruzada para metricas
    mais estaveis. Organizada para facilitar comparacao futura com XGBoost, redes
    neurais e variantes com geolocalizacao.
    """

    def __init__(self, config: JacareiModelConfig | None = None) -> None:
        self.config = config or JacareiModelConfig()
        self._neighborhood_encoding_map: pd.Series | None = None
        self._neighborhood_global_mean: float | None = None

    @property
    def db_path(self) -> str:
        return self.config.db_path

    @property
    def output_dir(self) -> str:
        return self.config.output_dir

    @property
    def model_path(self) -> str:
        return self.config.model_path

    @property
    def metrics_path(self) -> str:
        return self.config.metrics_path

    @property
    def dataset_path(self) -> str:
        return self.config.dataset_path

    @property
    def plot_path(self) -> str:
        return self.config.plot_path

    def train(self) -> JacareiModelResult:
        try:
            from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.impute import SimpleImputer
            from sklearn.metrics import (
                mean_absolute_error,
                mean_absolute_percentage_error,
                mean_squared_error,
                r2_score,
            )
            from sklearn.model_selection import cross_val_score, train_test_split
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import OneHotEncoder
        except ImportError as exc:
            raise RuntimeError(
                "scikit-learn nao esta instalado. Execute `python -m pip install -r requirements.txt`."
            ) from exc

        df = self._carregar_listings()
        rows_loaded = len(df)
        print(f"[JACAREI] {rows_loaded} registros carregados do banco externo.")

        df = self._preparar_base(df)
        df = self._filtrar_base(df)
        df = self._remover_outliers_por_grupo(df)
        rows_after_filter = len(df)
        print(f"[JACAREI] {rows_after_filter} registros restantes apos a filtragem.")

        if rows_after_filter < 100:
            raise RuntimeError(
                "Poucos registros apos a filtragem. Verifique se o banco externo foi colocado corretamente."
            )

        target_column = "preco_m2"

        # Target encoding do bairro (com CV, calculado ANTES do split para simplicidade
        # pedagogica; para producao real, mova para dentro do pipeline por fold)
        df["neighborhood_encoded"] = self._target_encode_cv(
            df, col="neighborhood", target=target_column
        )

        feature_columns_numeric = [
            "usable_area_m2",
            "bedrooms",
            "bathrooms",
            "suites",
            "parking_spaces",
            # "yearly_iptu",
            # "monthly_condo",
            # "amenities_count",
            # "neighborhood_encoded",
        ]
        feature_columns_categorical = [
            "property_type",
            "listing_type",
        ]

        model_frame = df[
            feature_columns_numeric + feature_columns_categorical + [target_column]
        ].copy()
        self._salvar_dataset_limpo(model_frame)

        x = model_frame[feature_columns_numeric + feature_columns_categorical]
        y = model_frame[target_column]

        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )

        try:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

        preprocessor = ColumnTransformer(
            transformers=[
                ("numeric", SimpleImputer(strategy="median"), feature_columns_numeric),
                (
                    "categorical",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", encoder),
                        ]
                    ),
                    feature_columns_categorical,
                ),
            ]
        )

        model = RandomForestRegressor(
            n_estimators=self.config.n_estimators,
            random_state=self.config.random_state,
            n_jobs=-1,
            min_samples_leaf=self.config.min_samples_leaf,
            max_features=self.config.max_features,
        )

        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )
        wrapped_model = TransformedTargetRegressor(
            regressor=pipeline,
            func=np.log1p,
            inverse_func=np.expm1,
        )

        print("[JACAREI] Rodando cross-validation para metricas estaveis...")
        cv_scores = cross_val_score(
            wrapped_model,
            x,
            y,
            cv=self.config.cv_folds,
            scoring="neg_mean_absolute_error",
            n_jobs=-1,
        )
        cv_mae_mean = float(-cv_scores.mean())
        cv_mae_std = float(cv_scores.std())
        print(f"[JACAREI] MAE via CV ({self.config.cv_folds}-fold): {cv_mae_mean:,.2f} (+/- {cv_mae_std:,.2f})")

        print("[JACAREI] Treinando modelo final no split de treino...")
        wrapped_model.fit(x_train, y_train)

        predictions = wrapped_model.predict(x_test)
        mae = float(mean_absolute_error(y_test, predictions))
        rmse = float(math.sqrt(mean_squared_error(y_test, predictions)))
        mape = float(mean_absolute_percentage_error(y_test, predictions))
        r2 = float(r2_score(y_test, predictions))

        self._salvar_modelo(wrapped_model)
        self._salvar_grafico_avaliacao(y_test, predictions)
        self._salvar_metricas(
            {
                "db_path": self.db_path,
                "rows_loaded": rows_loaded,
                "rows_after_filter": rows_after_filter,
                "rows_train": len(x_train),
                "rows_test": len(x_test),
                "mae": mae,
                "rmse": rmse,
                "mape": mape,
                "r2": r2,
                "cv_mae_mean": cv_mae_mean,
                "cv_mae_std": cv_mae_std,
                "features_numeric": feature_columns_numeric,
                "features_categorical": feature_columns_categorical,
                "target": target_column,
            }
        )

        print(
            f"[JACAREI] Modelo salvo em {self.model_path} | "
            f"MAE={mae:,.2f} | RMSE={rmse:,.2f} | MAPE={mape:.2%} | R2={r2:.3f}"
        )

        return JacareiModelResult(
            rows_loaded=rows_loaded,
            rows_after_filter=rows_after_filter,
            rows_train=len(x_train),
            rows_test=len(x_test),
            mae=mae,
            rmse=rmse,
            mape=mape,
            r2=r2,
            cv_mae_mean=cv_mae_mean,
            cv_mae_std=cv_mae_std,
            model_path=self.model_path,
            metrics_path=self.metrics_path,
            dataset_path=self.dataset_path,
            plot_path=self.plot_path,
        )

    def _carregar_listings(self) -> pd.DataFrame:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Arquivo nao encontrado: {self.db_path}. Coloque o banco VivaReal nesse caminho."
            )

        with sqlite3.connect(self.db_path) as connection:
            return pd.read_sql_query("SELECT * FROM listings", connection)

    def _preparar_base(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["usable_area_m2"] = self._coluna_numerica(df, "usable_area_m2")
        df["sale_price"] = self._coluna_numerica(df, "sale_price")
        df["bedrooms"] = self._coluna_numerica(df, "bedrooms")
        df["bathrooms"] = self._coluna_numerica(df, "bathrooms")
        df["suites"] = self._coluna_numerica(df, "suites")
        df["parking_spaces"] = self._coluna_numerica(df, "parking_spaces")
        df["yearly_iptu"] = self._coluna_numerica(df, "yearly_iptu")
        df["monthly_condo"] = self._coluna_numerica(df, "monthly_condo")

        df["property_type"] = self._coluna_texto(df, "property_type")
        df["listing_type"] = self._coluna_texto(df, "listing_type")
        df["usage_type"] = self._coluna_texto(df, "usage_type")
        df["neighborhood"] = self._coluna_texto(df, "neighborhood")

        amenities = df["amenities"] if "amenities" in df.columns else pd.Series([None] * len(df), index=df.index)
        df["amenities_count"] = amenities.apply(self._contar_amenidades)
        df["preco_m2"] = df["sale_price"] / df["usable_area_m2"]

        return df

    def _filtrar_base(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        df = df.copy()
        df = df[df["usage_type"].eq("RESIDENTIAL")]
        df = df[df["sale_price"].between(cfg.sale_price_min, cfg.sale_price_max)]
        df = df[df["usable_area_m2"].between(cfg.usable_area_min, cfg.usable_area_max)]
        df = df[df["preco_m2"].between(cfg.preco_m2_min, cfg.preco_m2_max)]
        df = df.dropna(subset=["preco_m2", "usable_area_m2", "sale_price"])
        return df

    def _remover_outliers_por_grupo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers de preco_m2 usando IQR calculado DENTRO de cada grupo
        (por padrao, property_type). Evita que o corte fixo prejudique tipos
        de imovel com faixas de preco naturalmente diferentes (ex: chacaras
        vs apartamentos).
        """
        cfg = self.config
        group_col = cfg.outlier_group_col
        fator = cfg.outlier_iqr_factor

        df = df.copy()
        agrupado = df.groupby(group_col)["preco_m2"]

        q1 = agrupado.transform("quantile", 0.25)
        q3 = agrupado.transform("quantile", 0.75)
        iqr = q3 - q1

        limite_inf = q1 - fator * iqr
        limite_sup = q3 + fator * iqr

        mascara = df["preco_m2"].between(limite_inf, limite_sup)
        return df[mascara].reset_index(drop=True)

    def _target_encode_cv(self, df: pd.DataFrame, col: str, target: str) -> pd.Series:
        """
        Codifica uma coluna categorica (ex: neighborhood) pela media suavizada
        do target, calculada via K-Fold para evitar vazamento de dados (a media
        de cada linha nunca inclui a propria linha).
        """
        from sklearn.model_selection import KFold

        cfg = self.config
        global_mean = float(df[target].mean())
        encoded = pd.Series(index=df.index, dtype="float64")

        kf = KFold(n_splits=cfg.target_encoding_splits, shuffle=True, random_state=cfg.random_state)
        for train_idx, val_idx in kf.split(df):
            train_fold = df.iloc[train_idx]
            stats = train_fold.groupby(col)[target].agg(["mean", "count"])
            smoothing = cfg.target_encoding_smoothing
            smooth_mean = (stats["mean"] * stats["count"] + global_mean * smoothing) / (
                stats["count"] + smoothing
            )
            val_fold_col = df.iloc[val_idx][col]
            encoded.iloc[val_idx] = val_fold_col.map(smooth_mean).fillna(global_mean)

        # guarda o mapeamento "final" (usando a base inteira) para uso em inferencia futura
        stats_full = df.groupby(col)[target].agg(["mean", "count"])
        smoothing = cfg.target_encoding_smoothing
        self._neighborhood_encoding_map = (
            stats_full["mean"] * stats_full["count"] + global_mean * smoothing
        ) / (stats_full["count"] + smoothing)
        self._neighborhood_global_mean = global_mean

        return encoded

    def _salvar_dataset_limpo(self, df: pd.DataFrame) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        df.to_csv(self.dataset_path, index=False)

    def _salvar_modelo(self, model) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.model_path, "wb") as arquivo:
            pickle.dump(
                {
                    "model": model,
                    "neighborhood_encoding_map": self._neighborhood_encoding_map,
                    "neighborhood_global_mean": self._neighborhood_global_mean,
                },
                arquivo,
            )

    def _salvar_metricas(self, metricas: dict) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.metrics_path, "w", encoding="utf-8") as arquivo:
            json.dump(metricas, arquivo, ensure_ascii=False, indent=2)

    def _salvar_grafico_avaliacao(self, y_true: pd.Series, y_pred: pd.Series) -> None:
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise RuntimeError(
                "matplotlib nao esta instalado. Execute `python -m pip install -r requirements.txt`."
            ) from exc

        os.makedirs(self.output_dir, exist_ok=True)

        y_true_series = pd.Series(y_true).reset_index(drop=True)
        y_pred_series = pd.Series(y_pred).reset_index(drop=True)
        erro = y_true_series - y_pred_series
        valor_maximo = max(float(y_true_series.max()), float(y_pred_series.max())) * 1.05
        ordem = y_true_series.sort_values().index
        y_true_ordenado = y_true_series.loc[ordem].reset_index(drop=True)
        y_pred_ordenado = y_pred_series.loc[ordem].reset_index(drop=True)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5), tight_layout=True)

        axes[0].scatter(y_true_series, y_pred_series, alpha=0.35, color="#2f7bba", edgecolor="none")
        axes[0].plot([0, valor_maximo], [0, valor_maximo], linestyle="--", color="#d62728", linewidth=2)
        axes[0].set_xlabel("Valor real do preco por m2")
        axes[0].set_ylabel("Valor previsto do preco por m2")
        axes[0].set_title("Real vs Previsto")
        axes[0].grid(True, alpha=0.25)

        axes[1].plot(y_true_ordenado, color="#2f7bba", linewidth=2, label="Real")
        axes[1].plot(y_pred_ordenado, color="#ff9800", linewidth=2, label="Previsto")
        axes[1].set_xlabel("Amostras ordenadas por valor real")
        axes[1].set_ylabel("Preco por m2")
        axes[1].set_title("Curva de regressao ordenada")
        axes[1].legend()
        axes[1].grid(True, alpha=0.25)

        axes[2].hist(erro, bins=30, color="#79c36a", alpha=0.85)
        axes[2].axvline(0, color="#d62728", linestyle="--", linewidth=2)
        axes[2].set_xlabel("Erro")
        axes[2].set_ylabel("Frequencia")
        axes[2].set_title("Distribuicao dos erros")
        axes[2].grid(True, alpha=0.25)

        fig.suptitle("Avaliacao do baseline Jacarei (RandomForest)")
        fig.savefig(self.plot_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def _coluna_numerica(df: pd.DataFrame, nome_coluna: str) -> pd.Series:
        if nome_coluna not in df.columns:
            return pd.Series([pd.NA] * len(df), index=df.index, dtype="float64")
        return pd.to_numeric(df[nome_coluna], errors="coerce")

    @staticmethod
    def _coluna_texto(df: pd.DataFrame, nome_coluna: str) -> pd.Series:
        if nome_coluna not in df.columns:
            return pd.Series(["UNKNOWN"] * len(df), index=df.index, dtype="object")
        return df[nome_coluna].fillna("UNKNOWN").astype(str)

    @staticmethod
    def _contar_amenidades(valor: object) -> int:
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return 0

        if isinstance(valor, str):
            texto = valor.strip()
            if not texto:
                return 0
            try:
                itens = json.loads(texto)
            except json.JSONDecodeError:
                return 0
            return len(itens) if isinstance(itens, list) else 0

        if isinstance(valor, list):
            return len(valor)

        return 0