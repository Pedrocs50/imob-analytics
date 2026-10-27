"""Mineracao de dados dos anuncios do VivaReal de Jacarei.

Tres leituras sobre os datasets limpos (`vivareal-prep`), todas descritivas:
  1. associacao entre caracteristicas e R$/m2 (correlacao de Spearman);
  2. grupos de imoveis (K-means) e o R$/m2 tipico de cada grupo;
  3. termos do texto do anuncio associados a preco acima ou abaixo do bairro.

Sao associacoes, nao efeitos causais. Resultados em `reports/results/mineracao.md`.
"""
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = os.path.join("data", "processed", "vivareal")
RESULTS_DIR = os.path.join("reports", "results", "mineracao")
RELATORIO = os.path.join("reports", "results", "mineracao.md")

SEGMENTOS = ("apartamento", "casa")
NUMERICAS = ["usable_area_m2", "total_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces",
             "monthly_condo", "amenities_count"]
ROTULOS = {"usable_area_m2": "area util", "total_area_m2": "area total", "bedrooms": "quartos",
           "bathrooms": "banheiros", "suites": "suites", "parking_spaces": "vagas",
           "monthly_condo": "condominio (R$)", "amenities_count": "no de comodidades"}
FEATURES_GRUPO = ["usable_area_m2", "bedrooms", "suites", "parking_spaces"]
N_GRUPOS = 4
MIN_ANUNCIOS_TERMO = 150  # termo precisa aparecer em pelo menos isto para entrar na leitura
TOP_TERMOS = 12


def _carregar(segmento: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(PROCESSED_DIR, f"{segmento}.csv"))
    df = df[df["preco_m2"].between(df["preco_m2"].quantile(0.01), df["preco_m2"].quantile(0.99))]
    return df.reset_index(drop=True)


def associacao(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for col in NUMERICAS:
        sub = df[[col, "preco_m2"]].dropna()
        if len(sub) < 100 or sub[col].nunique() < 3:
            continue
        linhas.append({"caracteristica": ROTULOS[col], "n": len(sub),
                       "spearman com R$/m2": sub[col].corr(sub["preco_m2"], method="spearman")})
    return pd.DataFrame(linhas).sort_values("spearman com R$/m2", key=abs, ascending=False)


def grupos(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=FEATURES_GRUPO).copy()
    x = base[FEATURES_GRUPO].copy()
    x["usable_area_m2"] = np.log1p(x["usable_area_m2"])
    x = StandardScaler().fit_transform(x)
    base["grupo"] = KMeans(n_clusters=N_GRUPOS, n_init=10, random_state=0).fit_predict(x)
    tabela = base.groupby("grupo").agg(
        anuncios=("preco_m2", "size"),
        area_mediana=("usable_area_m2", "median"),
        quartos=("bedrooms", "median"),
        suites=("suites", "median"),
        vagas=("parking_spaces", "median"),
        preco_m2_mediano=("preco_m2", "median"),
        preco_mediano=("sale_price", "median"),
    )
    return tabela.sort_values("area_mediana").reset_index(drop=True).rename_axis("grupo").reset_index()


def termos(df: pd.DataFrame) -> pd.DataFrame:
    """Efeito de cada termo = mediana de (R$/m2 do anuncio / mediana do bairro) com o termo menos sem o termo.
    Dividir pelo bairro tira o efeito 'esse termo aparece em bairro caro'."""
    base = df.dropna(subset=["neighborhood"]).copy()
    base["rel_bairro"] = base["preco_m2"] / base.groupby("neighborhood")["preco_m2"].transform("median")
    linhas = []
    for col in [c for c in base.columns if c.startswith("txt_")]:
        tem = base[col] > 0
        if tem.sum() < MIN_ANUNCIOS_TERMO or (~tem).sum() < MIN_ANUNCIOS_TERMO:
            continue
        linhas.append({"termo": col.removeprefix("txt_").replace("_", " "), "anuncios com o termo": int(tem.sum()),
                       "efeito vs bairro (%)": (base.loc[tem, "rel_bairro"].median()
                                                - base.loc[~tem, "rel_bairro"].median()) * 100})
    return pd.DataFrame(linhas).sort_values("efeito vs bairro (%)", ascending=False)


def _md(df: pd.DataFrame, casas: int = 2) -> str:
    cab = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    corpo = "".join("| " + " | ".join(f"{v:.{casas}f}" if isinstance(v, float) else str(v) for v in lin) + " |\n"
                    for lin in df.itertuples(index=False))
    return cab + corpo


def executar() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    saida = ["# Mineracao de dados dos anuncios (VivaReal, Jacarei)\n",
             "Gerado por `python main.py mineracao`. Leituras descritivas: sao **associacoes, nao efeitos causais**. "
             "Anuncios com R$/m2 fora do intervalo 1%-99% foram retirados.\n"]
    for segmento in SEGMENTOS:
        df = _carregar(segmento)
        assoc, grp, trm = associacao(df), grupos(df), termos(df)
        for nome, tab in (("associacao", assoc), ("grupos", grp), ("termos", trm)):
            tab.to_csv(os.path.join(RESULTS_DIR, f"{segmento}_{nome}.csv"), index=False)
        saida.append(f"\n## {segmento.capitalize()} ({len(df)} anuncios)\n")
        saida.append("\n### 1. Associacao com o R$/m2 (Spearman)\n\n" + _md(assoc))
        saida.append(f"\n### 2. Grupos de imoveis (K-means, k={N_GRUPOS}, por area, quartos, suites e vagas)\n\n" + _md(grp, 1))
        saida.append(f"\n### 3. Termos do anuncio: maior e menor efeito sobre o preco relativo ao bairro "
                     f"(termos em {MIN_ANUNCIOS_TERMO}+ anuncios)\n\n**Associados a preco acima do bairro**\n\n"
                     + _md(trm.head(TOP_TERMOS), 1)
                     + "\n**Associados a preco abaixo do bairro**\n\n" + _md(trm.tail(TOP_TERMOS).iloc[::-1], 1))
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("".join(saida))
    print(f"[MINERACAO] relatorio em {RELATORIO}; tabelas em {RESULTS_DIR}")
