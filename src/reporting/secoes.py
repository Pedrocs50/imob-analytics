"""Secoes do relatorio. Cada funcao recebe os numeros (`numeros.coletar()`) e o `Relato` (que junta avisos de consistencia)
e devolve Markdown. Afirmacoes interpretativas passam por `r.afirmar(condicao, texto)`: so entram se os numeros as sustentam."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from src.reporting.referencias import REFERENCIAS, por_tema

FIG = os.path.join("reports", "figures")
SEG_ROT = {"apartamento": "Apartamento", "casa": "Casa", "residencial": "Residencial"}


# ----------------------------------------------------------------------------- utilidades
class Relato:
    def __init__(self) -> None:
        self.avisos: list[str] = []

    def afirmar(self, condicao: bool, texto: str, onde: str = "") -> str:
        """Devolve o texto se a condicao vale; senao registra um aviso para revisao e devolve um marcador."""
        if condicao:
            return texto
        self.avisos.append(f"{onde or texto[:70]}: a afirmação já não é sustentada pelos números atuais.")
        return f"**[revisar: a afirmação “{texto[:60]}…” não é sustentada pelos números atuais]**"

    def ausente(self, nome: str, comando: str) -> str:
        self.avisos.append(f"{nome}: fonte ausente (rode `{comando}`).")
        return f"> *Seção indisponível: faltam resultados de {nome}. Gere com `{comando}`.*"


_ACENTOS = [("Localizacao", "Localização"), ("anuncios", "anúncios"), ("anuncio", "anúncio"), ("area util", "área útil"), ("Comodos", "Cômodos"), ("Condominio", "Condomínio"),
            ("condominio", "condomínio"), ("suite", "suíte"), (" m2", " m²"), ("Tendencia", "Tendência"), ("semelhanca", "semelhança"), ("so o alvo", "só o alvo"),
            ("Setor e Censo", "Setor e Censo"), ("Terreno (casas)", "Terreno (casas)")]


def acentuar(texto: str) -> str:
    """Rotulos dos CSVs saem sem acento (convencao dos arquivos de resultado); o relatorio os apresenta com acento."""
    for a, b in _ACENTOS:
        texto = texto.replace(a, b)
    return texto


def br(x: float, d: int = 1) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x: float, d: int = 1) -> str:
    return f"{br(x, d)}%"


def tabela(df: pd.DataFrame, formatos: dict[str, int] | None = None) -> str:
    """Tabela Markdown; `formatos` diz quantas casas decimais por coluna numerica (padrao 2)."""
    formatos = formatos or {}
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    linhas = []
    for _, r in df.iterrows():
        cel = []
        for c in df.columns:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cel.append("—" if np.isnan(v) else br(float(v), formatos.get(c, 2)))
            else:
                cel.append(str(v))
        linhas.append("| " + " | ".join(cel) + " |")
    return "\n".join([cab, sep, *linhas])


def figura(arquivo: str, legenda: str) -> str:
    return f"![{legenda}](figures/{arquivo})\n*Figura: {legenda}*\n" if os.path.exists(os.path.join(FIG, arquivo)) else ""


# ----------------------------------------------------------------------------- 1. resumo
def resumo(n: dict, r: Relato) -> str:
    if "conjunto" not in n or not n["preco_total"] or n["tendencias"] is None:
        return "## 1. Resumo executivo\n\n" + r.ausente("resumo", "python main.py modelos-avancados e projecao")
    c, pt = n["conjunto"], n["preco_total"]
    s_nac, s_sjc = n["series"]["nacional"], n["series"]["SJC"]
    arima12 = s_nac["arima"][(s_nac["arima"]["h (meses)"] == 12) & (s_nac["arima"]["modelo"] == "arima")]["MAPE (%)"].iloc[0] if s_nac["arima"] is not None else np.nan
    t12 = n["tendencias"][(n["tendencias"]["cenario"] == "ARIMA SJC") & (n["tendencias"]["h"] == 12)].iloc[0]
    p = n["projecao"]
    est = {s: p[p["segmento"] == s]["preco_m2_estimado_hoje"].median() for s in dados_seg()}
    return f"""## 1. Resumo executivo

- **O que foi feito.** Duas trilhas sobre o mercado imobiliário de Jacareí-SP: (i) **precificação** do R$/m² de cada anúncio (VivaReal, março/2026) e
  (ii) **séries temporais** do índice FipeZAP (nacional e São José dos Campos) com ARIMA, LSTM e gradient boosting global, combinadas numa **projeção de preço**.
- **Precificação.** O conjunto final de modelos explica **R² = {br(c['apartamento']['R2'], 2)} (apartamento)** e **{br(c['casa']['R2'], 2)} (casa)** do R$/m² no teste temporal
  (anúncios mais recentes), com MAPE de {pct(c['apartamento']['MAPE (%)'])} e {pct(c['casa']['MAPE (%)'])}. Medido como a literatura brasileira costuma medir (preço total,
  partição aleatória), o R² sobe para {br(pt['apartamento']['R2'], 2)} e {br(pt['casa']['R2'], 2)}.
- **Séries.** No índice nacional o **ARIMA(0,2,3) é o melhor modelo** (erro de {pct(arima12, 2)} em 12 meses). Em São José dos Campos as redes e o gradient boosting erram menos aos 6 e 12 meses,
  mas **sem significância estatística** (poucas origens de teste). Nenhum modelo é uniformemente melhor.
- **Projeção.** A mediana do valor estimado hoje é de **R$ {br(est['apartamento'], 0)}/m² (apartamento)** e **R$ {br(est['casa'], 0)}/m² (casa)**; o cenário central (ARIMA de SJC)
  aponta **{br((np.exp(t12['variacao']) - 1) * 100, 1)}%** em 12 meses (alta se positivo), com IC95 de {br((np.exp(t12['inf']) - 1) * 100, 1)}% a {br((np.exp(t12['sup']) - 1) * 100, 1)}%.
- **Ressalva principal.** São preços **pedidos** em anúncios de um único dia, e o FipeZAP **não cobre Jacareí** (a tendência usa São José dos Campos como referência).
"""


def dados_seg():
    return ("apartamento", "casa")


# ----------------------------------------------------------------------------- 2. escopo e dados
def escopo_dados(n: dict, r: Relato) -> str:
    l = n["limpeza"]
    cont = {s: (len(n["anuncios"][s]) if n["anuncios"][s] is not None else None) for s in SEG_ROT}
    linhas_limpeza = ""
    if l.get("bruto"):
        linhas_limpeza = (f"A base tem **{br(l['bruto'], 0)}** registros; **{br(l['residencial'], 0)}** são residenciais e **{br(l['dedup'], 0)}** permanecem após remover "
                          f"{br(l['duplicatas'], 0)} duplicatas (mesmo anúncio coletado mais de uma vez; fica o registro mais recente). ")
    return f"""## 2. Objetivo, escopo e dados

**Objetivo.** Analisar e prever o mercado imobiliário de Jacareí-SP (iniciação científica). As metas do projeto são coleta, tratamento, análise exploratória,
regressão e ARIMA, LSTM, comparação ARIMA x LSTM, sensibilidade das variáveis, visualizações interativas e este relatório.

**Duas trilhas, porque os dados impõem isso:**

| Trilha | Dados | O que se prevê |
|---|---|---|
| Precificação | VivaReal de Jacareí: uma fotografia de março/2026 | O R$/m² de um anúncio, a partir das características do imóvel e da localização (previsão **transversal**, não no tempo) |
| Séries temporais | FipeZAP (índice nacional desde 2008, 224 meses; São José dos Campos desde 2018, 104 meses) e variáveis macro (BCB, IBGE, IPEA) | O índice de preço de venda nos próximos meses (ARIMA, ARIMAX, LSTM, gradient boosting) |

O VivaReal **não** permite previsão no tempo (é uma fotografia, com viés de sobrevivência nas datas de criação), e o FipeZAP **não tem Jacareí**: por isso a ponte entre as trilhas
é uma premissa explícita (Jacareí acompanha São José dos Campos).

**Dados do VivaReal.** {linhas_limpeza}Os dados foram separados em **apartamento ({br(cont['apartamento'] or 0, 0)})**, **casa ({br(cont['casa'] or 0, 0)})** e **residencial
({br(cont['residencial'] or 0, 0)})**, com limites de preço, área e cômodos por segmento e remoção de valores extremos por IQR. Taxas implausíveis de condomínio e IPTU viram ausentes
(o IPTU ficou fora dos modelos: a unidade do campo não está confirmada).

**Informação externa.** Setores censitários do IBGE (Censo 2022; 544 setores em Jacareí) e variáveis do Censo por setor (renda do responsável, densidade, moradores por domicílio,
domicílios vagos), atribuídos às coordenadas por junção espacial.

**Dados faltantes e como foram tratados** (detalhe em `docs/DIARIO_MODELAGEM.md`):

| Problema | Tratamento |
|---|---|
| Coordenadas ausentes (~52% dos anúncios) | Imputação hierárquica só com coordenadas (mediana da rua no bairro, depois do bairro), nunca com o preço; cobertura de 99% |
| Taxa de condomínio ausente | Indicador de ausência e o valor (a ausência é informativa) |
| Suítes ausentes | Valor nativo ausente nas árvores; indicador no modelo linear |
| Bairros e setores raros | Agrupados em uma categoria (bairro < 30 anúncios, setor < 15) |
| Anúncios duplicados | Mantido o mais recente (evita o mesmo anúncio no treino e no teste) |
| Texto do anúncio | 150 palavras e bigramas, **sem dígitos nem preços** (o preço aparece em 19% dos títulos: seria vazamento do alvo) |
"""


# ----------------------------------------------------------------------------- 3. metodos
def metodos(n: dict, r: Relato) -> str:
    return """## 3. Métodos

### 3.1 Precificação (R$/m² de um anúncio)

- **Validação.** Divisão **temporal**: treino nos 75% de anúncios mais antigos (pela data de criação) e teste nos 25% mais recentes, a mais exigente; também holdout aleatório de 20% e 5-fold.
  Métricas: R², MAE (R$/m²) e MAPE (%).
- **Modelos.** Regressão linear (referência), HistGradientBoosting, LightGBM e CatBoost; **conjunto** (média dos três ajustados).
- **Variáveis.** Características do imóvel (área, cômodos, vagas, suítes, tipo, condomínio), bairro, coordenadas, preço dos 15 vizinhos reais mais próximos
  (calculado **sem vazamento**: cada anúncio fica fora do próprio cálculo), setor IBGE e Censo 2022, área do terreno, indicadores de palavras do anúncio e contexto (área relativa ao bairro, número de
  anúncios na rua e no bairro, distância ao centro).
- **Ajuste de parâmetros.** Busca bayesiana (Optuna/TPE) com validação cruzada interna **só no treino**; o teste nunca participa da escolha.
- **Incerteza.** Intervalos **conformais**: quantil do erro relativo fora da amostra no treino; testados no teste temporal.
- **Importância e sensibilidade.** Permutação por grupo de variáveis e cenários "e se?" sobre o modelo final.

### 3.2 Séries temporais (índice FipeZAP)

- **Transformação.** Log do índice; `d = 2` (testes ADF e KPSS); ARIMA(0,2,3) (a média móvel trimestral do índice aparece como MA(3)).
- **Avaliação.** *Walk-forward* com janela expansiva (1, 3, 6 e 12 meses), contra benchmarks (ingênuo e tendência), com teste de **Diebold-Mariano** (Newey-West, ajuste de Harvey).
- **Variáveis externas.** Painéis "as-of" (cada linha traz só o que já estava publicado, com defasagens confirmadas) e teste automático de vazamento temporal.
- **LSTM e painel.** Rede de 1 camada em **painel de 50 cidades**, modelando o crescimento padronizado; variantes com todas as cidades, as 10 mais parecidas e ponderação por semelhança;
  gradient boosting global como comparador.

### 3.3 Projeção de preço

Valor estimado de cada anúncio por previsões **fora da amostra** (5 partições), levado de março/2026 até o último índice com a variação **observada** de São José dos Campos, e depois
projetado com a **previsão** do ARIMA de SJC (cenário central), comparado ao ARIMA nacional e à tendência dos últimos 12 meses.
"""


# ----------------------------------------------------------------------------- 4. precificacao
def resultados_precificacao(n: dict, r: Relato) -> str:
    ev, av, iv, pt = n["evolucao"], n["avancados"], n["intervalos"], n["preco_total"]
    if ev is None or av is None or iv is None or "conjunto" not in n:
        return "## 4. Resultados: precificação\n\n" + r.ausente("precificação", "python main.py reg-geo e modelos-avancados")
    ev = ev.rename(columns={s: SEG_ROT[s] for s in SEG_ROT})
    c = n["conjunto"]
    gb_sem, ols = ev.set_index("Etapa").loc["Gradient boosting, sem coordenadas"], ev.set_index("Etapa").loc["Regressão linear (variáveis do imóvel e bairro)"]
    et = ev.set_index("Etapa")
    ordem_et = list(et.index)
    salto_arvore = (gb_sem.values - ols.values)  # linear -> gradient boosting, por segmento
    outros = et.drop(index=[ordem_et[0], ordem_et[2]]).values - et.shift(1).drop(index=[ordem_et[0], ordem_et[2]]).values  # ganho de cada outra etapa
    maior = bool((salto_arvore > np.nanmax(outros, axis=0)).all())
    gb_bate = r.afirmar(maior, "Trocar o modelo linear por árvores (gradient boosting) foi o maior salto isolado de desempenho nos três segmentos.", "evolução do R²")
    final = av.copy()
    final["modelo"] = final["modelo"].str.replace("parametros padrao", "padrão").str.replace("ajustado (Optuna)", "ajustado", regex=False).str.replace("Conjunto (media dos 3 ajustados)", "Conjunto dos 3 ajustados", regex=False)
    tab_final = final[final["segmento"].isin(["apartamento", "casa"])].pivot_table(index="modelo", columns="segmento", values=["R2", "MAE"], sort=False)
    tab_final.columns = [f"{'R²' if a == 'R2' else 'MAE (R$/m²)'} — {SEG_ROT[b].lower()}" for a, b in tab_final.columns]
    tab_final = tab_final.reset_index().rename(columns={"modelo": "Modelo"})
    fmt_f = {cn: (3 if "R²" in cn else 0) for cn in tab_final.columns}
    iv_t = iv.assign(segmento=iv["segmento"].map(SEG_ROT), nominal=(iv["nivel nominal"] * 100).round(0).astype(int).astype(str) + "%",
                     cobertura=(iv["cobertura no teste temporal"] * 100), erro=(iv["erro relativo no quantil"] * 100))
    iv_t = iv_t[["segmento", "nominal", "cobertura", "erro", "largura media (R$/m2)"]].rename(
        columns={"segmento": "Segmento", "nominal": "Nível nominal", "cobertura": "Cobertura no teste (%)", "erro": "Erro relativo do intervalo (±%)", "largura media (R$/m2)": "Largura média (R$/m²)"})
    calibrado = bool(((iv["cobertura no teste temporal"] - iv["nivel nominal"]).abs() <= 0.03).all())
    txt_cal = r.afirmar(calibrado, "A cobertura observada fica a até 3 pontos percentuais do nível nominal nos três segmentos: os intervalos são bem calibrados.", "calibração dos intervalos")
    return f"""## 4. Resultados: precificação

### 4.1 Evolução do R² (teste temporal)

{tabela(ev, {c_: 3 for c_ in ev.columns if c_ != 'Etapa'})}

{gb_bate} A informação nova (terreno, texto, condomínio) e o ajuste de parâmetros acrescentaram ganhos menores, porém consistentes. O Censo 2022 acrescentou pouco, por ser redundante com a localização.
O CatBoost ajustado não superou seus parâmetros padrão (apenas 8 tentativas).

{figura('modelos_avancados_real_previsto.png', 'Preço real e previsto no teste temporal (conjunto final)')}
### 4.2 Modelos finais

{tabela(tab_final, fmt_f)}

No apartamento o conjunto supera o melhor modelo único; em casa e no residencial o LightGBM sozinho empata com o conjunto (diferença dentro do ruído).

### 4.3 Qualidade dos intervalos de previsão

{tabela(iv_t, {'Cobertura no teste (%)': 1, 'Erro relativo do intervalo (±%)': 1, 'Largura média (R$/m²)': 0})}

{txt_cal} O erro de avaliar um imóvel isolado, porém, é grande: mediana do erro relativo fora da amostra de
{pct(pt['apartamento']['erro_relativo_mediano'])} no apartamento e {pct(pt['casa']['erro_relativo_mediano'])} na casa.

### 4.4 O que mais pesa e o que muda o preço

{_sensibilidade(n, r)}
"""


def _sensibilidade(n: dict, r: Relato) -> str:
    g, c = n["sens_grupos"], n["sens_cenarios"]
    if g is None or c is None:
        return r.ausente("sensibilidade", "python main.py sensibilidade")
    linhas = []
    for seg in dados_seg():
        d = g[g["segmento"] == seg].sort_values("aumento do MAE (R$/m2)", ascending=False).head(3)
        linhas.append(f"- **{SEG_ROT[seg]}**: " + "; ".join(f"{acentuar(x['grupo'].split(' (')[0]).lower()} (+{br(x['aumento do MAE (R$/m2)'], 0)} R$/m² de erro; +{br(x['aumento relativo (%)'], 0)}%)" for _, x in d.iterrows()) + ".")
    sel = c[c["cenario"].isin(["+10% de area util", "+1 suite", "+1 vaga", "+50 m2 de terreno", "casa passa a ser em condominio"])]
    sel = sel.assign(segmento=sel["segmento"].map(SEG_ROT), cenario=sel["cenario"].map(acentuar))[["segmento", "cenario", "variacao mediana do R$/m2 (%)", "variacao mediana do preco total (R$)"]]
    sel.columns = ["Segmento", "Cenário", "Variação do R$/m² (%)", "Variação do preço total (R$)"]
    return ("Relevância por grupo de variáveis (aumento do erro ao embaralhar o grupo, teste temporal):\n\n" + "\n".join(linhas) +
            "\n\nCenários “e se?” (mediana entre os imóveis, mantendo o resto):\n\n" + tabela(sel, {"Variação do R$/m² (%)": 1, "Variação do preço total (R$)": 0}) +
            "\n\n*São associações aprendidas dos anúncios, não efeitos causais; o texto do anúncio tem 150 colunas, então seu peso de grupo deve ser lido como “traz informação”.*\n\n" +
            figura("sensibilidade_grupos.png", "Relevância por grupo de variáveis"))


# ----------------------------------------------------------------------------- 5. series
def resultados_series(n: dict, r: Relato) -> str:
    s = n["series"]
    if any(s[k]["modelos"] is None for k in s):
        return "## 5. Resultados: séries temporais\n\n" + r.ausente("séries", "python main.py lstm")
    blocos = []
    verd = {}
    for chave, rot in (("nacional", "Índice nacional (140 origens de teste)"), ("SJC", "São José dos Campos (44 origens de teste)")):
        m, dm = s[chave]["modelos"], s[chave]["dm"]
        piv = m.pivot_table(index="modelo", columns="h (meses)", values="MAPE (%)", sort=False)
        piv.columns = [f"{h} mês" if h == 1 else f"{h} meses" for h in piv.columns]
        piv = piv.reset_index().rename(columns={"modelo": "Modelo"})
        piv["Modelo"] = piv["Modelo"].map(acentuar)
        blocos.append(f"**{rot}** — MAPE (%):\n\n{tabela(piv, {c_: 2 for c_ in piv.columns if c_ != 'Modelo'})}")
        arima = m[m["modelo"].str.startswith("ARIMA")].set_index("h (meses)")["MAPE (%)"]
        melhor = m[~m["modelo"].str.startswith("ARIMA")].groupby("h (meses)")["MAPE (%)"].min()
        verd[chave] = {"arima": arima, "melhor_outro": melhor, "dm": dm}
    nac, sjc = verd["nacional"], verd["SJC"]
    arima_ganha_nac = r.afirmar(bool((nac["arima"] <= nac["melhor_outro"] + 1e-12).all()),
                                "No índice nacional o ARIMA tem o menor erro em todos os horizontes (1, 3, 6 e 12 meses), contra todas as variantes de LSTM, o gradient boosting global e a tendência.", "ARIMA no nacional")
    menor_sjc = bool(sjc["melhor_outro"].loc[[6, 12]].lt(sjc["arima"].loc[[6, 12]]).all())
    d12 = sjc["dm"][sjc["dm"]["h (meses)"] == 12]
    nao_signif = bool((d12["p (bilateral)"] > 0.05).all())
    sjc_txt = r.afirmar(menor_sjc and nao_signif,
                        f"Em São José dos Campos, aos 6 e 12 meses o melhor modelo alternativo erra menos que o ARIMA (12 meses: {pct(sjc['melhor_outro'].loc[12], 2)} contra {pct(sjc['arima'].loc[12], 2)}), "
                        f"mas nenhuma diferença é significativa a 5% aos 12 meses (menor p = {br(d12['p (bilateral)'].min(), 2)}), pois há poucas origens.", "SJC")
    return f"""## 5. Resultados: séries temporais

Mesmo *walk-forward* para todos os modelos (as redes são reajustadas a cada 12 meses; o ARIMA, todo mês). Comparações com Diebold-Mariano contra o ARIMA(0,2,3).

{(chr(10) * 2).join(blocos)}

- {arima_ganha_nac}
- {sjc_txt}
- O painel de 50 cidades ajuda o LSTM quando a série do alvo é longa (nacional), mas não quando é curta (SJC, onde o controle só com a própria série foi o melhor);
  a semelhança entre cidades não trouxe ganho consistente, e as cidades mais parecidas com SJC não são as vizinhas.
- **Resultados negativos que fazem parte do estudo:** ARIMAX com crédito, juros, confiança e IBC-Br, cidades vizinhas defasadas, combinações com tendência e aluguel/yield (razão preço/aluguel) **não** melhoraram o ARIMA
  de forma significativa no índice nacional; alguns o pioraram.
- O intervalo de 95% do ARIMA é conservador no nacional (cobertura de 99% a 100%) e cobre menos que o nominal em SJC: não é confiável para calibrar a incerteza.

{figura('lstm_comparacao.png', 'ARIMA, LSTM e gradient boosting: erro por horizonte')}{figura('arima_previsao.png', 'Previsão do ARIMA para o índice FipeZAP')}"""


# ----------------------------------------------------------------------------- 6. projecao
def projecao(n: dict, r: Relato) -> str:
    p, t = n["projecao"], n["tendencias"]
    if p is None or t is None:
        return "## 6. Projeção de preço de Jacareí\n\n" + r.ausente("projeção", "python main.py projecao")
    linhas = []
    for seg in dados_seg():
        d = p[p["segmento"] == seg]
        linhas.append({"Segmento": SEG_ROT[seg], "Anúncios": float(len(d)), "Pedido (mediana)": d["preco_m2_pedido"].median(), "Estimado hoje": d["preco_m2_estimado_hoje"].median(),
                       "+3 meses": d["preco_m2_proj_3m"].median(), "+6 meses": d["preco_m2_proj_6m"].median(), "+12 meses": d["preco_m2_proj_12m"].median()})
    tab = pd.DataFrame(linhas)
    cen = t.assign(variacao=(np.exp(t["variacao"]) - 1) * 100, inf=(np.exp(t["inf"]) - 1) * 100, sup=(np.exp(t["sup"]) - 1) * 100)
    cen["cenario"] = cen["cenario"].map(acentuar)
    cen = cen.rename(columns={"cenario": "Cenário", "h": "Horizonte (meses)", "variacao": "Variação (%)", "inf": "IC95 inferior (%)", "sup": "IC95 superior (%)"})[["Cenário", "Horizonte (meses)", "Variação (%)", "IC95 inferior (%)", "IC95 superior (%)"]]
    cen["Horizonte (meses)"] = cen["Horizonte (meses)"].astype(float)
    concordam = bool((t.groupby("h")["variacao"].min() > 0).all())
    conc = r.afirmar(concordam, "Os três cenários de tendência apontam alta em todos os horizontes.", "cenários")
    return f"""## 6. Projeção de preço de Jacareí

Medianas de R$/m² (valor estimado de cada anúncio por previsão fora da amostra; “hoje” = último índice publicado):

{tabela(tab, {'Anúncios': 0, 'Pedido (mediana)': 0, 'Estimado hoje': 0, '+3 meses': 0, '+6 meses': 0, '+12 meses': 0})}

Cenários de tendência (variação do R$/m² após o último índice publicado):

{tabela(cen, {'Horizonte (meses)': 0, 'Variação (%)': 1, 'IC95 inferior (%)': 1, 'IC95 superior (%)': 1})}

{conc} A incerteza do **valor de um imóvel específico** (±17% a ±23% em 80%) é muito maior que a da tendência; as duas não foram combinadas em um único intervalo.
**Premissas:** Jacareí acompanha a tendência de São José dos Campos e todos os imóveis variam igual (não há tendência por bairro).

{figura('projecao_cenarios.png', 'Cenários de tendência do FipeZAP aplicados a Jacareí')}{figura('projecao_premio_por_setor.png', 'Preço pedido acima ou abaixo do valor estimado, por setor')}"""


# ----------------------------------------------------------------------------- 7. literatura
def literatura(n: dict, r: Relato) -> str:
    pt, c, ev = n["preco_total"], n.get("conjunto"), n["evolucao"]
    if not pt or c is None:
        return "## 7. Comparação com a literatura\n\n" + r.ausente("comparação", "python main.py projecao e modelos-avancados")
    tab = pd.DataFrame([{"Trabalho": x.citacao.split(". ")[0], "Dados": x.dados, "Método": x.metodo, "Resultado reportado": x.resultado} for x in REFERENCIAS if x.tema in ("precificacao", "series", "incerteza")])
    comp = pd.DataFrame([
        {"Medida": "R² do preço total, partição aleatória (5-fold, fora da amostra)", "Apartamento": pt["apartamento"]["R2"], "Casa": pt["casa"]["R2"]},
        {"Medida": "MAPE do preço total (%)", "Apartamento": pt["apartamento"]["MAPE"], "Casa": pt["casa"]["MAPE"]},
        {"Medida": "R² do R$/m², teste temporal (conjunto final)", "Apartamento": c["apartamento"]["R2"], "Casa": c["casa"]["R2"]},
        {"Medida": "MAPE do R$/m², teste temporal (%)", "Apartamento": c["apartamento"]["MAPE (%)"], "Casa": c["casa"]["MAPE (%)"]},
        {"Medida": "Erro relativo mediano fora da amostra (%)", "Apartamento": pt["apartamento"]["erro_relativo_mediano"], "Casa": pt["casa"]["erro_relativo_mediano"]}])
    faixa = pt["apartamento"]["MAPE"] > 8.21 and pt["casa"]["MAPE"] > 8.21 and pt["apartamento"]["MAPE"] < 18.21 and pt["casa"]["MAPE"] < 18.21
    texto_faixa = r.afirmar(faixa, f"O MAPE do preço total (apartamento {pct(pt['apartamento']['MAPE'])}, casa {pct(pt['casa']['MAPE'])}) fica **entre** o de Belo Horizonte (8,21%) e o de João Pessoa (18,21%).", "MAPE entre as referências")
    ajuste = n["ajuste_gb"]
    e = ev.set_index("Etapa")
    ganho_casa = float(e.loc["+ terreno e texto do anúncio", "casa"] - e.loc["+ vizinhos, setor IBGE e Censo 2022", "casa"])
    texto_txt = r.afirmar(ganho_casa > 0.02, f"Aqui, terreno e texto elevaram o R² temporal das casas em {br(ganho_casa, 3)}, **de acordo** com a literatura.", "ganho de terreno e texto")
    rf_txt = ""
    if ajuste is not None:
        rf = ajuste[ajuste["modelo"].str.startswith("Random Forest") & ajuste["validacao"].str.contains("temporal")].set_index("segmento")["R2"]
        gb = ajuste[ajuste["modelo"].str.contains("padrao") & ajuste["modelo"].str.startswith("Gradient") & ajuste["validacao"].str.contains("temporal")].set_index("segmento")["R2"]
        if len(rf) and len(gb):
            rf_txt = r.afirmar(bool((gb.reindex(rf.index) >= rf).all()),
                               f"Nos mesmos dados e divisões, o gradient boosting supera o Random Forest nos três segmentos (R² temporal {br(gb.get('apartamento', np.nan), 3)} contra {br(rf.get('apartamento', np.nan), 3)} no apartamento), o que **concorda** com a ordenação de Zilli e Bastos (2024).", "GB x RF")
    return f"""## 7. Comparação com a literatura

Comparar números entre estudos exige cuidado: mercados, períodos, **o que é previsto** (preço total ou R$/m²), **o tipo de preço** (anúncio ou venda) e **a forma de validar** (partição aleatória ou temporal)
mudam o resultado. A tabela resume os trabalhos usados; as ressalvas de cada um estão no apêndice B.

{tabela(tab)}

### 7.1 Precificação

Para comparar com trabalhos brasileiros, que reportam o **preço total** com **partição aleatória**, foi calculada a mesma medida a partir das previsões fora da amostra deste projeto:

{tabela(comp, {'Apartamento': 2, 'Casa': 2})}

- {texto_faixa}
- O **R² do preço total é mais alto que o R² do R$/m²** porque a área explica boa parte do preço total. Os R² de 85% (João Pessoa) e 94% (Belo Horizonte) não são comparáveis ao R² do R$/m² deste projeto, que é menor
  por construção; o R² do preço total acima é a comparação justa (ambos com partição aleatória; o de Belo Horizonte usa uma única divisão 90/10, o deste projeto vem de 5 partições).
- {rf_txt}
- **Texto e informação adicional.** A literatura (Cambridge, UConn) indica que combinar atributos textuais e numéricos melhora os modelos. {texto_txt}
  Em apartamentos o ganho do texto foi pequeno no teste temporal.
- **O que explica o preço.** Em João Pessoa, a área foi a variável mais influente, seguida de coordenadas e aluguel do bairro. Aqui a localização fina domina nos apartamentos e bairro, tamanho e condomínio nas casas: **mesma natureza**, com a área e a localização no topo.

### 7.2 Incerteza

Bastos e Paquette (2024) mostram que intervalos **conformais** têm cobertura correta, enquanto regressões quantílicas comuns cobrem menos que o nominal, e que imóveis maiores, mais antigos e de
bairros de renda extrema são mais difíceis de avaliar. Aqui os intervalos conformais cobrem próximo do nominal, e os das casas (mais heterogêneas) são mais largos que os dos apartamentos — **coerente** com o achado deles.

### 7.3 Séries temporais

- Hansson e Rostami (2019) encontram, em preços de casas de Estocolmo e Uppsala, que o ARIMA sazonal supera o LSTM em 12 meses. O resultado do índice nacional aqui é **o mesmo**.
- Siami-Namini e Siami Namin (2018) relatam redução de erro de 84% a 87% do LSTM sobre o ARIMA em séries econômicas e financeiras. Este projeto **não reproduz** esse resultado: o índice FipeZAP é uma série suave (média móvel de 3 meses), quase determinística,
  e o ARIMA é reestimado todo mês no *walk-forward*. São **hipóteses** para a diferença (natureza da série e forma de avaliar), não testadas aqui; o ponto é que o resultado depende do tipo de série e do desenho da avaliação.
- Em SJC, a série curta (104 meses) e o único período de teste limitam qualquer conclusão: as redes erram menos aos 6 e 12 meses, mas sem significância.

### 7.4 Preço pedido, preço de venda e outros avaliadores

- Os dados são **preços pedidos**. Segundo o FipeZAP (via B3 Bora Investir), o desconto médio de negociação é de cerca de 8% (12% quando há desconto), e 68% das compras de setembro/2025 tiveram desconto.
  As estimativas deste projeto são, portanto, **preços pedidos esperados**, e o preço de fechamento tende a ser menor. Nenhum ajuste de negociação foi aplicado.
- O erro mediano do avaliador automático da Zillow é de cerca de 7% para imóveis fora do mercado (cerca de 1,8% para os à venda, que usam o preço anunciado como entrada). O erro relativo mediano deste projeto
  ({pct(pt['apartamento']['erro_relativo_mediano'])} e {pct(pt['casa']['erro_relativo_mediano'])}) é da **mesma ordem de grandeza**, em um mercado menor e com muito menos dados e variáveis, e prevendo o preço pedido.

> **Conclusão da comparação.** Os resultados são **consistentes** com a literatura nos pontos que podem ser comparados (gradient boosting e texto ajudam; intervalos conformais calibram; ARIMA vence o LSTM em
> índices imobiliários suaves), com a ressalva de que não há trabalho idêntico (Jacareí, preço pedido, validação temporal) e de que alguns números da literatura vêm só de resumos.
"""


# ----------------------------------------------------------------------------- 8. limitacoes
def limitacoes(n: dict, r: Relato) -> str:
    return """## 8. Limitações e ameaças à validade

| Limitação | Efeito | O que foi feito / o que falta |
|---|---|---|
| Preços **pedidos**, não de venda | O valor estimado é um preço pedido esperado; a venda tende a ser menor (desconto de negociação) | Documentado; sem ajuste. Falta uma base de preços de transação |
| Fotografia de **um dia** (março/2026) | Não há série temporal própria de Jacareí; a previsão no tempo depende de um proxy | Premissa explícita (SJC); coletar snapshots periódicos |
| FipeZAP **não tem Jacareí** | A projeção supõe que Jacareí acompanha SJC | Cenários alternativos (nacional, tendência); validar a aceitação do proxy |
| Poucos dados de SJC (104 meses; 44 origens de teste) | Resultados de SJC são indicativos, sem significância | Atualizar conforme novos meses forem publicados |
| Apartamentos com R² ~0,73 | Faltam qualidade, conservação, andar e idade do prédio | Buscar essas variáveis |
| Coordenadas reais em ~48% dos anúncios | O resto é imputado pelo bairro/rua | Imputação sem usar o preço; ganho limitado |
| Anúncios do mesmo prédio ou loteamento são parecidos | A divisão temporal reduz, mas não elimina, o vazamento entre treino e teste | Divisão temporal e vizinhos *leave-one-out* |
| Associações, não causalidade | Sensibilidade e cenários "e se?" descrevem o que o modelo aprendeu | Declarado nos textos |
| IPTU com unidade não confirmada | Ficou fora dos modelos | Confirmar a unidade do campo na fonte |
| Literatura comparada por resumos/páginas | Alguns números não foram verificados no texto completo | Ressalvas no apêndice B |
"""


# ----------------------------------------------------------------------------- 9. conclusoes
def conclusoes(n: dict, r: Relato) -> str:
    c = n.get("conjunto")
    if c is None:
        return "## 9. Conclusões e próximos passos\n\n" + r.ausente("conclusões", "python main.py modelos-avancados")
    return f"""## 9. Conclusões e próximos passos

**Conclusões.**

1. É possível estimar o R$/m² anunciado em Jacareí com **R² de {br(c['apartamento']['R2'], 2)} (apartamento) e {br(c['casa']['R2'], 2)} (casa)** no teste mais exigente (anúncios mais recentes), com intervalos de previsão bem calibrados.
   O erro de um imóvel isolado continua alto (MAPE de {pct(c['apartamento']['MAPE (%)'])} a {pct(c['casa']['MAPE (%)'])}); o modelo serve melhor para estimar nível e comparar anúncios.
2. **Informação nova rendeu tanto quanto, ou mais que, o ajuste de parâmetros**: terreno e texto (casas) e a taxa de condomínio e o contexto do anúncio deram ganhos comparáveis ou maiores que a busca de hiperparâmetros; o Censo, redundante com a localização, rendeu pouco.
3. No índice FipeZAP o **ARIMA é difícil de bater**: vence no nacional; em SJC as redes parecem melhores em prazos longos, mas sem evidência estatística. Resultados negativos (aluguel, ARIMAX, vizinhas) estão documentados.
4. A projeção de preço de Jacareí é **coerente nos três cenários** (alta no horizonte de 12 meses), mas depende de duas premissas: Jacareí acompanha SJC e todos os imóveis variam igual.

**Próximos passos.**

1. Coletar **snapshots periódicos** do VivaReal para formar uma série própria de Jacareí e medir crescimento por área.
2. Variáveis de **qualidade do imóvel** (estado, andar, idade do prédio), que são o gargalo dos apartamentos.
3. Confirmar a **unidade do IPTU** na fonte e a adequação do FipeZAP de SJC como proxy de Jacareí.
4. Preços de transação (ou ajuste de negociação) para sair do preço pedido.
5. Atualizar os resultados de SJC quando houver mais meses e refazer a comparação ARIMA x LSTM.
"""


# ----------------------------------------------------------------------------- apendices
def apendices(n: dict, r: Relato) -> str:
    refs = []
    for x in REFERENCIAS:
        refs.append(f"- **{x.citacao}**  \n  Dados: {x.dados} Método: {x.metodo} Resultado: {x.resultado}  \n  *Ressalva de comparabilidade:* {x.ressalva}  \n  <{x.url}>")
    return f"""## Apêndice A. Como reproduzir

Ordem dos comandos (tempos medidos nesta máquina, só CPU):

| Comando | Tempo | Produz |
|---|---|---|
| `python main.py vivareal-prep` | curto | datasets limpos por segmento |
| `python main.py series-coletar`, `series-fipezap`, `series-painel` | minutos | séries e painéis sem vazamento temporal |
| `python main.py reg-linear`, `reg-geo`, `ajuste-gb` | ~7 min (`ajuste-gb`) | regressão linear, geografia/Censo, ajuste |
| `python main.py arima`, `arima-plus` | ~45 s e ~2 min | ARIMA, ARIMAX, vizinhas |
| `python main.py lstm` | ~7 min | LSTM e gradient boosting em painel |
| `python main.py modelos-avancados` | ~70 min | modelos finais, conjunto e intervalos |
| `python main.py sensibilidade`, `projecao` | ~2,5 e ~4 min | sensibilidade e projeção |
| `python main.py prever --segmento ...` | ~40 s | avaliação de um imóvel |
| `python main.py painel`, `relatorio` | segundos | painel interativo e este relatório |

Os parâmetros e as sementes são fixos; reexecutar reproduz os números (uma execução interrompida do `modelos-avancados` reproduziu exatamente os mesmos números do apartamento na segunda tentativa).

## Apêndice B. Referências e ressalvas de comparabilidade

{chr(10).join(refs)}

*Os dados deste projeto: VivaReal de Jacareí (base de anúncios fornecida ao projeto, não versionada por conter dados pessoais de anunciantes), FipeZAP (planilha pública), BCB/IBGE/IPEA (APIs públicas) e Censo 2022 (IBGE).*
"""
