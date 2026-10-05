from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from branca.colormap import LinearColormap

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.geo import CAIXA_LAT, CAIXA_LON, SETORES
from src.pricing.linear_regression import carregar

REPORT = os.path.join("reports", "results", "mapa_setores.md")
HTML = os.path.join("reports", "figures", "mapa_setores_interativo.html")
SEGMENTOS = ("apartamento", "casa")
MIN_ANUNCIOS = 5  # setores com menos anuncios reais ficam em branco


def estatisticas_por_setor() -> tuple[gpd.GeoDataFrame, dict[str, pd.DataFrame]]:
    """R$/m2 mediano de cada setor censitario (IBGE 2022). Usa so anuncios com coordenada REAL:
    a imputada pelo bairro colocaria varios anuncios no mesmo ponto e distorceria a contagem por setor."""
    setores = gpd.read_file(SETORES)
    stats, dados = {}, {}
    for seg in SEGMENTOS:
        df = carregar(seg)
        df = df[df["lat"].between(*CAIXA_LAT) & df["lon"].between(*CAIXA_LON)].copy()
        pontos = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4674")
        j = gpd.sjoin(pontos, setores[["CD_SETOR", "geometry"]], how="left", predicate="within")
        dados[seg] = j
        g = j.groupby("CD_SETOR")["preco_m2"].agg(n="size", mediana="median", p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
        stats[seg] = g
    return setores, stats


def montar_tabela(setores: gpd.GeoDataFrame, stats: dict[str, pd.DataFrame]) -> gpd.GeoDataFrame:
    t = setores.set_index("CD_SETOR")
    for seg, g in stats.items():
        t = t.join(g.add_suffix(f"_{seg}"))
        t[f"n_{seg}"] = t[f"n_{seg}"].fillna(0).astype(int)
        t[f"mediana_{seg}"] = t[f"mediana_{seg}"].where(t[f"n_{seg}"] >= MIN_ANUNCIOS)
    t["anuncios_por_km2"] = (t["n_apartamento"] + t["n_casa"]) / t["AREA_KM2"]
    return t.reset_index()


def figura_estatica(t: gpd.GeoDataFrame) -> str:
    com_dados = t[(t["n_apartamento"] + t["n_casa"]) > 0]
    x0, y0, x1, y1 = com_dados.total_bounds
    fig, eixos = plt.subplots(1, 2, figsize=(15, 6.5))
    for eixo, seg in zip(eixos, SEGMENTOS):
        t.plot(ax=eixo, color="#eeeeee", edgecolor="#cccccc", linewidth=0.3)
        valido = t[t[f"mediana_{seg}"].notna()]
        valido.plot(ax=eixo, column=f"mediana_{seg}", cmap="viridis", edgecolor="white", linewidth=0.3, legend=True,
                    legend_kwds={"label": "mediana de R$/m2", "shrink": 0.7})
        eixo.set_xlim(x0 - 0.01, x1 + 0.01)
        eixo.set_ylim(y0 - 0.01, y1 + 0.01)
        eixo.set_title(f"{seg}: R$/m2 mediano por setor censitario (IBGE 2022)\n{len(valido)} setores com {MIN_ANUNCIOS}+ anuncios com coordenadas reais; cinza = sem dados", fontsize=9)
        eixo.set_aspect("equal")
        eixo.set_axis_off()
    fig.tight_layout()
    return salvar_fig(fig, "geo_mapa_setores.png")


def mapa_interativo(t: gpd.GeoDataFrame) -> str:
    centro = [-23.295, -45.96]
    mapa = folium.Map(location=centro, zoom_start=12, tiles="OpenStreetMap", control_scale=True)
    for seg in SEGMENTOS:
        valido = t[t[f"mediana_{seg}"].notna()].copy()
        cor = LinearColormap(["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"],
                             vmin=float(valido[f"mediana_{seg}"].quantile(0.05)), vmax=float(valido[f"mediana_{seg}"].quantile(0.95)),
                             caption=f"{seg}: mediana de R$/m2 por setor")
        camada = folium.FeatureGroup(name=f"{seg} (R$/m2 por setor)", show=(seg == "apartamento"))
        dados = valido[["CD_SETOR", f"mediana_{seg}", f"n_{seg}", f"p25_{seg}", f"p75_{seg}", "geometry"]].rename(
            columns={f"mediana_{seg}": "mediana", f"n_{seg}": "n", f"p25_{seg}": "p25", f"p75_{seg}": "p75"})
        folium.GeoJson(
            dados.to_json(),
            style_function=lambda f, c=cor: {"fillColor": c(f["properties"]["mediana"]), "color": "white", "weight": 0.5, "fillOpacity": 0.75},
            tooltip=folium.GeoJsonTooltip(fields=["CD_SETOR", "n", "mediana", "p25", "p75"],
                                          aliases=["setor", "anuncios", "R$/m2 mediano", "p25", "p75"], localize=True),
        ).add_to(camada)
        camada.add_to(mapa)
        cor.add_to(mapa)
    folium.LayerControl(collapsed=False).add_to(mapa)
    os.makedirs(os.path.dirname(HTML), exist_ok=True)
    mapa.save(HTML)
    return HTML.replace("\\", "/")


def executar() -> dict:
    setores, stats = estatisticas_por_setor()
    t = montar_tabela(setores, stats)
    saida = t.drop(columns="geometry")
    salvar_tab(saida, "setores_preco.csv")
    fig = figura_estatica(t)
    html = mapa_interativo(t)

    L = ["# Mapa de R$/m2 por setor censitario do IBGE (Jacarei)", "",
         "Gerado por `python main.py mapa-setores`. Nao editar manualmente.", "",
         f"Malha: setores censitarios do Censo 2022 (IBGE), 544 em Jacarei (`{SETORES}`). Cada anuncio **com coordenada real** e associado ao setor "
         f"que o contem; setores com menos de {MIN_ANUNCIOS} anuncios ficam em branco. Os valores sao o **nivel** de preco (snapshot de marco/2026), "
         "nao crescimento: o crescimento por area exige varios snapshots.", "",
         "| Segmento | Anuncios com coordenadas reais | Setores com algum anuncio | Setores com 5+ anuncios | Mediana dos setores (R$/m2) | Min - max das medianas |",
         "|---|---|---|---|---|---|"]
    for seg in SEGMENTOS:
        n = int(t[f"n_{seg}"].sum()); algum = int((t[f"n_{seg}"] > 0).sum()); ok = int(t[f"mediana_{seg}"].notna().sum())
        m = t[f"mediana_{seg}"].dropna()
        L.append(f"| {seg} | {n} | {algum} | {ok} | {m.median():.0f} | {m.min():.0f} - {m.max():.0f} |")
    for seg in SEGMENTOS:
        top = t.dropna(subset=[f"mediana_{seg}"]).sort_values(f"mediana_{seg}", ascending=False)
        cols = ["CD_SETOR", f"n_{seg}", f"mediana_{seg}", "AREA_KM2"]
        L += ["", f"## {seg}: 8 setores mais caros e 8 mais baratos (5+ anuncios)", "",
              md(pd.concat([top.head(8), top.tail(8)])[cols].rename(columns={f"n_{seg}": "anuncios", f"mediana_{seg}": "R$/m2 mediano", "AREA_KM2": "area (km2)"}).round(2), 2)]
    L += ["", "## Arquivos", "", f"- `{fig}`", f"- `{html}` (interativo: abra no navegador; alterna apartamento e casa; passe o mouse sobre um setor)",
          "- `reports/results/eda/setores_preco.csv` (todos os setores, com contagens e quantis)", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
    return {"tabela": t, "figura": fig, "html": html}
