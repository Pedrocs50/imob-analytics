from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.timeseries import panel
from src.timeseries.catalogo import ESTIMADA, FONTES_DEFASAGEM
from src.timeseries.panel import Paineis, montar_paineis

RELATORIO = os.path.join("reports", "results", "series_vazamento.md")
CORTES = ("2013-06-01", "2018-09-01", "2022-03-01", "2025-01-01")  # datas de referencia
VALIDADE_MAXIMA_MESES = panel.VALIDADE_TRIMESTRAL_MESES - 1


@dataclass
class Falha:
    teste: str
    coluna: str
    detalhe: str


def _iguais(a: pd.Series, b: pd.Series) -> pd.Series:
    """Igualdade tolerante que trata NaN == NaN."""
    a, b = a.align(b, join="inner")
    return (a.isna() & b.isna()) | ((a - b).abs() <= 1e-9 * np.maximum(1.0, a.abs().fillna(0)))


def _defasagem_declarada(coluna: str, meta: pd.DataFrame) -> int | None:
    base = coluna[:-6] if coluna.endswith("_ffill") else coluna
    return int(meta.loc[base, "defasagem_meses"]) if base in meta.index else None


# --------------------------------------------------------------------------------------
# T1: o que foi aplicado no painel e o que o catalogo declara
# --------------------------------------------------------------------------------------
def teste_defasagem_declarada(wide: pd.DataFrame, meta: pd.DataFrame, p: Paineis) -> tuple[int, list[Falha]]:
    """Cada serie-base do painel as-of deve ser a serie original deslocada exatamente
    pela defasagem declarada no catalogo (mes r aparece na linha r + L)."""
    falhas, n = [], 0
    for coluna in p.mensal.columns:
        declarada = _defasagem_declarada(coluna, meta)
        if declarada is None or coluna.endswith("_ffill"):
            continue
        n += 1
        esperado = wide[coluna].shift(declarada, freq="MS")
        ok = _iguais(p.mensal[coluna], esperado.reindex(p.mensal.index))
        if not ok.all():
            falhas.append(Falha("defasagem declarada x aplicada", coluna,
                                f"{int((~ok).sum())} linhas diferem do deslocamento de {declarada} mes(es)"))
    return n, falhas


# --------------------------------------------------------------------------------------
# T2: perturbar o futuro nao pode mudar o passado
# --------------------------------------------------------------------------------------
def _perturbar(wide: pd.DataFrame, corte: pd.Timestamp) -> pd.DataFrame:
    """Altera de forma inequivoca todas as observacoes com data de referencia > corte."""
    alterado = wide.copy()
    futuro = alterado.index > corte
    alterado.loc[futuro] = alterado.loc[futuro] * 1.9 + 7.0
    return alterado


def teste_perturbacao(
    wide: pd.DataFrame, meta: pd.DataFrame, p: Paineis, construir=montar_paineis
) -> tuple[int, list[Falha]]:
    """Reconstroi os paineis com dados posteriores ao corte adulterados. A linha t de uma
    coluna com dependencia efetiva de L meses so pode mudar se t > corte + L."""
    falhas, n = [], 0
    for texto in CORTES:
        corte = pd.Timestamp(texto)
        q = construir(_perturbar(wide, corte), meta)

        for coluna, lag in p.defasagem_mensal.items():
            n += 1
            limite = corte + pd.DateOffset(months=lag)
            linhas = p.mensal.index[p.mensal.index <= limite]
            ok = _iguais(p.mensal.loc[linhas, coluna], q.mensal.loc[linhas, coluna])
            if not ok.all():
                falhas.append(Falha("perturbacao (mensal)", coluna,
                                    f"corte {corte:%Y-%m}: {int((~ok).sum())} linha(s) ate {limite:%Y-%m} mudaram "
                                    "com dados futuros alterados"))

        for coluna, k in p.defasagem_trimestral.items():
            n += 1
            # a linha do trimestre que comeca em d usa o trimestre d - k, que termina em d - 3k + 2 meses
            ultimo_mes_usado = p.trimestral.index - pd.DateOffset(months=3 * k) + pd.DateOffset(months=2)
            linhas = p.trimestral.index[ultimo_mes_usado <= corte]
            ok = _iguais(p.trimestral.loc[linhas, coluna], q.trimestral.loc[linhas, coluna])
            if not ok.all():
                falhas.append(Falha("perturbacao (trimestral)", coluna,
                                    f"corte {corte:%Y-%m}: {int((~ok).sum())} trimestre(s) mudaram com dados futuros alterados"))
    return n, falhas


# --------------------------------------------------------------------------------------
# T3: valor trimestral repetido alem da validade
# --------------------------------------------------------------------------------------
def teste_validade_trimestral(wide: pd.DataFrame, meta: pd.DataFrame, p: Paineis) -> tuple[int, list[Falha]]:
    """Recalcula, de forma independente, qual trimestre deveria estar visivel em cada mes
    e exige ausencia quando o ultimo publicado tem mais de 3 meses de disponibilidade."""
    falhas, n = [], 0
    for coluna in [c for c in p.mensal.columns if c.endswith("_ffill")]:
        base = coluna[:-6]
        lag = int(meta.loc[base, "defasagem_meses"])
        serie = wide[base].dropna()
        for mes, valor in p.mensal[coluna].items():
            n += 1
            disponiveis = [q for q in serie.index if q + pd.DateOffset(months=2 + lag) <= mes]
            if not disponiveis:
                esperado = np.nan
            else:
                q = max(disponiveis)
                idade = (mes.year - q.year) * 12 + mes.month - q.month - (2 + lag)
                esperado = serie[q] if idade <= VALIDADE_MAXIMA_MESES else np.nan
            if not ((pd.isna(valor) and pd.isna(esperado)) or valor == esperado):
                falhas.append(Falha("validade do valor trimestral", coluna,
                                    f"{mes:%Y-%m}: painel={valor}, esperado={esperado}"))
                break  # uma ocorrencia por coluna basta
    return n, falhas


# --------------------------------------------------------------------------------------
# Auto-teste: o validador precisa reprovar vazamentos plantados de proposito
# --------------------------------------------------------------------------------------
def autoteste(wide: pd.DataFrame, meta: pd.DataFrame) -> list[tuple[str, bool]]:
    resultados = []

    # (a) painel construido com o IPCA sem defasagem, contra um catalogo que declara 1 mes
    meta_errada = meta.copy()
    meta_errada.loc["bcb_ipca", "defasagem_meses"] = 0
    p_errado = montar_paineis(wide, meta_errada)
    _, falhas = teste_defasagem_declarada(wide, meta, p_errado)
    resultados.append(("IPCA aplicado sem defasagem (T1 deve reprovar)", any(f.coluna == "bcb_ipca" for f in falhas)))

    # (b) deflator com base no FIM da amostra, como no painel antigo (T2 deve reprovar)
    original = panel._derivadas

    def com_vazamento(ref, lag, inicio):
        saida = original(ref, lag, inicio)
        acumulado = (1 + ref["bcb_ipca"] / 100).cumprod()
        indice = acumulado / acumulado.iloc[-1] * 100  # usa o ultimo IPCA da amostra
        for nome in [n for n in saida if n.endswith("preco_m2_real")]:
            saida[nome] = (ref[nome.replace("preco_m2_real", "preco_m2")] / (indice / 100), saida[nome][1])
        return saida

    panel._derivadas = com_vazamento
    try:
        p_vaza = montar_paineis(wide, meta)
        _, falhas = teste_perturbacao(wide, meta, p_vaza, construir=montar_paineis)
    finally:
        panel._derivadas = original
    resultados.append(("deflator com base no fim da amostra (T2 deve reprovar)",
                       any("preco_m2_real" in f.coluna for f in falhas)))
    return resultados


# --------------------------------------------------------------------------------------
def validar_vazamento(wide: pd.DataFrame, meta: pd.DataFrame, p: Paineis) -> dict:
    n1, f1 = teste_defasagem_declarada(wide, meta, p)
    n2, f2 = teste_perturbacao(wide, meta, p)
    n3, f3 = teste_validade_trimestral(wide, meta, p)
    auto = autoteste(wide, meta)
    return {
        "testes": [
            ("T1 defasagem declarada x aplicada", n1, f1),
            ("T2 perturbacao do futuro (mensal e trimestral)", n2, f2),
            ("T3 validade do valor trimestral", n3, f3),
        ],
        "autoteste": auto,
        "falhas": f1 + f2 + f3 + [Falha("autoteste", nome, "validador nao detectou vazamento plantado")
                                  for nome, ok in auto if not ok],
    }


def escrever_relatorio(resultado: dict, meta: pd.DataFrame, p: Paineis, caminho: str = RELATORIO) -> None:
    falhas = resultado["falhas"]
    linhas = [
        "# Validacao de vazamento temporal",
        "",
        "Gerado por `python main.py series-painel`. Nao editar manualmente.",
        "",
        "Convencao: a linha do mes `t` dos paineis `painel_mensal.csv` e `painel_trimestral.csv`",
        "contem so o que estava publicado ate o ultimo dia do mes `t`. Os arquivos `*_referencia.csv`",
        "usam a data de referencia e servem so para o alvo, nunca para as variaveis explicativas.",
        "",
        f"**Resultado: {'REPROVADO' if falhas else 'APROVADO'}** ({len(falhas)} falha(s))",
        "",
        "## Testes",
        "",
        "| Teste | Verificacoes | Falhas |",
        "|---|---|---|",
    ]
    for nome, n, fs in resultado["testes"]:
        linhas.append(f"| {nome} | {n} | {len(fs)} |")
    linhas += ["", "O validador tambem e testado contra vazamentos plantados de proposito:", ""]
    for nome, ok in resultado["autoteste"]:
        linhas.append(f"- {'detectado' if ok else 'NAO DETECTADO'}: {nome}")
    if falhas:
        linhas += ["", "## Falhas", ""] + [f"- `{f.coluna}` ({f.teste}): {f.detalhe}" for f in falhas]

    linhas += [
        "", "## Defasagens aplicadas", "",
        "`L` = meses entre o ultimo mes do periodo de referencia e a divulgacao (catalogo). "
        "No painel trimestral, o deslocamento e de `k = ceil(L/3)` trimestres.",
        "",
        "| Serie | L | k (trimestres) | Situacao | Fonte |",
        "|---|---|---|---|---|",
    ]
    for sid in meta.index:
        chave = "fipezap" if sid.startswith("fipezap_") else sid
        situacao, fonte = FONTES_DEFASAGEM.get(chave, (ESTIMADA, "sem fonte registrada"))
        if sid.startswith("fipezap_") and sid != "fipezap_nacional_res_venda_preco_m2":
            continue  # as demais series FipeZAP seguem a mesma regra; uma linha representa todas
        rotulo = "`fipezap_*` (35 series)" if sid.startswith("fipezap_") else f"`{sid}`"
        lag = int(meta.loc[sid, "defasagem_meses"])
        linhas.append(f"| {rotulo} | {lag} | {-(-lag // 3)} | {situacao} | {fonte} |")
    linhas += ["", "Colunas derivadas herdam a maior defasagem das series de entrada.", ""]

    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))
