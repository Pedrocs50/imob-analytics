from __future__ import annotations

import math
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.timeseries.config import DB_PATH, PROCESSED_DIR
from src.timeseries.storage import conectar

# Convencao dos paineis "as-of" (arquivos painel_mensal.csv e painel_trimestral.csv):
# a linha do mes t contem SO o que estava publicado ate o ultimo dia do mes t. Uma serie
# com defasagem L (meses entre o ultimo mes do periodo de referencia e a divulgacao) tem o
# valor do mes de referencia r na linha r + L. Os paineis "_referencia" nao deslocam nada:
# servem para o ALVO e para descrever a serie, nunca para as variaveis explicativas.

PREFIXO_FIPEZAP = "fipezap_"
COLUNA_ALVO = "fipezap_nacional_res_venda_preco_m2"  # define o fim da janela dos paineis
VALIDADE_TRIMESTRAL_MESES = 3  # um valor trimestral vale ate a proxima divulgacao esperada

# como cada coluna derivada vira trimestre (o padrao e a media do trimestre)
AGREGACAO_DERIVADA = {"ipca_indice": "last", "ipca_acum_12m": "last"}


@dataclass
class Paineis:
    mensal: pd.DataFrame  # as-of: sem informacao futura
    mensal_referencia: pd.DataFrame  # indexado pelo mes de referencia (nao usar como preditor)
    trimestral: pd.DataFrame  # as-of
    trimestral_referencia: pd.DataFrame
    defasagem_mensal: dict[str, int]  # meses entre a data de referencia e a linha onde entra
    defasagem_trimestral: dict[str, int]  # trimestres de deslocamento (k)


def carregar_wide(db_path: str = DB_PATH) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (observacoes em formato largo, tabela `series`). O indice e a data
    de referencia (primeiro dia do periodo)."""
    with conectar(db_path) as conexao:
        obs = pd.read_sql("SELECT serie_id, data_ref, valor FROM observacoes", conexao)
        meta = pd.read_sql("SELECT * FROM series", conexao).set_index("id")
    obs["data_ref"] = pd.to_datetime(obs["data_ref"])
    wide = obs.pivot(index="data_ref", columns="serie_id", values="valor").sort_index()
    return wide, meta


def _derivadas(ref: pd.DataFrame, lag: dict[str, int], inicio_painel: pd.Timestamp) -> dict[str, tuple[pd.Series, list[str]]]:
    """Colunas derivadas calculadas sobre o painel de referencia. Retorna
    {nome: (serie, colunas_de_entrada)}; a defasagem de cada uma e a maior das entradas."""
    saida: dict[str, tuple[pd.Series, list[str]]] = {}

    if "bcb_ipca" in ref:
        ipca = ref["bcb_ipca"]
        acumulado = (1 + ipca / 100).cumprod()
        # base = mes em que o painel comeca (constante causal; nao depende do fim da amostra)
        indice = acumulado / acumulado.loc[inicio_painel] * 100
        saida["ipca_indice"] = (indice, ["bcb_ipca"])
        saida["ipca_acum_12m"] = (
            ((1 + ipca / 100).rolling(12).apply(np.prod, raw=True) - 1) * 100, ["bcb_ipca"]
        )
        for col in [c for c in ref if c.startswith(PREFIXO_FIPEZAP) and c.endswith("venda_preco_m2")]:
            saida[col.replace("preco_m2", "preco_m2_real")] = (
                ref[col] / (indice / 100), [col, "bcb_ipca"]
            )
        if "bcb_selic_mes" in ref:
            saida["selic_real_mes"] = (
                ((1 + ref["bcb_selic_mes"] / 100) / (1 + ipca / 100) - 1) * 100, ["bcb_selic_mes", "bcb_ipca"]
            )

    for col in [c for c in ref if c.startswith(PREFIXO_FIPEZAP) and c.endswith(("venda_indice", "locacao_indice"))]:
        saida[col.replace("indice", "var_mensal")] = (ref[col].pct_change(fill_method=None) * 100, [col])
        saida[col.replace("indice", "var_12m")] = (ref[col].pct_change(12, fill_method=None) * 100, [col])

    for col in ("bcb_igpm", "bcb_incc"):
        if col in ref:
            saida[f"{col}_acum_12m"] = (
                ((1 + ref[col] / 100).rolling(12).apply(np.prod, raw=True) - 1) * 100, [col]
            )
    return saida


def _trimestral_ao_mes(serie: pd.Series, defasagem: int, indice: pd.DatetimeIndex) -> pd.Series:
    """Serie trimestral (data = 1o dia do trimestre) vista mes a mes. O valor do trimestre q
    (meses q, q+1, q+2) so existe a partir do mes q+2+defasagem e vale ate a proxima
    divulgacao esperada; depois disso fica ausente (nao ha repeticao por anos)."""
    disponivel = serie.dropna().copy()
    disponivel.index = disponivel.index + pd.DateOffset(months=2 + defasagem)
    disponivel = disponivel[~disponivel.index.duplicated(keep="last")]
    return disponivel.reindex(indice).ffill(limit=VALIDADE_TRIMESTRAL_MESES - 1)


def _agregar_trimestre(serie: pd.Series, tipo: str, por_tri: pd.PeriodIndex) -> pd.Series:
    grupos = serie.groupby(por_tri)
    if tipo == "taxa":  # variacao % no mes -> variacao composta no trimestre
        return grupos.apply(lambda s: ((1 + s / 100).prod() - 1) * 100 if s.notna().all() else np.nan)
    if tipo in ("saldo", "last"):
        return grupos.last()
    return grupos.apply(lambda s: s.mean() if s.notna().all() else np.nan)


def montar_paineis(wide: pd.DataFrame, meta: pd.DataFrame) -> Paineis:
    """Funcao pura (sem disco): monta os 4 paineis a partir das observacoes e do catalogo."""
    freq, tipo_serie = meta["frequencia"], meta["tipo"]
    lag_base = {c: int(meta.loc[c, "defasagem_meses"]) for c in wide}
    mensais = [c for c in wide if freq[c] == "M"]
    trimestrais = [c for c in wide if freq[c] == "Q"]

    alvo = wide[COLUNA_ALVO].dropna()
    inicio, fim = alvo.index.min(), alvo.index.max()
    indice = pd.date_range(wide.index.min(), fim, freq="MS")

    # ---------------- painel mensal de referencia ----------------
    ref = wide.reindex(indice)[mensais].copy()
    derivadas = _derivadas(ref, lag_base, inicio)
    lag_mensal = {c: lag_base[c] for c in mensais}
    for nome, (serie, entradas) in derivadas.items():
        ref[nome] = serie
        lag_mensal[nome] = max(lag_base[e] for e in entradas)

    # ---------------- painel mensal as-of ----------------
    asof = pd.DataFrame({c: ref[c].shift(lag_mensal[c]) for c in ref}, index=indice)
    lag_efetivo = dict(lag_mensal)  # meses entre a data de referencia da observacao e a linha
    for c in trimestrais:
        asof[f"{c}_ffill"] = _trimestral_ao_mes(wide[c], lag_base[c], indice)
        lag_efetivo[f"{c}_ffill"] = 2 + lag_base[c]  # data = 1o dia do trimestre; ultimo mes = +2

    recorte = slice(inicio, None)
    mensal_ref, mensal = ref.loc[recorte], asof.loc[recorte]
    mensal_ref.index.name = mensal.index.name = "data_ref"

    # ---------------- paineis trimestrais ----------------
    tri_idx = pd.date_range(inicio, fim, freq="QS")
    por_tri = mensal_ref.index.to_period("Q")
    partes: dict[str, pd.Series] = {}
    for col in mensal_ref:
        if col.endswith("var_mensal"):  # variacao mensal nao tem sentido agregada por trimestre
            continue
        tipo = AGREGACAO_DERIVADA.get(col) or (tipo_serie[col] if col in tipo_serie.index else "nivel")
        agregada = _agregar_trimestre(mensal_ref[col], tipo, por_tri)
        agregada.index = agregada.index.to_timestamp()
        partes[col] = agregada
    tri_ref = pd.DataFrame(partes).reindex(tri_idx)
    for col in trimestrais:  # series trimestrais entram como publicadas
        tri_ref[col] = wide[col].reindex(tri_idx)
    ultimo_completo = fim - pd.DateOffset(months=2)  # o trimestre em curso nao entra
    tri_ref = tri_ref[tri_ref.index <= ultimo_completo]

    # o trimestre so e conhecido quando seu ultimo mes + defasagem cabe ate o fim do trimestre
    # seguinte: k = ceil(defasagem / 3) trimestres de deslocamento (0 se divulgado no proprio mes)
    k = {c: math.ceil(lag_mensal.get(c, lag_base.get(c, 0)) / 3) for c in tri_ref}
    tri_asof = pd.DataFrame({c: tri_ref[c].shift(k[c]) for c in tri_ref}, index=tri_ref.index)
    tri_ref.index.name = tri_asof.index.name = "data_ref"

    return Paineis(mensal, mensal_ref, tri_asof, tri_ref, lag_efetivo, k)


def construir_paineis(db_path: str = DB_PATH, saida: str = PROCESSED_DIR) -> Paineis:
    wide, meta = carregar_wide(db_path)
    p = montar_paineis(wide, meta)

    os.makedirs(saida, exist_ok=True)
    p.mensal.to_csv(os.path.join(saida, "painel_mensal.csv"))
    p.mensal_referencia.to_csv(os.path.join(saida, "painel_mensal_referencia.csv"))
    p.trimestral.to_csv(os.path.join(saida, "painel_trimestral.csv"))
    p.trimestral_referencia.to_csv(os.path.join(saida, "painel_trimestral_referencia.csv"))
    print(f"[SERIES] painel_mensal (as-of): {p.mensal.shape[0]} meses x {p.mensal.shape[1]} colunas "
          f"({p.mensal.index.min():%Y-%m} a {p.mensal.index.max():%Y-%m})")
    print(f"[SERIES] painel_trimestral (as-of): {p.trimestral.shape[0]} trimestres x {p.trimestral.shape[1]} colunas")
    return p
