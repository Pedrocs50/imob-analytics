"""Mineracao avancada dos anuncios do VivaReal de Jacarei: regras de associacao, arvore de decisao e validacao.

Complementa `mineracao.py` (correlacao, K-means, termos). Aqui a pergunta e: **o que faz um imovel custar mais que os
vizinhos do mesmo bairro?** O preco e sempre comparado com a mediana do proprio bairro (`rel_bairro`), para nao confundir
"tem piscina" com "mora em bairro caro". Classe alvo: preco/m2 relativo ao bairro no terco superior.

  1. regras de associacao (conjuntos de ate 3 caracteristicas, com suporte, confianca e lift);
  2. arvore de decisao rasa (regras legiveis) com teste em dados separados;
  3. escolha do numero de grupos do K-means (silhueta) e perfil dos grupos;
  4. validacao: IC95% por bootstrap, consistencia entre metades, estabilidade dos grupos, validacao cruzada;
  5. imoveis fora da curva (preco pedido muito acima ou abaixo do esperado, com previsao fora da amostra);
  6. tempo de anuncio no ar versus preco relativo ao bairro.

Sao associacoes, nao efeitos causais. Resultados em `reports/results/mineracao_avancada.md` e `reports/figures/mineracao_*.png`.
"""
import itertools
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from src.pricing.mineracao import FEATURES_GRUPO, N_GRUPOS, NUMERICAS, ROTULOS, SEGMENTOS, _carregar, _md

RELATORIO = os.path.join("reports", "results", "mineracao_avancada.md")
RESULTS_DIR = os.path.join("reports", "results", "mineracao_avancada")
FIGURAS_DIR = os.path.join("reports", "figures")

MIN_ANUNCIOS_BAIRRO = 15  # mediana do bairro so vale com anuncios suficientes
MIN_SUPORTE = 0.03  # a regra precisa valer para ao menos 3% dos anuncios
MIN_ANUNCIOS_REGRA = 100
TAMANHO_MAX_REGRA = 3
MAIS_QUE_O_SUBCONJUNTO = 0.03  # regra maior so entra se a confianca subir isto sobre qualquer parte dela
TOP_REGRAS = 10
SEMENTES = 5
BOOTSTRAP = 200

# colunas de termos do anuncio (vindas do texto) que indicam uma caracteristica
TERMOS = {
    "piscina": ["txt_piscina"], "churrasqueira": ["txt_churrasqueira"], "area gourmet": ["txt_gourmet", "txt_área_gourmet"],
    "varanda": ["txt_varanda"], "quadra": ["txt_quadra"], "portaria": ["txt_portaria"], "seguranca": ["txt_segurança"],
    "academia": ["txt_academia"], "playground": ["txt_playground"], "salao de festas": ["txt_salão_festas"],
    "armarios planejados": ["txt_planejados", "txt_planejada"], "lavabo": ["txt_lavabo"], "quintal": ["txt_quintal"],
}
FEATURES_ARVORE = ["usable_area_m2", "bedrooms", "bathrooms", "suites", "parking_spaces", "monthly_condo", "amenities_count"]
NOMES_ARVORE = {"usable_area_m2": "area util", "bedrooms": "quartos", "bathrooms": "banheiros", "suites": "suites",
                "parking_spaces": "vagas", "monthly_condo": "condominio", "amenities_count": "comodidades"}


def _com_bairro(df: pd.DataFrame) -> pd.DataFrame:
    """So anuncios de bairros com anuncios suficientes; `rel_bairro` = R$/m2 dividido pela mediana do bairro."""
    base = df.dropna(subset=["neighborhood"]).copy()
    base = base[base.groupby("neighborhood")["preco_m2"].transform("size") >= MIN_ANUNCIOS_BAIRRO]
    base["rel_bairro"] = base["preco_m2"] / base.groupby("neighborhood")["preco_m2"].transform("median")
    return base.reset_index(drop=True)


def _itens(df: pd.DataFrame) -> pd.DataFrame:
    """Caracteristicas verdadeiro/falso usadas nas regras: termos do anuncio e faixas das variaveis numericas."""
    itens = {nome: df.reindex(columns=cols, fill_value=0).fillna(0).gt(0).any(axis=1) for nome, cols in TERMOS.items()}
    itens["2+ suites"] = df["suites"].fillna(0) >= 2
    itens["2+ vagas"] = df["parking_spaces"].fillna(0) >= 2
    itens["3+ quartos"] = df["bedrooms"].fillna(0) >= 3
    itens["area acima da mediana"] = df["usable_area_m2"] >= df["usable_area_m2"].median()
    itens["em condominio fechado"] = df["em_condominio"].fillna(False).astype(bool)
    return pd.DataFrame(itens)


def regras(itens: pd.DataFrame, alvo: pd.Series) -> pd.DataFrame:
    """Regras "se tem {A, B, C} entao alvo": suporte, confianca (P(alvo | A,B,C)) e lift (confianca / P(alvo))."""
    n, base = len(itens), alvo.mean()
    matriz, nomes, y = itens.to_numpy(), list(itens.columns), alvo.to_numpy()
    confianca, linhas = {}, []
    for tam in range(1, TAMANHO_MAX_REGRA + 1):
        for combo in itertools.combinations(range(len(nomes)), tam):
            mascara = matriz[:, combo].all(axis=1)
            total = int(mascara.sum())
            if total < max(MIN_ANUNCIOS_REGRA, MIN_SUPORTE * n):
                continue
            conf = float(y[mascara].mean())
            partes = [confianca[c] for c in itertools.combinations(combo, tam - 1) if c in confianca] if tam > 1 else []
            confianca[combo] = conf
            if partes and conf < max(partes) + MAIS_QUE_O_SUBCONJUNTO:  # nao acrescenta nada sobre uma regra menor
                continue
            linhas.append({"se o anuncio tem": " + ".join(nomes[c] for c in combo), "anuncios": total,
                           "suporte (%)": 100 * total / n, "confianca (%)": 100 * conf, "lift": conf / base})
    return pd.DataFrame(linhas).sort_values(["lift", "anuncios"], ascending=False)


def regras_em_dados_nao_vistos(itens: pd.DataFrame, alvo: pd.Series) -> pd.DataFrame:
    """As regras com maior lift sao escolhidas entre centenas de combinacoes, o que infla o lift. Teste honesto: escolher
    as regras numa metade dos anuncios e medir o lift na outra metade, que nao participou da escolha."""
    ordem = np.random.default_rng(1).permutation(len(itens))
    a, b = ordem[:len(itens) // 2], ordem[len(itens) // 2:]
    escolhidas = regras(itens.iloc[a].reset_index(drop=True), alvo.iloc[a].reset_index(drop=True)).head(TOP_REGRAS)
    base_b, linhas = alvo.iloc[b].mean(), []
    for r in escolhidas.itertuples(index=False):
        mascara = itens.iloc[b][r[0].split(" + ")].all(axis=1)
        linhas.append({"regra (escolhida na metade A)": r[0], "lift na metade A": r[4], "anuncios na metade B": int(mascara.sum()),
                       "lift na metade B (nao vista)": alvo.iloc[b][mascara].mean() / base_b})
    return pd.DataFrame(linhas)


def arvore(df: pd.DataFrame, itens: pd.DataFrame, alvo: pd.Series, segmento: str) -> tuple[dict, str]:
    X = pd.concat([df[FEATURES_ARVORE].fillna(df[FEATURES_ARVORE].median()), itens[["em condominio fechado"]].astype(int)], axis=1)
    nomes = [NOMES_ARVORE.get(c, c) for c in X.columns]
    modelo = DecisionTreeClassifier(max_depth=3, min_samples_leaf=150, random_state=0)
    X_tr, X_te, y_tr, y_te = train_test_split(X, alvo, test_size=0.3, random_state=0, stratify=alvo)
    modelo.fit(X_tr, y_tr)
    pred = modelo.predict(X_te)
    metricas = {"acuracia no teste": float((pred == y_te).mean()),
                "acuracia de quem sempre chuta a classe mais comum": float(max(y_te.mean(), 1 - y_te.mean())),
                "AUC no teste": float(roc_auc_score(y_te, modelo.predict_proba(X_te)[:, 1])),
                "acuracia (validacao cruzada, 5 partes)": float(cross_val_score(DecisionTreeClassifier(
                    max_depth=3, min_samples_leaf=150, random_state=0), X, alvo, cv=5).mean())}
    fig, ax = plt.subplots(figsize=(24, 8))
    plot_tree(modelo, feature_names=nomes, class_names=["demais", "preco alto p/ o bairro"], filled=True, rounded=True,
              proportion=True, impurity=False, fontsize=9, ax=ax)
    ax.set_title(f"Arvore de decisao ({segmento}): o que leva o imovel ao terco mais caro do seu bairro")
    fig.savefig(os.path.join(FIGURAS_DIR, f"mineracao_arvore_{segmento}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return metricas, export_text(modelo, feature_names=nomes)


def escolha_de_k(df: pd.DataFrame, segmento: str) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    base = df.dropna(subset=FEATURES_GRUPO).copy()
    x = base[FEATURES_GRUPO].copy()
    x["usable_area_m2"] = np.log1p(x["usable_area_m2"])
    x = StandardScaler().fit_transform(x)
    amostra = np.random.default_rng(0).choice(len(x), size=min(4000, len(x)), replace=False)
    silhuetas = pd.DataFrame([{"k": k, "silhueta": silhouette_score(
        x[amostra], KMeans(k, n_init=10, random_state=0).fit_predict(x[amostra]))} for k in range(2, 9)])
    rotulos = [KMeans(N_GRUPOS, n_init=10, random_state=s).fit_predict(x) for s in range(SEMENTES)]
    estabilidade = np.mean([adjusted_rand_score(rotulos[0], r) for r in rotulos[1:]])
    base["grupo"] = rotulos[0]
    ordem = base.groupby("grupo")["usable_area_m2"].median().sort_values().index
    base["grupo"] = base["grupo"].map({g: i + 1 for i, g in enumerate(ordem)})
    perfil = base.groupby("grupo").agg(anuncios=("preco_m2", "size"), area_mediana=("usable_area_m2", "median"),
                                        quartos=("bedrooms", "median"), suites=("suites", "median"),
                                        vagas=("parking_spaces", "median"), preco_m2_mediano=("preco_m2", "median")).reset_index()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8))
    ax1.plot(silhuetas["k"], silhuetas["silhueta"], marker="o")
    ax1.axvline(N_GRUPOS, color="gray", ls="--", label=f"k usado = {N_GRUPOS}")
    ax1.set(xlabel="numero de grupos (k)", ylabel="silhueta (maior = grupos mais separados)", title="Escolha de k"); ax1.legend()
    ax2.boxplot([g["preco_m2"].values for _, g in base.groupby("grupo")], showfliers=False,
                tick_labels=[f"G{r.grupo}\n{r.area_mediana:.0f} m2, {r.vagas:.0f} vagas" for r in perfil.itertuples()])
    ax2.set(ylabel="R$/m2", title=f"R$/m2 por grupo de {segmento}")
    fig.savefig(os.path.join(FIGURAS_DIR, f"mineracao_grupos_{segmento}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return silhuetas, np.array([estabilidade]), perfil


def validacao_spearman(df: pd.DataFrame, segmento: str) -> pd.DataFrame:
    """Spearman com IC95% (bootstrap) e o mesmo valor em duas metades aleatorias dos dados."""
    rng = np.random.default_rng(0)
    ordem = rng.permutation(len(df))
    metade_a, metade_b = df.iloc[ordem[:len(df) // 2]], df.iloc[ordem[len(df) // 2:]]
    linhas = []
    for col in NUMERICAS:
        sub = df[[col, "preco_m2"]].dropna()
        if len(sub) < 100 or sub[col].nunique() < 3:
            continue
        spearman = lambda d: d[col].corr(d["preco_m2"], method="spearman")  # noqa: E731
        boot = [spearman(sub.sample(len(sub), replace=True, random_state=int(s))) for s in rng.integers(0, 1_000_000_000, BOOTSTRAP)]
        linhas.append({"caracteristica": ROTULOS[col], "n": len(sub), "spearman": spearman(sub),
                       "IC95 inf": np.percentile(boot, 2.5), "IC95 sup": np.percentile(boot, 97.5),
                       "metade A": spearman(metade_a[[col, "preco_m2"]].dropna()), "metade B": spearman(metade_b[[col, "preco_m2"]].dropna())})
    tabela = pd.DataFrame(linhas).sort_values("spearman", key=abs, ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ordenada = tabela.iloc[::-1]
    ax.barh(ordenada["caracteristica"], ordenada["spearman"], color="#3b6ea5",
            xerr=[ordenada["spearman"] - ordenada["IC95 inf"], ordenada["IC95 sup"] - ordenada["spearman"]], capsize=3)
    ax.set(xlabel="correlacao de Spearman com o R$/m2 (barra = IC95%)", title=f"Caracteristicas x preco do m2: {segmento}")
    fig.savefig(os.path.join(FIGURAS_DIR, f"mineracao_correlacao_{segmento}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return tabela


def fora_da_curva(df: pd.DataFrame, itens: pd.DataFrame, segmento: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Preco esperado do R$/m2 por LightGBM com previsao FORA DA AMOSTRA (cada anuncio e previsto por um modelo que nao o viu,
    validacao cruzada de 5 partes). Anuncios muito acima/abaixo do esperado sao candidatos a revisar: erro de cadastro,
    sobrepreco ou oportunidade. O modelo so ve caracteristicas, bairro e coordenadas; nao ve o proprio preco."""
    X = pd.concat([df[FEATURES_ARVORE + ["lat", "lon"]], itens.astype(int)], axis=1)
    X["bairro"] = df["neighborhood"].astype("category")
    y = np.log(df["preco_m2"])
    previsto = np.zeros(len(df))
    for treino, teste in KFold(5, shuffle=True, random_state=0).split(X):
        modelo = LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=20, subsample=0.8,
                               subsample_freq=1, colsample_bytree=0.7, random_state=0, verbose=-1)
        previsto[teste] = modelo.fit(X.iloc[treino], y.iloc[treino]).predict(X.iloc[teste])
    esperado = np.exp(previsto)
    desvio = 100 * (df["preco_m2"] / esperado - 1)
    pd.DataFrame({"tolerancia (%)": range(5, 65, 5), "% dos anuncios dentro": [float((desvio.abs() <= t).mean() * 100) for t in range(5, 65, 5)]}
                 ).to_csv(os.path.join(RESULTS_DIR, f"{segmento}_fora_da_curva_tolerancia.csv"), index=False)
    resumo = {"R2 do log(R$/m2) fora da amostra": float(1 - ((y - previsto) ** 2).sum() / ((y - y.mean()) ** 2).sum()),
              "erro percentual mediano": float(desvio.abs().median()), "% dos anuncios a ate 20% do esperado": float((desvio.abs() <= 20).mean() * 100),
              "% mais de 30% ACIMA do esperado": float((desvio > 30).mean() * 100), "% mais de 30% ABAIXO do esperado": float((desvio < -30).mean() * 100)}
    tabela = pd.DataFrame({"bairro": df["neighborhood"], "area (m2)": df["usable_area_m2"], "quartos": df["bedrooms"], "vagas": df["parking_spaces"],
                           "preco pedido (R$)": df["sale_price"], "R$/m2 pedido": df["preco_m2"], "R$/m2 esperado": esperado, "diferenca (%)": desvio})
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(esperado, df["preco_m2"], s=4, alpha=0.25, color="#3b6ea5")
    limites = [df["preco_m2"].min(), df["preco_m2"].max()]
    ax.plot(limites, limites, color="black", lw=1, label="pedido = esperado")
    ax.plot(limites, [v * 1.3 for v in limites], color="#c0392b", lw=1, ls="--", label="+30%")
    ax.plot(limites, [v * 0.7 for v in limites], color="#c0392b", lw=1, ls="--", label="-30%")
    ax.set(xscale="log", yscale="log", xlabel="R$/m2 esperado (previsao fora da amostra)", ylabel="R$/m2 pedido",
           title=f"Preco pedido x esperado: {segmento}"); ax.legend()
    fig.savefig(os.path.join(FIGURAS_DIR, f"mineracao_fora_da_curva_{segmento}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return resumo, tabela.nsmallest(8, "diferenca (%)"), tabela.nlargest(8, "diferenca (%)")


def tempo_no_ar(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Ha quanto tempo o anuncio esta no ar (coleta menos criacao) e o preco relativo ao bairro."""
    dias = (pd.to_datetime(df["scraped_at"]) - pd.to_datetime(df["created_at"], utc=True).dt.tz_localize(None)).dt.days
    base = df.assign(dias=dias)[dias.between(0, 3650)]
    base = base.assign(faixa=pd.cut(base["dias"], [-1, 30, 90, 180, 365, 730, 4000],
                                    labels=["ate 30 dias", "31-90 dias", "91-180 dias", "181-365 dias", "1 a 2 anos", "mais de 2 anos"]))
    tabela = base.groupby("faixa", observed=True).agg(anuncios=("rel_bairro", "size"), rel_bairro_mediano=("rel_bairro", "median"),
                                                      preco_m2_mediano=("preco_m2", "median")).reset_index()
    tabela["vs bairro (%)"] = 100 * (tabela["rel_bairro_mediano"] - 1)
    return tabela.drop(columns="rel_bairro_mediano"), float(base["dias"].corr(base["rel_bairro"], method="spearman"))


def executar() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURAS_DIR, exist_ok=True)
    saida = ["# Mineracao avancada dos anuncios (VivaReal, Jacarei)\n",
             "Gerado por `python main.py mineracao-avancada`. Complementa `mineracao.md`. A pergunta: **o que faz um imovel custar mais "
             "que os vizinhos do mesmo bairro?** O preco/m2 de cada anuncio e dividido pela mediana do proprio bairro "
             f"(bairros com {MIN_ANUNCIOS_BAIRRO}+ anuncios); a classe \"alto\" e o terco mais caro nessa comparacao. "
             "Sao **associacoes, nao efeitos causais**.\n"]
    for segmento in SEGMENTOS:
        df = _com_bairro(_carregar(segmento))
        itens = _itens(df)
        corte = df["rel_bairro"].quantile(2 / 3)
        alto = df["rel_bairro"] >= corte
        saida.append(f"\n## {segmento.capitalize()} ({len(df)} anuncios; \"alto\" = R$/m2 pelo menos {100 * (corte - 1):.0f}% acima do bairro)\n")

        regras_alto = regras(itens, alto)
        regras_alto.to_csv(os.path.join(RESULTS_DIR, f"{segmento}_regras_alto.csv"), index=False)
        saida.append(f"\n### 1. Regras de associacao: o que acompanha preco alto para o bairro\n\n"
                     f"Probabilidade base de \"alto\": {100 * alto.mean():.0f}%. **Confianca** = % dos anuncios com a combinacao que sao \"alto\"; "
                     f"**lift** = confianca / base (lift 1,5 = 50% mais chance que a media). Combinacoes de ate {TAMANHO_MAX_REGRA} itens em "
                     f"{max(MIN_ANUNCIOS_REGRA, int(MIN_SUPORTE * len(df)))}+ anuncios; so entra regra maior que melhora a menor em "
                     f"{100 * MAIS_QUE_O_SUBCONJUNTO:.0f} pontos.\n\n" + _md(regras_alto.head(TOP_REGRAS), 1))
        validadas = regras_em_dados_nao_vistos(itens, alto)
        validadas.to_csv(os.path.join(RESULTS_DIR, f"{segmento}_regras_validadas.csv"), index=False)
        saida.append(f"\n**Teste em dados nao vistos:** as {TOP_REGRAS} melhores regras escolhidas numa metade dos anuncios e medidas na outra. "
                     f"Lift medio {validadas['lift na metade A'].mean():.2f} (onde foram escolhidas) -> "
                     f"{validadas['lift na metade B (nao vista)'].mean():.2f} (nao vistos). Se continua bem acima de 1, a regra nao e acaso de selecao.\n\n"
                     + _md(validadas, 2))

        metricas, texto_arvore = arvore(df, itens, alto, segmento)
        saida.append("\n### 2. Arvore de decisao (profundidade 3, 70% treino / 30% teste)\n\n" + _md(
            pd.DataFrame([{"medida": k, "valor (%)": 100 * v} for k, v in metricas.items()]), 1)
            + f"\nFigura: `reports/figures/mineracao_arvore_{segmento}.png`. Regras:\n\n```\n{texto_arvore}```\n")

        silhuetas, estabilidade, perfil = escolha_de_k(df, segmento)
        melhor = int(silhuetas.loc[silhuetas["silhueta"].idxmax(), "k"])
        saida.append(f"\n### 3. Grupos de imoveis (K-means, k={N_GRUPOS})\n\nSilhueta por k (maior = grupos mais separados): "
                     + ", ".join(f"k={int(r.k)}: {r.silhueta:.2f}" for r in silhuetas.itertuples())
                     + f". Maior silhueta em k={melhor}; usamos k={N_GRUPOS} porque os grupos ficam interpretaveis "
                     f"(ver perfil)" + (". **Silhueta baixa em k=%d: os perfis se sobrepoem; ler como descricao de perfis, nao como segmentos distintos**" % N_GRUPOS
                                       if silhuetas.set_index("k").loc[N_GRUPOS, "silhueta"] < 0.35 else "") + f". Estabilidade com {SEMENTES} sementes (ARI): {estabilidade[0]:.2f} (1 = mesmos grupos).\n\n" + _md(perfil, 1)
                     + f"\nFigura: `reports/figures/mineracao_grupos_{segmento}.png`.\n")

        tabela = validacao_spearman(df, segmento)
        tabela.to_csv(os.path.join(RESULTS_DIR, f"{segmento}_spearman_validado.csv"), index=False)
        saida.append("\n### 4. Validacao da correlacao (bootstrap e metades)\n\nIC95% por " + f"{BOOTSTRAP} reamostragens; \"metade A/B\" = "
                     "o mesmo calculo em duas metades aleatorias dos dados (se parecidas, o resultado nao e acaso de amostra).\n\n" + _md(tabela)
                     + f"\nFigura: `reports/figures/mineracao_correlacao_{segmento}.png`.\n")
        resumo, abaixo, acima = fora_da_curva(df, itens, segmento)
        saida.append("\n### 5. Imoveis fora da curva (preco pedido x esperado)\n\nO preco esperado vem de um modelo (LightGBM) que ve so "
                     "caracteristicas, bairro e coordenadas, com previsao fora da amostra (cada anuncio e previsto por um modelo que nao o viu). "
                     "Anuncios muito fora do esperado sao **candidatos a revisar**: erro de cadastro, sobrepreco ou oportunidade. "
                     "Nao e prova de que o imovel esta caro ou barato: o modelo nao ve estado de conservacao, acabamento nem fotos.\n\n"
                     + _md(pd.DataFrame([{"medida": k, "valor": v} for k, v in resumo.items()]), 2)
                     + "\n**Mais abaixo do esperado**\n\n" + _md(abaixo, 1) + "\n**Mais acima do esperado**\n\n" + _md(acima, 1)
                     + f"\nFigura: `reports/figures/mineracao_fora_da_curva_{segmento}.png`.\n")
        tabela_tempo, spearman_tempo = tempo_no_ar(df)
        saida.append("\n### 6. Tempo de anuncio no ar x preco relativo ao bairro\n\n"
                     f"Correlacao de Spearman entre dias no ar e preco relativo ao bairro: **{spearman_tempo:.2f}** (fraca). "
                     "Tempo no ar = data da coleta menos a data de criacao do anuncio; anuncios antigos podem estar desatualizados.\n\n" + _md(tabela_tempo, 1))
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("".join(saida))
    print(f"[MINERACAO-AVANCADA] relatorio em {RELATORIO}; figuras em {FIGURAS_DIR}/mineracao_*.png")
