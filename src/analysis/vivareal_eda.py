from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.vivareal.config import DEFAULT_OUTPUT_DIR

REPORT = os.path.join("reports", "results", "eda_vivareal.md")
SEGMENTOS = ("apartamento", "casa")  # o residencial e a uniao dos dois
NUMERICAS = ["usable_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces", "yearly_iptu",
             "monthly_condo", "amenities_count", "lat", "lon"]
ROTULO = {"usable_area_m2": "area util", "bedrooms": "quartos", "bathrooms": "banheiros", "suites": "suites",
          "parking_spaces": "vagas", "yearly_iptu": "IPTU anual", "monthly_condo": "condominio", "amenities_count": "n. comodidades",
          "lat": "latitude", "lon": "longitude", "em_condominio": "casa em condominio", "preco_m2": "preco por m2"}
# caixa aproximada de Jacarei, so para detectar coordenadas obviamente fora do municipio
CAIXA_LAT, CAIXA_LON = (-23.45, -23.15), (-46.20, -45.70)
COR = {"apartamento": "#1f5f99", "casa": "#d9822b"}


def carregar(pasta: str = DEFAULT_OUTPUT_DIR) -> dict[str, pd.DataFrame]:
    dados = {}
    for nome in (*SEGMENTOS, "residencial"):
        caminho = os.path.join(pasta, f"{nome}.csv")
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"{caminho} nao existe. Rode antes `python main.py vivareal-prep`.")
        dados[nome] = pd.read_csv(caminho, parse_dates=["created_at", "scraped_at"])
    return dados


# ----------------------------------------------------------------------------- tabelas
def descritiva(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    linhas = []
    for nome, df in d.items():
        pm2 = df["preco_m2"]
        linhas.append({
            "segmento": nome, "n": len(df), "preco_m2 mediana": pm2.median(), "preco_m2 media": pm2.mean(), "desvio": pm2.std(),
            "p5": pm2.quantile(0.05), "p95": pm2.quantile(0.95), "assimetria": stats.skew(pm2), "assimetria do log": stats.skew(np.log(pm2)),
            "preco mediano (R$)": df["sale_price"].median(), "area mediana (m2)": df["usable_area_m2"].median(),
            "quartos (mediana)": df["bedrooms"].median(),
        })
    return pd.DataFrame(linhas)


def faltantes(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    colunas = ["usable_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces", "yearly_iptu", "monthly_condo", "lat", "lon"]
    return pd.DataFrame({nome: (df[colunas].isna().mean() * 100).round(1) for nome, df in d.items()}).rename(index=ROTULO).reset_index(names="variavel (% ausente)")


def por_tipo(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    g = d["residencial"].groupby(["segmento", "property_type"])
    tab = g.agg(n=("preco_m2", "size"), **{"preco_m2 mediana": ("preco_m2", "median"), "area mediana": ("usable_area_m2", "median"),
                                          "preco mediano (R$)": ("sale_price", "median")}).reset_index()
    return tab.sort_values("n", ascending=False)


def correlacao_com_alvo(d: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    linhas, matrizes = [], {}
    for nome in SEGMENTOS:
        df = d[nome].copy()
        cols = NUMERICAS + (["em_condominio"] if nome == "casa" else [])
        matrizes[nome] = df[cols + ["preco_m2"]].rename(columns=ROTULO).corr(method="spearman", min_periods=100)
        for c in cols:
            par = df[[c, "preco_m2"]].dropna()
            if len(par) >= 100 and par[c].nunique() > 1:
                rho = stats.spearmanr(par[c], par["preco_m2"])
                linhas.append({"segmento": nome, "variavel": ROTULO[c], "n": len(par), "Spearman com preco_m2": rho.statistic, "p": rho.pvalue})
    tab = pd.DataFrame(linhas)
    tab["|rho|"] = tab["Spearman com preco_m2"].abs()
    return tab.sort_values(["segmento", "|rho|"], ascending=[True, False]).drop(columns="|rho|"), matrizes


def multicolinearidade(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = ["usable_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces"]
    linhas = []
    for nome in SEGMENTOS:
        x = d[nome][cols].dropna()
        x = x.assign(const=1.0)
        for i, c in enumerate(cols):
            linhas.append({"segmento": nome, "variavel": ROTULO[c], "n": len(x), "VIF": variance_inflation_factor(x.values, i)})
    return pd.DataFrame(linhas)


def bairros(d: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    resumo, topo = [], []
    for nome in SEGMENTOS:
        df = d[nome]
        cont = df["neighborhood"].value_counts()
        grandes = cont[cont >= 30].index
        sub = df[df["neighborhood"].isin(grandes)]
        # eta^2: parcela da variancia de log(preco_m2) explicada pelo bairro (so bairros com n >= 30)
        y = np.log(sub["preco_m2"])
        total = ((y - y.mean()) ** 2).sum()
        entre = sub.assign(y=y).groupby("neighborhood")["y"].apply(lambda s: len(s) * (s.mean() - y.mean()) ** 2).sum()
        resumo.append({"segmento": nome, "bairros": cont.size, "com n >= 30": len(grandes), "com n < 10": int((cont < 10).sum()),
                       "top 5 concentram (%)": cont.head(5).sum() / len(df) * 100,
                       "cobertura dos bairros com n >= 30 (%)": len(sub) / len(df) * 100,
                       "eta2: variancia de log(preco_m2) explicada pelo bairro": entre / total})
        t = (df[df["neighborhood"].isin(cont.head(12).index)].groupby("neighborhood")["preco_m2"].agg(["size", "median"])
             .sort_values("size", ascending=False).reset_index())
        t.insert(0, "segmento", nome)
        topo.append(t.rename(columns={"size": "n", "median": "preco_m2 mediana"}))
    return pd.DataFrame(resumo), pd.concat(topo, ignore_index=True)


def condominio(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    linhas = []
    casa = d["casa"]
    a, b = casa.loc[casa["em_condominio"] == 0, "preco_m2"], casa.loc[casa["em_condominio"] == 1, "preco_m2"]
    u = stats.mannwhitneyu(a, b)
    linhas.append({"analise": "casa fora x dentro de condominio (preco_m2 mediana)", "valor A": a.median(), "valor B": b.median(),
                   "n A": len(a), "n B": len(b), "p (Mann-Whitney)": u.pvalue})
    for grupo, rot in ((0, "fora de condominio"), (1, "em condominio")):
        s = casa.loc[casa["em_condominio"] == grupo, "monthly_condo"]
        linhas.append({"analise": f"casa {rot}: % sem valor de condominio", "valor A": s.isna().mean() * 100,
                       "valor B": np.nan, "n A": len(s), "n B": np.nan, "p (Mann-Whitney)": np.nan})
    for nome in SEGMENTOS:
        df = d[nome]
        com = df[df["monthly_condo"] > 0][["monthly_condo", "preco_m2"]]
        rho = stats.spearmanr(com["monthly_condo"], com["preco_m2"])
        linhas.append({"analise": f"{nome}: Spearman(condominio, preco_m2) entre os que tem taxa > 0", "valor A": rho.statistic,
                       "valor B": np.nan, "n A": len(com), "n B": np.nan, "p (Mann-Whitney)": rho.pvalue})
    return pd.DataFrame(linhas)


def implausiveis(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Variaveis que a limpeza (`vivareal-prep`) nao filtra e que tem valores incoerentes."""
    regras = {"monthly_condo": (50, 5_000, "condominio mensal (R$)"), "yearly_iptu": (50, 30_000, "IPTU anual (R$)")}
    linhas = []
    for nome in SEGMENTOS:
        df = d[nome]
        for col, (baixo, alto, rot) in regras.items():
            s_ = df[col].dropna()
            linhas.append({"segmento": nome, "variavel": rot, "n com valor": len(s_), "mediana": s_.median(), "p1": s_.quantile(0.01),
                           "p99": s_.quantile(0.99), "maximo": s_.max(), "zeros (sem taxa)": int((s_ == 0).sum()),
                           "positivos abaixo do limite inferior": int(((s_ > 0) & (s_ < baixo)).sum()),
                           "acima do limite superior": int((s_ > alto).sum()), "limites (inferior; superior)": f"{baixo}; {alto}"})
    return pd.DataFrame(linhas)


def geografia(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    linhas = []
    for nome, df in d.items():
        tem = df["lat"].notna() & df["lon"].notna()
        fora = tem & ~(df["lat"].between(*CAIXA_LAT) & df["lon"].between(*CAIXA_LON))
        linhas.append({"segmento": nome, "n": len(df), "com coordenadas (%)": tem.mean() * 100,
                       "fora da caixa de Jacarei": int(fora.sum()),
                       "corr. lat x preco_m2 (Spearman)": stats.spearmanr(df.loc[tem, "lat"], df.loc[tem, "preco_m2"]).statistic,
                       "corr. lon x preco_m2 (Spearman)": stats.spearmanr(df.loc[tem, "lon"], df.loc[tem, "preco_m2"]).statistic})
    return pd.DataFrame(linhas)


def tempo(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = d["residencial"].copy()
    df["trimestre de criacao"] = df["created_at"].dt.tz_convert(None).dt.to_period("Q").astype(str)
    tab = df.groupby(["trimestre de criacao", "segmento"])["preco_m2"].agg(["size", "median"]).unstack("segmento")
    tab.columns = [f"{a} ({b})" for a, b in tab.columns]
    tab = tab.rename(columns=lambda c: c.replace("size", "n").replace("median", "mediana preco_m2")).reset_index()
    tab = tab[tab["trimestre de criacao"] >= "2022Q1"].copy()
    for c in [c for c in tab.columns if c.startswith("n (")]:
        tab[c] = tab[c].fillna(0).astype(int)
    return tab


# ----------------------------------------------------------------------------- figuras
def fig_distribuicao(d: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.8))
    res = d["residencial"]
    ordem = res.groupby("property_type")["preco_m2"].median().sort_values().index
    sns.boxplot(data=res, y="property_type", x="preco_m2", order=ordem, hue="segmento", palette=COR, fliersize=1.5, ax=eixos[0], dodge=False)
    eixos[0].set_title("Preco por m2 por tipo de imovel"); eixos[0].set_xlabel("R$/m2"); eixos[0].set_ylabel("")
    for nome in SEGMENTOS:
        eixos[1].hist(d[nome]["preco_m2"], bins=50, alpha=0.6, color=COR[nome], label=nome, density=True)
        eixos[2].hist(np.log(d[nome]["preco_m2"]), bins=50, alpha=0.6, color=COR[nome], label=nome, density=True)
    eixos[1].set_title("Distribuicao de preco_m2 (assimetria a direita)"); eixos[1].set_xlabel("R$/m2"); eixos[1].legend()
    eixos[2].set_title("Distribuicao de log(preco_m2)"); eixos[2].set_xlabel("log(R$/m2)")
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_distribuicao.png")


def fig_area_preco(d: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.6))
    for eixo, nome in zip(eixos, SEGMENTOS):
        df = d[nome]
        eixo.scatter(df["usable_area_m2"], df["preco_m2"], s=4, alpha=0.25, color=COR[nome])
        eixo.set_xscale("log")
        rho = stats.spearmanr(df["usable_area_m2"], df["preco_m2"]).statistic
        eixo.set_title(f"{nome}: area x preco por m2 (Spearman {rho:.2f})")
        eixo.set_xlabel("area util (m2, escala log)"); eixo.set_ylabel("R$/m2"); eixo.grid(alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_area_preco.png")


def fig_correlacao(matrizes: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(15, 6.2))
    for eixo, (nome, m) in zip(eixos, matrizes.items()):
        sns.heatmap(m, cmap="RdBu_r", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", annot_kws={"size": 7}, cbar=nome == "casa", ax=eixo)
        eixo.set_title(f"{nome}: correlacao de Spearman")
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_correlacao.png")


def fig_bairros(topo: pd.DataFrame) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(13, 5))
    for eixo, nome in zip(eixos, SEGMENTOS):
        t = topo[topo["segmento"] == nome].sort_values("preco_m2 mediana")
        eixo.barh(t["neighborhood"], t["preco_m2 mediana"], color=COR[nome])
        for y, (v, n) in enumerate(zip(t["preco_m2 mediana"], t["n"])):
            eixo.text(v, y, f" n={n}", va="center", fontsize=7)
        eixo.set_title(f"{nome}: 12 bairros com mais anuncios")
        eixo.set_xlabel("mediana de R$/m2")
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_bairros.png")


def fig_condominio(d: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, 3, figsize=(15, 4.6))
    casa = d["casa"]
    sns.boxplot(data=casa.assign(grupo=casa["em_condominio"].map({0: "fora de condominio", 1: "em condominio"})),
                x="grupo", y="preco_m2", color=COR["casa"], fliersize=1.5, ax=eixos[0])
    eixos[0].set_title("Casas: R$/m2 dentro x fora de condominio", fontsize=10); eixos[0].set_xlabel(""); eixos[0].set_ylabel("R$/m2")
    for eixo, nome in zip(eixos[1:], SEGMENTOS):
        df = d[nome]
        df = df[df["monthly_condo"] > 0]
        eixo.scatter(df["monthly_condo"], df["preco_m2"], s=4, alpha=0.25, color=COR[nome])
        eixo.set_xscale("log")
        rho = stats.spearmanr(df["monthly_condo"], df["preco_m2"]).statistic
        eixo.set_title(f"{nome}: taxa de condominio x R$/m2 (Spearman {rho:.2f})", fontsize=10)
        eixo.set_xlabel("condominio mensal (R$, escala log)"); eixo.set_ylabel("R$/m2"); eixo.grid(alpha=0.3)
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_condominio.png")


def fig_mapa(d: dict[str, pd.DataFrame]) -> str:
    fig, eixos = plt.subplots(1, 2, figsize=(13, 5.4))
    for eixo, nome in zip(eixos, SEGMENTOS):
        df = d[nome].dropna(subset=["lat", "lon"])
        df = df[df["lat"].between(*CAIXA_LAT) & df["lon"].between(*CAIXA_LON)]
        pontos = eixo.scatter(df["lon"], df["lat"], c=df["preco_m2"], s=6, alpha=0.6, cmap="viridis",
                              vmin=df["preco_m2"].quantile(0.05), vmax=df["preco_m2"].quantile(0.95))
        eixo.set_title(f"{nome}: anuncios com coordenadas (n={len(df)})", fontsize=10)
        eixo.set_xlabel("longitude"); eixo.set_ylabel("latitude"); eixo.set_aspect("equal")
        fig.colorbar(pontos, ax=eixo, label="R$/m2 (p5 a p95)", shrink=0.8)
    fig.tight_layout()
    return salvar_fig(fig, "eda_vivareal_mapa.png")


# ----------------------------------------------------------------------------- orquestracao
def executar() -> dict:
    d = carregar()
    desc, falt, tipo = descritiva(d), faltantes(d), por_tipo(d)
    corr, matrizes = correlacao_com_alvo(d)
    vif = multicolinearidade(d)
    bair, topo = bairros(d)
    cond, geo, temp, impl = condominio(d), geografia(d), tempo(d), implausiveis(d)
    figuras = [fig_distribuicao(d), fig_area_preco(d), fig_correlacao(matrizes), fig_bairros(topo), fig_condominio(d), fig_mapa(d)]

    tabelas = {"vivareal_descritiva.csv": desc, "vivareal_faltantes.csv": falt, "vivareal_por_tipo.csv": tipo,
               "vivareal_correlacao_alvo.csv": corr, "vivareal_vif.csv": vif, "vivareal_bairros_resumo.csv": bair,
               "vivareal_bairros_top.csv": topo, "vivareal_condominio.csv": cond, "vivareal_geografia.csv": geo, "vivareal_tempo.csv": temp,
               "vivareal_implausiveis.csv": impl}
    for nome, df in tabelas.items():
        salvar_tab(df, nome)

    L = ["# Analise exploratoria: datasets VivaReal (apartamento, casa, residencial)", "",
         "Gerado por `python main.py eda-vivareal`. Nao editar manualmente. Fonte: `data/processed/vivareal/*.csv`",
         "(saida de `vivareal-prep`). A leitura esta em `docs/ANALISE_EXPLORATORIA.md`.", "",
         "## 1. Resumo por segmento", "", md(desc, 2), "", "## 2. Valores ausentes (%)", "", md(falt, 1), "",
         "## 3. Por tipo de imovel", "", md(tipo, 1), "",
         "## 4. Correlacao (Spearman) das variaveis com preco_m2", "", md(corr, 3), "",
         "## 5. Multicolinearidade (VIF; acima de 5 merece atencao, acima de 10 e problema)", "", md(vif, 2), "",
         "## 6. Bairros", "", md(bair, 2), "", "Os 12 bairros com mais anuncios por segmento:", "", md(topo, 1), "",
         "## 7. Condominio", "", md(cond, 3), "",
         "Valores implausiveis que a limpeza atual nao trata (pendencia para o `vivareal-prep`):", "", md(impl, 1), "",
         "## 8. Coordenadas", "", md(geo, 3), "",
         "## 9. Tempo (por trimestre de criacao do anuncio)", "",
         "Anuncios ativos em marco/2026 agrupados pela data de publicacao: ha vies de sobrevivencia; nao e serie de precos.", "",
         md(temp, 1), "", "## Figuras geradas", ""]
    L += [f"- `{f}`" for f in figuras]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
    return {"desc": desc, "corr": corr, "vif": vif, "bairros": bair, "cond": cond, "geo": geo, "impl": impl, "figuras": figuras}
