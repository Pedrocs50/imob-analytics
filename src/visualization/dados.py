"""Leitura dos resultados ja gerados. Cada funcao devolve None se a fonte nao existe (o painel mostra um aviso no lugar)."""
from __future__ import annotations

import json
import os
from functools import lru_cache

import pandas as pd

EDA = os.path.join("reports", "results", "eda")
ARIMA = os.path.join("reports", "results", "arima")
LSTM = os.path.join("reports", "results", "lstm")
VIVAREAL = os.path.join("data", "processed", "vivareal")
SERIES = os.path.join("data", "processed", "series")
SETORES_GPKG = os.path.join("data", "raw", "ibge", "jacarei_setores_2022.gpkg")
SEGMENTOS = ("apartamento", "casa")

# nome do arquivo e comando que o gera (para a mensagem de aviso)
GERADO_POR = {
    "setores_preco.csv": "mapa-setores", "modelos_avancados_metricas.csv": "modelos-avancados",
    "modelos_avancados_intervalos.csv": "modelos-avancados", "regressao_geo_metricas.csv": "reg-geo",
    "projecao_por_setor.csv": "projecao", "projecao_cenarios_tendencia.csv": "projecao",
    "sens_grupos.csv": "sensibilidade", "sens_cenarios.csv": "sensibilidade", "sens_curvas.csv": "sensibilidade",
    "sens_bairros.csv": "sensibilidade", "projecao_anuncios.csv": "projecao",
}


def comando_de(caminho: str) -> str:
    return "python main.py " + GERADO_POR.get(os.path.basename(caminho), "...")


@lru_cache(maxsize=None)
def csv(caminho: str) -> pd.DataFrame | None:
    return pd.read_csv(caminho) if os.path.exists(caminho) else None


def eda(nome: str) -> pd.DataFrame | None:
    return csv(os.path.join(EDA, nome))


def anuncios(segmento: str) -> pd.DataFrame | None:
    return csv(os.path.join(VIVAREAL, f"{segmento}.csv"))


def projecao_anuncios() -> pd.DataFrame | None:
    return csv(os.path.join(VIVAREAL, "projecao_anuncios.csv"))


def painel_series() -> pd.DataFrame | None:
    d = csv(os.path.join(SERIES, "painel_mensal_referencia.csv"))
    if d is None:
        return None
    d = d.copy()
    d["data_ref"] = pd.to_datetime(d["data_ref"])
    return d


@lru_cache(maxsize=None)
def setores_geojson() -> dict | None:
    """Setores censitarios de Jacarei (544) como GeoJSON simplificado (~30 m) e com coordenadas de ~1 m, para o mapa; id = CD_SETOR.
    O arquivo vai repetido em cada traco do mapa, entao o tamanho importa."""
    if not os.path.exists(SETORES_GPKG):
        return None
    import geopandas as gpd
    import shapely

    g = gpd.read_file(SETORES_GPKG)[["CD_SETOR", "geometry"]].to_crs(4326)
    g["geometry"] = shapely.set_precision(g.geometry.simplify(0.0003, preserve_topology=True).values, 1e-5)
    return json.loads(g.to_json(drop_id=True))


def limites_setores(ids: set[str], margem: float = 0.08) -> tuple[list[float], list[float]] | None:
    """([lon_min, lon_max], [lat_min, lat_max]) dos setores `ids`, com margem; enquadra o mapa na area com dados."""
    geo = setores_geojson()
    if geo is None:
        return None
    pontos: list[tuple[float, float]] = []

    def coletar(c):
        if c and isinstance(c[0], (int, float)):
            pontos.append((c[0], c[1]))
        else:
            for x in c:
                coletar(x)

    for f in geo["features"]:
        if f["properties"]["CD_SETOR"] in ids:
            coletar(f["geometry"]["coordinates"])
    if not pontos:
        return None
    lon, lat = zip(*pontos)
    dx, dy = (max(lon) - min(lon)) * margem, (max(lat) - min(lat)) * margem
    return [min(lon) - dx, max(lon) + dx], [min(lat) - dy, max(lat) + dy]
