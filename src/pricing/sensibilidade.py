"""Meta 7: sensibilidade e relevancia das variaveis do modelo final de precificacao (conjunto LightGBM + HistGradientBoosting).

Tres leituras complementares:
1. relevancia por GRUPO de variaveis (permutacao no teste temporal: quanto o erro sobe quando o grupo e embaralhado);
2. sensibilidade "e se?": efeito medio de mudar uma caracteristica do imovel (area, suite, vaga, terreno, condominio...) mantendo o resto;
3. efeito do bairro e curvas de preco para um imovel de referencia.
"""
from __future__ import annotations

import os
import time
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.censo import FEATURES_CENSO
from src.pricing.geo import _montar_x
from src.pricing.linear_regression import SEMENTE, carregar
from src.pricing.modelos_avancados import ajustar_e_prever, construir, matrizes, preparar
from src.pricing.projecao import MODELOS, carregar_params

REPORT = os.path.join("reports", "results", "sensibilidade.md")
SEGMENTOS = ("apartamento", "casa")
REPETICOES = 5
MIN_ANUNCIOS_BAIRRO = 30


def grupos(x: pd.DataFrame) -> dict[str, list[str]]:
    """Colunas de X por grupo de informacao (so as que existem no segmento)."""
    extras = x.attrs.get("extras", [])
    g = {
        "Tamanho (area util)": ["log_area"],
        "Comodos e vagas": ["quartos", "banheiros", "suites", "vagas", "comodidades"],
        "Terreno (casas)": ["log_terreno", "razao_terreno_construida"],
        "Condominio (taxa e tipo)": ["em_condominio", "condominio_informado", "valor_condominio", "tipo"],
        "Localizacao fina (coordenadas e vizinhos)": ["lat", "lon", "lat_i", "lon_i", "coord_origem"],
        "Bairro": ["bairro"],
        "Setor e Censo 2022": ["setor"] + FEATURES_CENSO,
        "Contexto (tamanho relativo, anuncios, centro)": ["area_rel_bairro", "n_anuncios_rua", "n_anuncios_bairro", "dist_centro_km"],
        "Texto do anuncio": [c for c in extras if c.startswith("txt_")],
    }
    return {k: [c for c in v if c in x.columns] for k, v in g.items() if any(c in x.columns for c in v)}


class Conjunto:
    """Preprocessamento + modelos ajustados num conjunto de treino; preve a partir de um X (DataFrame)."""

    def __init__(self, x: pd.DataFrame, y: pd.Series, treino, prep, cat_idx, params: dict):
        self.prep = clone(prep)
        Xa = np.asarray(self.prep.fit_transform(x.loc[treino], y.loc[treino]), dtype=float)
        self.cat_idx = cat_idx
        self.modelos = []
        for nome in MODELOS:
            m, _ = construir(nome, None, params[nome], cat_idx)
            ajustar_e_prever(nome, m, Xa, y.loc[treino].to_numpy(), Xa[:2], cat_idx)  # ajusta (a previsao das 2 linhas e descartada)
            self.modelos.append(m)

    def prever(self, x: pd.DataFrame) -> np.ndarray:
        X = np.asarray(self.prep.transform(x), dtype=float)
        return np.mean([m.predict(X) for m in self.modelos], axis=0)


# ----------------------------------------------------------------------------- 1. relevancia por grupo
def relevancia(df: pd.DataFrame, segmento: str, params: dict) -> pd.DataFrame:
    x, prep, cat_idx = preparar(df, segmento)
    y = df["preco_m2"]
    corte = df["created_at"].quantile(0.75)
    tr, te = df.index[df["created_at"] <= corte], df.index[df["created_at"] > corte]
    modelo = Conjunto(x, y, tr, prep, cat_idx, params)
    xt, yt = x.loc[te], y.loc[te].to_numpy()
    base = float(np.mean(np.abs(yt - modelo.prever(xt))))
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for nome, cols in grupos(x).items():
        aumentos = []
        for _ in range(REPETICOES):
            emb = xt.copy()
            emb[cols] = xt[cols].iloc[rng.permutation(len(xt))].to_numpy()  # o grupo inteiro e embaralhado junto
            aumentos.append(float(np.mean(np.abs(yt - modelo.prever(emb)))) - base)
        linhas.append({"segmento": segmento, "grupo": nome, "colunas": len(cols), "aumento do MAE (R$/m2)": np.mean(aumentos),
                       "desvio": np.std(aumentos), "aumento relativo (%)": np.mean(aumentos) / base * 100})
    out = pd.DataFrame(linhas).sort_values("aumento do MAE (R$/m2)", ascending=False)
    out.attrs["mae_base"] = base
    return out


# ----------------------------------------------------------------------------- 2. cenarios "e se?"
def _cenarios(df: pd.DataFrame, segmento: str) -> list[tuple[str, callable, pd.Series]]:
    """(nome, funcao que altera uma copia do df, linhas em que a alteracao se aplica)."""
    def mais(col, v):
        def f(d):
            d[col] = d[col] + v
        return f

    def area_pct(p):
        def f(d):
            d["usable_area_m2"] = d["usable_area_m2"] * (1 + p)
        return f

    todos = pd.Series(True, index=df.index)
    c = [("+10% de area util", area_pct(0.10), todos), ("+1 suite", mais("suites", 1), df["suites"].notna()),
         ("+1 vaga", mais("parking_spaces", 1), df["parking_spaces"].notna()), ("+1 quarto", mais("bedrooms", 1), df["bedrooms"].notna()),
         ("+1 banheiro", mais("bathrooms", 1), df["bathrooms"].notna())]
    if segmento == "casa":
        terreno = df["total_area_m2"].gt(0)
        c.append(("+50 m2 de terreno", mais("total_area_m2", 50), terreno))
        def cond(d):
            d["em_condominio"], d["property_type"] = 1, "CONDOMINIUM"
        c.append(("casa passa a ser em condominio", cond, df["em_condominio"] == 0))
    else:
        c.append(("+R$ 100 na taxa de condominio", mais("monthly_condo", 100), df["monthly_condo"].gt(0)))
    return c


def cenarios(df: pd.DataFrame, segmento: str, params: dict) -> pd.DataFrame:
    x, prep, cat_idx = preparar(df, segmento)
    y = df["preco_m2"]
    modelo = Conjunto(x, y, df.index, prep, cat_idx, params)
    atual = modelo.prever(x)
    linhas = []
    for nome, alterar, aplica in _cenarios(df, segmento):
        d = df.copy()
        alterar(d)
        xm, _, _ = _montar_x(d, segmento)
        novo = modelo.prever(xm)
        a0, a1 = df["usable_area_m2"].to_numpy(), d["usable_area_m2"].to_numpy()
        m = aplica.to_numpy()
        pct = (novo / atual - 1)[m]
        total = (novo * a1 - atual * a0)[m]
        linhas.append({"segmento": segmento, "cenario": nome, "imoveis": int(m.sum()), "variacao mediana do R$/m2 (%)": float(np.median(pct) * 100),
                       "q25 (%)": float(np.quantile(pct, 0.25) * 100), "q75 (%)": float(np.quantile(pct, 0.75) * 100),
                       "variacao mediana do preco total (R$)": float(np.median(total))})
    return pd.DataFrame(linhas)


# ----------------------------------------------------------------------------- 3. bairros e curvas
def _referencia(df: pd.DataFrame, segmento: str) -> pd.DataFrame:
    """Um imovel 'tipico' do segmento (medianas); sem coordenadas nem rua, para a localizacao vir so do bairro."""
    r = df.iloc[[0]].copy()
    for c in ("usable_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces", "amenities_count"):
        r[c] = df[c].median()
    r["total_area_m2"] = df["total_area_m2"].where(df["total_area_m2"] > 0).median() if segmento == "casa" else np.nan
    r["monthly_condo"], r["condominio_informado"] = (df["monthly_condo"].median(), 1) if segmento == "apartamento" else (np.nan, 0)
    r["lat"], r["lon"], r["street"] = np.nan, np.nan, np.nan
    txt = [c for c in df.columns if c.startswith("txt_")]
    r[txt] = 0
    if segmento == "casa":
        r["em_condominio"], r["property_type"] = 0, "HOME"
    return r


def _prever_linhas(modelo: Conjunto, df: pd.DataFrame, linhas: pd.DataFrame, segmento: str) -> np.ndarray:
    """Preve linhas sinteticas: elas entram na montagem das variaveis (imputacao de coordenadas, contagens) mas nao no treino."""
    base = pd.concat([df, linhas], ignore_index=True)
    xs, _, _ = _montar_x(base, segmento)
    return modelo.prever(xs.iloc[len(df):])


def curvas_e_bairros(df: pd.DataFrame, segmento: str, params: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    x, prep, cat_idx = preparar(df, segmento)
    modelo = Conjunto(x, df["preco_m2"], df.index, prep, cat_idx, params)
    ref = _referencia(df, segmento)
    bairros = df["neighborhood"].value_counts()
    bairros = bairros[bairros >= MIN_ANUNCIOS_BAIRRO].index
    linhas = pd.concat([ref.assign(neighborhood=b) for b in bairros], ignore_index=True)
    linhas["external_id"] = "REF"
    prev = _prever_linhas(modelo, df, linhas, segmento)
    tab_b = pd.DataFrame({"segmento": segmento, "bairro": bairros, "R$/m2 do imovel de referencia": prev,
                          "anuncios": df["neighborhood"].value_counts()[bairros].to_numpy(),
                          "R$/m2 mediano dos anuncios": df.groupby("neighborhood")["preco_m2"].median()[bairros].to_numpy()})
    tab_b["diferenca para a mediana dos bairros (%)"] = (tab_b["R$/m2 do imovel de referencia"] / tab_b["R$/m2 do imovel de referencia"].median() - 1) * 100
    tab_b = tab_b.sort_values("R$/m2 do imovel de referencia", ascending=False)

    # curva de preco pela area (e por numero de suites), no bairro mais frequente
    b0 = df["neighborhood"].value_counts().index[0]
    a_med = float(df["usable_area_m2"].median())
    areas = np.linspace(max(df["usable_area_m2"].quantile(0.02), 25), df["usable_area_m2"].quantile(0.98), 25)
    curvas = []
    for suites in sorted({0, 1, 2, int(df["suites"].median())}):
        linhas = pd.concat([ref.assign(neighborhood=b0, usable_area_m2=a, suites=suites) for a in areas], ignore_index=True)
        linhas["external_id"] = "REF"
        prev = _prever_linhas(modelo, df, linhas, segmento)
        curvas.append(pd.DataFrame({"segmento": segmento, "bairro": b0, "suites": suites, "area_m2": areas, "R$/m2": prev}))
    return tab_b, pd.concat(curvas, ignore_index=True)


# ----------------------------------------------------------------------------- figuras
def figura_relevancia(rel: pd.DataFrame) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(14, 5), sharex=False)
    for eixo, seg in zip(eixos, SEGMENTOS):
        d = rel[rel["segmento"] == seg].sort_values("aumento do MAE (R$/m2)")
        eixo.barh(d["grupo"], d["aumento do MAE (R$/m2)"], xerr=d["desvio"], color="#1f77b4")
        eixo.set_title(f"{seg}: aumento do erro ao embaralhar o grupo")
        eixo.set_xlabel("aumento do MAE (R$/m2), teste temporal")
        eixo.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "sensibilidade_grupos.png")


def figura_curvas(curvas: pd.DataFrame) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(13, 4.8))
    for eixo, seg in zip(eixos, SEGMENTOS):
        d = curvas[curvas["segmento"] == seg]
        for suites, g in d.groupby("suites"):
            eixo.plot(g["area_m2"], g["R$/m2"], marker="o", ms=3, label=f"{suites} suite(s)")
        eixo.set_title(f"{seg}: R$/m2 pela area (imovel de referencia, {d['bairro'].iloc[0]})", fontsize=10)
        eixo.set_xlabel("area util (m2)")
        eixo.set_ylabel("R$/m2 estimado")
        eixo.grid(alpha=0.3)
        eixo.legend(fontsize=8)
    fig.tight_layout()
    return salvar_fig(fig, "sensibilidade_curvas.png")


def figura_bairros(bairros: pd.DataFrame) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(14, 7))
    for eixo, seg in zip(eixos, SEGMENTOS):
        d = bairros[bairros["segmento"] == seg].head(20).iloc[::-1]
        eixo.barh(d["bairro"], d["R$/m2 do imovel de referencia"], color="#2ca02c")
        eixo.set_title(f"{seg}: 20 bairros mais caros para o mesmo imovel", fontsize=10)
        eixo.set_xlabel("R$/m2 estimado do imovel de referencia")
        eixo.tick_params(axis="y", labelsize=8)
        eixo.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "sensibilidade_bairros.png")


# ----------------------------------------------------------------------------- execucao
def executar() -> dict:
    warnings.filterwarnings("ignore")
    t0 = time.time()
    params = carregar_params()
    rels, cens, bairros, curvas = [], [], [], []
    for seg in SEGMENTOS:
        df = carregar(seg)
        rel = relevancia(df, seg, params[seg])
        rels.append(rel)
        print(f"[SENSIBILIDADE] {seg}: relevancia por grupo (MAE base {rel.attrs['mae_base']:.0f}) {time.time() - t0:.0f}s", flush=True)
        cens.append(cenarios(df, seg, params[seg]))
        b, c = curvas_e_bairros(df, seg, params[seg])
        bairros.append(b)
        curvas.append(c)
        print(f"[SENSIBILIDADE] {seg}: cenarios, bairros e curvas {time.time() - t0:.0f}s", flush=True)
    rel, cen, bai, cur = (pd.concat(v, ignore_index=True) for v in (rels, cens, bairros, curvas))
    for nome, tab in (("sens_grupos.csv", rel), ("sens_cenarios.csv", cen), ("sens_bairros.csv", bai), ("sens_curvas.csv", cur)):
        salvar_tab(tab, nome)
    figuras = [figura_relevancia(rel), figura_curvas(cur), figura_bairros(bai)]
    escrever_relatorio(rel, cen, bai, [r.attrs["mae_base"] for r in rels], figuras, time.time() - t0)
    return {"grupos": rel, "cenarios": cen, "bairros": bai}


def escrever_relatorio(rel, cen, bai, mae_base, figuras, segundos) -> None:
    L = ["# Sensibilidade e relevancia das variaveis (meta 7)", "",
         "Gerado por `python main.py sensibilidade`. Nao editar manualmente. Leitura em `docs/SENSIBILIDADE.md`.", "",
         "Modelo: conjunto LightGBM + HistGradientBoosting com os parametros de `modelos_avancados.md`. "
         f"Relevancia: permutacao do grupo no teste temporal ({REPETICOES} repeticoes). Cenarios e bairros: modelo ajustado em todo o segmento. "
         f"Tempo: {segundos:.0f} s.", ""]
    for seg, mae in zip(SEGMENTOS, mae_base):
        d = rel[rel["segmento"] == seg].drop(columns="segmento")
        L += [f"## Relevancia por grupo: {seg} (MAE do conjunto no teste: R$ {mae:.0f}/m2)", "", md(d.round(2), 2), ""]
    L += ["## Cenarios 'e se?' (efeito medio por imovel, mantendo o resto)", "",
          "Efeito sobre os imoveis do proprio segmento aos quais a mudanca se aplica (as previsoes sao dentro da amostra de treino; o que importa e a diferenca).", "",
          md(cen.round(2), 2), "",
          "## Imovel de referencia por bairro (R$/m2 estimado; bairros com 30+ anuncios)", ""]
    for seg in SEGMENTOS:
        d = bai[bai["segmento"] == seg].drop(columns="segmento")
        L += [f"### {seg}: 10 mais caros e 5 mais baratos", "", md(pd.concat([d.head(10), d.tail(5)]).round(1), 1), ""]
    L += ["## Figuras", ""] + [f"- `{f}`" for f in figuras] + [""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
