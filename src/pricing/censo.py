from __future__ import annotations

import os
import zipfile

import pandas as pd

ORIGINAIS = os.path.join("data", "raw", "ibge", "censo2022_originais")
JACAREI_CSV = os.path.join("data", "raw", "ibge", "jacarei_censo2022_setores.csv")
COD_MUNICIPIO = "3524402"

# colunas do Censo 2022 usadas (ver os dicionarios em data/raw/ibge/censo2022_originais/)
BASICO = {"v0001": "pessoas", "v0002": "domicilios", "v0005": "moradores_por_domicilio_ocupado",
          "v0007": "domicilios_ocupados", "v0008": "domicilios_uso_ocasional", "v0009": "domicilios_vagos"}
RENDA = {"V06001": "responsaveis", "V06004": "renda_responsavel_media", "V06006": "renda_responsavel_mediana"}

# variaveis derivadas que entram nos modelos
FEATURES_CENSO = ["renda_responsavel_media", "renda_responsavel_mediana", "densidade_hab_km2", "densidade_domicilios_km2",
                  "moradores_por_domicilio", "pct_domicilios_vagos", "pessoas"]


def _numerico(serie: pd.Series) -> pd.Series:
    """O IBGE usa virgula decimal em alguns arquivos, ponto em outros, e '.', 'X' ou vazio para dado ausente/sigiloso."""
    return pd.to_numeric(serie.astype("string").str.strip().str.replace(",", ".", regex=False), errors="coerce")


def extrair_jacarei() -> pd.DataFrame:
    """Recorta Jacarei dos arquivos nacionais do Censo 2022 (agregados por setor) e grava um CSV pequeno."""
    def ler(zip_nome: str, csv_nome: str) -> pd.DataFrame:
        with zipfile.ZipFile(os.path.join(ORIGINAIS, zip_nome)) as zf, zf.open(csv_nome) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str, low_memory=False)
        return df[df["CD_SETOR"].str.startswith(COD_MUNICIPIO)]

    basico = ler("basico.zip", "Agregados_por_setores_basico_BR.csv")
    renda = ler("renda.zip", "Agregados_por_setores_renda_responsavel_BR.csv")
    b = basico[["CD_SETOR", "SITUACAO", "AREA_KM2", *BASICO]].rename(columns=BASICO).copy()
    r = renda[["CD_SETOR", *RENDA]].rename(columns=RENDA)
    out = b.merge(r, on="CD_SETOR", how="left")
    for c in out.columns.difference(["CD_SETOR", "SITUACAO"]):
        out[c] = _numerico(out[c])
    os.makedirs(os.path.dirname(JACAREI_CSV), exist_ok=True)
    out.to_csv(JACAREI_CSV, index=False, encoding="utf-8")
    return out


def carregar_censo() -> pd.DataFrame:
    """Variaveis do Censo 2022 por setor de Jacarei, indexadas por CD_SETOR."""
    df = pd.read_csv(JACAREI_CSV, dtype={"CD_SETOR": str}) if os.path.exists(JACAREI_CSV) else extrair_jacarei()
    df["CD_SETOR"] = df["CD_SETOR"].astype(str)
    area = df["AREA_KM2"].where(df["AREA_KM2"] > 0)
    df["densidade_hab_km2"] = df["pessoas"] / area
    df["densidade_domicilios_km2"] = df["domicilios"] / area
    df["moradores_por_domicilio"] = df["moradores_por_domicilio_ocupado"]
    df["pct_domicilios_vagos"] = (df["domicilios_vagos"] + df["domicilios_uso_ocasional"]) / df["domicilios"].where(df["domicilios"] > 0) * 100
    return df.set_index("CD_SETOR")[["SITUACAO", "AREA_KM2", *FEATURES_CENSO]]
