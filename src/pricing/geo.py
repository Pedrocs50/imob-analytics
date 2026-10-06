from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy.spatial import cKDTree
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.censo import FEATURES_CENSO, carregar_censo
from src.pricing.linear_regression import MIN_ANUNCIOS_BAIRRO, SEMENTE, _metricas, _variaveis, carregar

REPORT = os.path.join("reports", "results", "regressao_geo.md")
CONTORNO = os.path.join("data", "raw", "ibge", "jacarei_contorno.geojson")
SETORES = os.path.join("data", "raw", "ibge", "jacarei_setores_2022.gpkg")
SEGMENTOS = ("apartamento", "casa", "residencial")
K_VIZINHOS = 15
MIN_ANUNCIOS_SETOR = 15  # setores com menos anuncios viram uma categoria unica
KM_POR_GRAU_LAT = 110.57
KM_POR_GRAU_LON_EQUADOR = 111.32
CAIXA_LAT, CAIXA_LON = (-23.45, -23.15), (-46.20, -45.70)  # so para descartar coordenadas fora do municipio


@dataclass(frozen=True)
class Cfg:
    tipo: str  # "ols" | "gb"
    coords: str = "nenhuma"  # "nenhuma" | "reais" | "imputadas"
    superficie: bool = False
    vizinhanca: bool = False
    setor: bool = False
    censo: bool = False  # variaveis do Censo 2022 do setor (renda, densidade, domicilios)
    extras: bool = False  # area do terreno e indicadores de palavras do titulo/descricao do anuncio


MODELOS: dict[str, Cfg] = {
    "OLS base (sem coordenadas)": Cfg("ols"),
    "OLS + vizinhos (kNN, so coord. reais)": Cfg("ols", "reais", vizinhanca=True),
    "OLS + vizinhos (coord. imputadas)": Cfg("ols", "imputadas", vizinhanca=True),
    "Gradient boosting sem coordenadas": Cfg("gb"),
    "Gradient boosting com lat/lon reais": Cfg("gb", "reais"),
    "Gradient boosting com lat/lon imputadas": Cfg("gb", "imputadas"),
    "Gradient boosting + setor IBGE": Cfg("gb", "imputadas", setor=True),
    "Gradient boosting imputadas + vizinhos": Cfg("gb", "imputadas", vizinhanca=True),
    "Gradient boosting imputadas + vizinhos + setor": Cfg("gb", "imputadas", vizinhanca=True, setor=True),
    "OLS + vizinhos + Censo": Cfg("ols", "imputadas", vizinhanca=True, censo=True),
    "Gradient boosting + Censo": Cfg("gb", "imputadas", censo=True),
    "Gradient boosting imputadas + vizinhos + Censo": Cfg("gb", "imputadas", vizinhanca=True, censo=True),
    "Gradient boosting imputadas + vizinhos + setor + Censo": Cfg("gb", "imputadas", vizinhanca=True, setor=True, censo=True),
    "GB completo + terreno e texto (sem vizinhos)": Cfg("gb", "imputadas", setor=True, censo=True, extras=True),
    "GB completo + terreno e texto": Cfg("gb", "imputadas", vizinhanca=True, setor=True, censo=True, extras=True),
}


# ----------------------------------------------------------------------------- imputacao e setor
def imputar_coordenadas(df: pd.DataFrame) -> pd.DataFrame:
    """Preenche lat/lon ausentes usando SO coordenadas (nunca o preco, entao nao ha vazamento do alvo):
    1) mediana das coordenadas reais da mesma rua no mesmo bairro (>= 2 anuncios), 2) mediana do bairro
    (>= 3 anuncios). Dispersao tipica das coordenadas reais: ~0,07 km dentro da rua e ~0,34 km dentro do bairro.
    Retorna lat_i, lon_i e coord_origem (0 real, 1 rua, 2 bairro, -1 sem informacao)."""
    lat, lon = df["lat"], df["lon"]
    real = lat.between(*CAIXA_LAT) & lon.between(*CAIXA_LON)
    ref = df[real]

    rua = ref.dropna(subset=["street"]).groupby(["neighborhood", "street"]).agg(lat_rua=("lat", "median"), lon_rua=("lon", "median"), n=("lat", "size"))
    rua = rua[rua["n"] >= 2].drop(columns="n")
    bairro = ref.groupby("neighborhood").agg(lat_b=("lat", "median"), lon_b=("lon", "median"), n=("lat", "size"))
    bairro = bairro[bairro["n"] >= 3].drop(columns="n")

    m_rua = df[["neighborhood", "street"]].merge(rua, left_on=["neighborhood", "street"], right_index=True, how="left")
    m_b = df[["neighborhood"]].merge(bairro, left_on="neighborhood", right_index=True, how="left")
    lat_i, lon_i = lat.where(real).copy(), lon.where(real).copy()
    origem = pd.Series(np.where(real, 0, -1), index=df.index)
    for lat_c, lon_c, cod in ((m_rua["lat_rua"], m_rua["lon_rua"], 1), (m_b["lat_b"], m_b["lon_b"], 2)):
        livre = lat_i.isna() & lat_c.notna()
        lat_i[livre], lon_i[livre], origem[livre] = lat_c[livre], lon_c[livre], cod
    return pd.DataFrame({"lat_i": lat_i, "lon_i": lon_i, "coord_origem": origem})


def atribuir_setor(lat: pd.Series, lon: pd.Series) -> pd.Series:
    """Setor censitario (IBGE, Censo 2022) de cada ponto, por juncao espacial."""
    import geopandas as gpd

    setores = gpd.read_file(SETORES)[["CD_SETOR", "geometry"]]
    ok = lat.notna() & lon.notna()
    pontos = gpd.GeoDataFrame({"i": lat.index[ok]}, geometry=gpd.points_from_xy(lon[ok], lat[ok]), crs="EPSG:4674")
    juncao = gpd.sjoin(pontos, setores, how="left", predicate="within").drop_duplicates("i").set_index("i")
    return juncao["CD_SETOR"].reindex(lat.index)


# ----------------------------------------------------------------------------- features geograficas
class GeoVizinhanca(BaseEstimator, TransformerMixin):
    """Features geograficas sem vazamento. Recebe colunas [lat, lon, bairro] e, opcionalmente, [lat_i, lon_i].

    - superficie: x, y, x^2, y^2, x*y (km a partir do centro, padronizados);
    - vizinhanca: mediana do alvo dos k anuncios REAIS mais proximos e distancia media a eles. No treino cada
      anuncio fica de fora do proprio calculo (leave-one-out); no teste so os anuncios do treino contam. Anuncios
      sem coordenada real mas com coordenada imputada (lat_i/lon_i) consultam a posicao imputada.
    Sem nenhuma coordenada, a mediana do bairro (no treino) substitui a vizinhanca."""

    def __init__(self, superficie: bool = True, vizinhanca: bool = True, k: int = K_VIZINHOS):
        self.superficie = superficie
        self.vizinhanca = vizinhanca
        self.k = k

    def _projetar(self, lat, lon):
        y = (lat - self.lat0_) * KM_POR_GRAU_LAT
        x = (lon - self.lon0_) * KM_POR_GRAU_LON_EQUADOR * np.cos(np.radians(self.lat0_))
        return np.column_stack([x, y])

    @staticmethod
    def _como_df(X) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            return X
        cols = ["lat", "lon", "bairro", "lat_i", "lon_i"][: X.shape[1]]
        return pd.DataFrame(X, columns=cols)

    def fit(self, X, y=None):
        X = self._como_df(X)
        lat, lon = pd.to_numeric(X["lat"]).to_numpy(float), pd.to_numeric(X["lon"]).to_numpy(float)
        valido = ~(np.isnan(lat) | np.isnan(lon))
        self.lat0_, self.lon0_ = float(np.nanmean(lat)), float(np.nanmean(lon))
        xy = self._projetar(lat[valido], lon[valido])
        self.escala_ = xy.std(axis=0)
        self.y_valido_ = np.asarray(y, float)[valido] if y is not None else None
        self.arvore_ = cKDTree(xy)
        self.n_ref_ = int(valido.sum())
        if y is not None:
            serie = pd.Series(np.asarray(y, float), index=X["bairro"].to_numpy())
            self.mediana_bairro_ = serie.groupby(level=0).median()
            self.mediana_geral_ = float(np.median(y))
        return self

    def _features(self, X: pd.DataFrame, loo: bool) -> np.ndarray:
        n = len(X)
        lat, lon = pd.to_numeric(X["lat"]).to_numpy(float), pd.to_numeric(X["lon"]).to_numpy(float)
        real = ~(np.isnan(lat) | np.isnan(lon))
        if "lat_i" in X.columns:
            lat_q = np.where(real, lat, pd.to_numeric(X["lat_i"]).to_numpy(float))
            lon_q = np.where(real, lon, pd.to_numeric(X["lon_i"]).to_numpy(float))
        else:
            lat_q, lon_q = lat, lon
        consulta = ~(np.isnan(lat_q) | np.isnan(lon_q))
        xy = np.zeros((n, 2))
        xy[consulta] = self._projetar(lat_q[consulta], lon_q[consulta])
        colunas = [real.astype(float)]  # tem_coord_real

        if self.superficie:
            z = np.where(consulta[:, None], xy / self.escala_, 0.0)
            colunas += [z[:, 0], z[:, 1], z[:, 0] ** 2 * consulta, z[:, 1] ** 2 * consulta, z[:, 0] * z[:, 1] * consulta]

        if self.vizinhanca:
            k = self.k + 1 if loo else self.k
            viz_preco = np.array(X["bairro"].map(self.mediana_bairro_).fillna(self.mediana_geral_), dtype=float)
            viz_dist = np.full(n, np.nan)
            if consulta.any():
                pos = np.flatnonzero(consulta)
                dist, idx = self.arvore_.query(xy[consulta], k=min(k, self.n_ref_))
                if loo:
                    # posicao de cada anuncio real dentro da arvore (so os reais sao pontos de referencia)
                    pos_arvore = np.cumsum(real) - 1
                    novos_idx, novas_dist = [], []
                    for linha, (d, ix) in enumerate(zip(dist, idx)):
                        proprio = pos_arvore[pos[linha]] if real[pos[linha]] else -1
                        manter = ix != proprio
                        if manter.all():
                            manter[-1] = False
                        novos_idx.append(ix[manter][: self.k])
                        novas_dist.append(d[manter][: self.k])
                    idx, dist = np.array(novos_idx), np.array(novas_dist)
                viz_preco[pos] = np.median(self.y_valido_[idx], axis=1)
                viz_dist[pos] = dist.mean(axis=1)
            if not hasattr(self, "dist_mediana_"):
                self.dist_mediana_ = float(np.nanmedian(viz_dist)) if np.isfinite(viz_dist).any() else 0.0
            colunas += [viz_preco, np.where(np.isnan(viz_dist), self.dist_mediana_, viz_dist)]
        return np.column_stack(colunas)

    def fit_transform(self, X, y=None, **kwargs):
        X = self._como_df(X)
        self.fit(X, y)
        return self._features(X, loo=True)

    def transform(self, X):
        return self._features(self._como_df(X), loo=False)

    def get_feature_names_out(self, input_features=None):
        nomes = ["tem_coord_real"]
        if self.superficie:
            nomes += ["geo_x", "geo_y", "geo_x2", "geo_y2", "geo_xy"]
        if self.vizinhanca:
            nomes += ["viz_preco_mediana", "viz_dist_km"]
        return np.array(nomes)


# ----------------------------------------------------------------------------- modelos
def _montar_x(df: pd.DataFrame, segmento: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    x, numericas, categoricas = _variaveis(df, segmento, "+ condominio informado")
    imp = imputar_coordenadas(df)
    real = imp["coord_origem"] == 0
    x["lat"], x["lon"] = df["lat"].where(real), df["lon"].where(real)
    x["lat_i"], x["lon_i"], x["coord_origem"] = imp["lat_i"], imp["lon_i"], imp["coord_origem"]
    setor = atribuir_setor(imp["lat_i"], imp["lon_i"])
    x["setor"] = setor.fillna("sem_setor")
    censo = carregar_censo()
    for c in FEATURES_CENSO:  # NaN onde nao ha setor ou o IBGE nao divulga (sigilo estatistico)
        x[c] = setor.map(censo[c])
    # informacao do anuncio: terreno e palavras do titulo/descricao (sem precos nem numeros)
    extras: list[str] = []
    if "total_area_m2" in df.columns:
        terreno = df["total_area_m2"].where(df["total_area_m2"] > 0)
        x["log_terreno"], x["razao_terreno_construida"] = np.log(terreno), terreno / df["usable_area_m2"]
        extras += ["log_terreno", "razao_terreno_construida"]
    # valor da taxa de condominio (proxy de padrao) e contexto sem preco: tamanho relativo ao bairro, quantos anuncios na rua e no bairro
    # (liquidez/densidade) e distancia ao centro. O IPTU foi testado e nao acrescentou nada (unidade nao confirmada): fica de fora.
    x["valor_condominio"] = df["monthly_condo"]
    x["area_rel_bairro"] = df["usable_area_m2"] / df.groupby("neighborhood")["usable_area_m2"].transform("median")
    x["n_anuncios_rua"] = df.groupby(["neighborhood", "street"])["usable_area_m2"].transform("size").where(df["street"].notna())
    x["n_anuncios_bairro"] = df.groupby("neighborhood")["usable_area_m2"].transform("size")
    x["dist_centro_km"] = np.hypot((imp["lat_i"] - imp["lat_i"].median()) * KM_POR_GRAU_LAT,
                                   (imp["lon_i"] - imp["lon_i"].median()) * KM_POR_GRAU_LON_EQUADOR * np.cos(np.radians(imp["lat_i"].median())))
    extras += ["valor_condominio", "area_rel_bairro", "n_anuncios_rua", "n_anuncios_bairro", "dist_centro_km"]
    texto = [c for c in df.columns if c.startswith("txt_")]
    x[texto] = df[texto]
    x.attrs["extras"] = extras + texto
    return x, numericas, categoricas


def _construir(cfg: Cfg, numericas: list[str], categoricas: list[str], extras: list[str] | None = None):
    numericas = numericas + (FEATURES_CENSO if cfg.censo else []) + ((extras or []) if cfg.extras else [])
    geo_cols = ["lat", "lon", "bairro"] + (["lat_i", "lon_i"] if cfg.coords == "imputadas" else [])
    if cfg.tipo == "ols":
        blocos = [("num", SimpleImputer(strategy="median", add_indicator=True), numericas),
                  ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=MIN_ANUNCIOS_BAIRRO,
                                        drop="first", sparse_output=False), categoricas)]
        if cfg.coords != "nenhuma" and (cfg.superficie or cfg.vizinhanca):
            blocos.append(("geo", GeoVizinhanca(cfg.superficie, cfg.vizinhanca), geo_cols))
        return Pipeline([("prep", ColumnTransformer(blocos)), ("reg", LinearRegression())])

    cats = categoricas + (["setor"] if cfg.setor else [])
    blocos = [("num", "passthrough", numericas),
              ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, min_frequency=MIN_ANUNCIOS_SETOR), cats)]
    cat_idx = list(range(len(numericas), len(numericas) + len(cats)))
    if cfg.coords == "reais":
        blocos.append(("geo", "passthrough", ["lat", "lon"]))
    elif cfg.coords == "imputadas":
        blocos.append(("geo", "passthrough", ["lat_i", "lon_i", "coord_origem"]))
    if cfg.vizinhanca:
        blocos.append(("viz", GeoVizinhanca(superficie=False, vizinhanca=True), geo_cols))
    return Pipeline([("prep", ColumnTransformer(blocos)),
                     ("reg", HistGradientBoostingRegressor(categorical_features=cat_idx, max_iter=300, learning_rate=0.05,
                                                           max_leaf_nodes=15, l2_regularization=1.0, random_state=SEMENTE))])


def avaliar(df: pd.DataFrame, segmento: str) -> tuple[pd.DataFrame, dict]:
    x, num, cat = _montar_x(df, segmento)
    y = df["preco_m2"]
    subconjuntos = {"todos os anuncios": pd.Series(True, index=df.index),
                    "so com coordenadas reais": x["coord_origem"] == 0,
                    "so sem coordenadas reais": x["coord_origem"] != 0}
    linhas, residuos = [], {}

    divisoes = {}
    i_tr, i_te = train_test_split(df.index, test_size=0.2, random_state=SEMENTE)
    divisoes["holdout aleatorio (20%)"] = [(i_tr, i_te)]
    divisoes["5-fold"] = [(df.index[a], df.index[b]) for a, b in KFold(5, shuffle=True, random_state=SEMENTE).split(df)]
    corte = df["created_at"].quantile(0.75)
    divisoes[f"temporal (teste apos {corte:%Y-%m-%d})"] = [(df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte])]

    for nome, cfg in MODELOS.items():
        for validacao, pares in divisoes.items():
            prev = pd.Series(np.nan, index=df.index)
            for tr, te in pares:
                m = _construir(cfg, num, cat, x.attrs.get("extras")).fit(x.loc[tr], y.loc[tr])
                prev.loc[te] = m.predict(x.loc[te])
            avaliados = prev.dropna().index
            for sub, mascara in subconjuntos.items():
                idx = avaliados[mascara.loc[avaliados].to_numpy()]
                linhas.append({"segmento": segmento, "modelo": nome, "validacao": validacao, "subconjunto": sub,
                               "n teste": len(idx), **_metricas(y.loc[idx], prev.loc[idx].to_numpy())})
            if validacao == "holdout aleatorio (20%)":
                residuos[nome] = (y - prev).loc[avaliados]
    return pd.DataFrame(linhas), residuos


# ----------------------------------------------------------------------------- contorno e mapas
def carregar_contorno() -> list[np.ndarray]:
    """Contorno do municipio (API do IBGE, dado publico de ~2 KB), guardado em data/raw/ibge/."""
    if not os.path.exists(CONTORNO):
        os.makedirs(os.path.dirname(CONTORNO), exist_ok=True)
        resp = requests.get("https://servicodados.ibge.gov.br/api/v3/malhas/municipios/3524402",
                            params={"formato": "application/vnd.geo+json", "qualidade": "intermediaria"}, timeout=60)
        resp.raise_for_status()
        with open(CONTORNO, "w", encoding="utf-8") as arquivo:
            arquivo.write(resp.text)
    with open(CONTORNO, encoding="utf-8") as arquivo:
        geo = json.load(arquivo)
    aneis = []
    for feat in geo["features"]:
        g = feat["geometry"]
        poligonos = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        aneis += [np.array(p[0]) for p in poligonos]
    return aneis


def _desenhar_contorno(eixo, aneis, dados: pd.DataFrame | None = None) -> None:
    for a in aneis:
        eixo.plot(a[:, 0], a[:, 1], color="k", lw=0.8)
    if dados is not None and len(dados):
        margem = 0.012
        eixo.set_xlim(dados["lon"].quantile(0.002) - margem, dados["lon"].quantile(0.998) + margem)
        eixo.set_ylim(dados["lat"].quantile(0.002) - margem, dados["lat"].quantile(0.998) + margem)


def mapa_preco(dados: dict[str, pd.DataFrame], aneis) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(14, 6))
    for eixo, nome in zip(eixos, ("apartamento", "casa")):
        d = dados[nome].dropna(subset=["lat", "lon"])
        d = d[d["lat"].between(*CAIXA_LAT) & d["lon"].between(*CAIXA_LON)]
        hb = eixo.hexbin(d["lon"], d["lat"], C=d["preco_m2"], reduce_C_function=np.median, gridsize=38, mincnt=5,
                         cmap="viridis", vmin=d["preco_m2"].quantile(0.05), vmax=d["preco_m2"].quantile(0.95))
        _desenhar_contorno(eixo, aneis, d)
        eixo.set_title(f"{nome}: mediana de R$/m2 por celula (minimo 5 anuncios; n = {len(d)})", fontsize=10)
        eixo.set_xlabel("longitude"); eixo.set_ylabel("latitude"); eixo.set_aspect("equal")
        fig.colorbar(hb, ax=eixo, shrink=0.75, label="R$/m2")
    fig.tight_layout()
    return salvar_fig(fig, "geo_mapa_preco_m2.png")


def mapa_residuos(dados: dict[str, pd.DataFrame], residuos: dict[str, dict], aneis) -> str:
    fig, eixos = plt.subplots(2, 2, figsize=(13, 11))
    for linha, nome in enumerate(("apartamento", "casa")):
        for col, modelo in enumerate(("OLS base (sem coordenadas)", "Gradient boosting imputadas + vizinhos + setor")):
            eixo = eixos[linha, col]
            d = dados[nome].assign(res=residuos[nome][modelo]).dropna(subset=["lat", "lon", "res"])
            d = d[d["lat"].between(*CAIXA_LAT) & d["lon"].between(*CAIXA_LON)]
            hb = eixo.hexbin(d["lon"], d["lat"], C=d["res"], reduce_C_function=np.mean, gridsize=30, mincnt=4,
                             cmap="RdBu_r", vmin=-1500, vmax=1500)
            _desenhar_contorno(eixo, aneis, d)
            eixo.set_title(f"{nome}: residuo medio ({modelo})", fontsize=9)
            eixo.set_aspect("equal")
            fig.colorbar(hb, ax=eixo, shrink=0.7, label="real - previsto (R$/m2)")
    fig.tight_layout()
    return salvar_fig(fig, "geo_mapa_residuos.png")


# ----------------------------------------------------------------------------- orquestracao
def executar() -> dict:
    warnings.filterwarnings("ignore")
    aneis = carregar_contorno()
    dados = {s: carregar(s) for s in SEGMENTOS}
    metricas, residuos = [], {}
    for segmento, df in dados.items():
        m, r = avaliar(df, segmento)
        metricas.append(m)
        residuos[segmento] = r
        origem = imputar_coordenadas(df)["coord_origem"].value_counts().to_dict()
        print(f"[GEO] {segmento}: {len(df)} anuncios; origem da coordenada (0 real, 1 rua, 2 bairro, -1 nenhuma): {origem}")
    tab = pd.concat(metricas, ignore_index=True)
    salvar_tab(tab, "regressao_geo_metricas.csv")
    figuras = [mapa_preco(dados, aneis), mapa_residuos(dados, residuos, aneis)]
    escrever_relatorio(tab, dados, figuras)
    return {"metricas": tab, "figuras": figuras}


def escrever_relatorio(tab: pd.DataFrame, dados: dict[str, pd.DataFrame], figuras: list[str]) -> None:
    L = ["# Modelos com latitude, longitude e setores do IBGE (VivaReal)", "",
         "Gerado por `python main.py reg-geo`. Nao editar manualmente.", "",
         "Mesmas variaveis do modelo linear (`docs/MODELOS_PRECIFICACAO.md`, variante `+ condominio informado`) mais informacao "
         "geografica. **So ~48% dos anuncios tem coordenadas reais.** Para os demais as coordenadas sao **imputadas** usando so "
         "coordenadas (sem usar o preco): mediana da rua dentro do bairro (>= 2 anuncios com coordenada real) e, na falta, a mediana do "
         "bairro (>= 3). O indicador `coord_origem` (0 real, 1 rua, 2 bairro) entra nos modelos.", "",
         f"- **Vizinhos (kNN):** mediana do R$/m2 dos {K_VIZINHOS} anuncios **reais** mais proximos e distancia media, sem vazamento "
         "(cada anuncio fica fora do proprio calculo; no teste so o treino conta).",
         "- **Setor IBGE:** setor censitario 2022 (544 em Jacarei) de cada anuncio, por juncao espacial, como categoria (setores "
         f"com menos de {MIN_ANUNCIOS_SETOR} anuncios viram uma so).",
         "- **Gradient boosting:** arvores usam as coordenadas e categorias nativamente.", "",
         "Validacoes: holdout aleatorio de 20%, 5-fold e divisao temporal (teste nos 25% mais recentes). Cada modelo e avaliado em "
         "**todos os anuncios**, **so nos com coordenadas reais** e **so nos sem coordenadas reais** (onde a imputacao importa).", ""]
    for segmento in SEGMENTOS:
        t = tab[tab["segmento"] == segmento]
        n_real = int(dados[segmento]["lat"].between(*CAIXA_LAT).sum())
        L += [f"## {segmento} ({len(dados[segmento])} anuncios; {n_real} com coordenadas reais)", ""]
        for sub in ("todos os anuncios", "so com coordenadas reais", "so sem coordenadas reais"):
            pv = t[t["subconjunto"] == sub].copy()
            pv["validacao"] = pv["validacao"].str.replace(r"temporal.*", "temporal", regex=True).str.replace("holdout aleatorio (20%)", "holdout", regex=False)
            piv = pv.pivot_table(index="modelo", columns="validacao", values="R2", sort=False)
            piv["MAE temporal (R$/m2)"] = pv[pv["validacao"] == "temporal"].set_index("modelo")["MAE"]
            n_t = int(pv[pv["validacao"] == "temporal"]["n teste"].iloc[0])
            L += [f"### R2 e MAE, {sub} (n teste temporal = {n_t})", "", md(piv.reset_index().round(3), 3), ""]
    L += ["## Figuras", ""] + [f"- `{f}`" for f in figuras]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
