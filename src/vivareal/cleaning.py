from __future__ import annotations

import json

import pandas as pd

from src.vivareal.config import SegmentoConfig

NUMERIC_COLUMNS = [
    "sale_price",
    "usable_area_m2",
    "bedrooms",
    "bathrooms",
    "suites",
    "parking_spaces",
    "yearly_iptu",
    "monthly_condo",
    "lat",
    "lon",
]

OUTPUT_COLUMNS = [
    "external_id",
    "segmento",
    "property_type",
    "em_condominio",
    "neighborhood",
    "lat",
    "lon",
    "usable_area_m2",
    "bedrooms",
    "bathrooms",
    "suites",
    "parking_spaces",
    "yearly_iptu",
    "iptu_informado",
    "monthly_condo",
    "condominio_informado",
    "amenities_count",
    "sale_price",
    "preco_m2",
    "created_at",
    "scraped_at",
]


def _contar_amenidades(valor) -> int:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return 0
    try:
        itens = json.loads(valor)
    except (TypeError, ValueError):
        return 0
    return len(itens) if isinstance(itens, list) else 0


def preparar_base(df: pd.DataFrame) -> pd.DataFrame:
    """Converte tipos e cria colunas derivadas. Nao remove linhas."""
    df = df.copy()
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("property_type", "usage_type", "neighborhood"):
        df[col] = df[col].astype("string").str.strip()

    # lat/lon = 0 e um valor de preenchimento, nao uma coordenada
    coordenada_invalida = (df["lat"] == 0) & (df["lon"] == 0)
    df.loc[coordenada_invalida, ["lat", "lon"]] = float("nan")

    df["amenities_count"] = df["amenities"].apply(_contar_amenidades)
    return df


def deduplicar(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Mantem, por external_id, o registro com scraped_at mais recente
    (desempate pelo maior id da tabela). Retorna (base, linhas removidas)."""
    antes = len(df)
    df = df.sort_values(["scraped_at", "id"]).drop_duplicates("external_id", keep="last")
    return df.reset_index(drop=True), antes - len(df)


def _registrar(log: list[tuple[str, int]], etapa: str, df: pd.DataFrame) -> None:
    log.append((etapa, len(df)))


def _anular_implausiveis(df: pd.DataFrame, coluna: str, faixa: tuple[float, float], rotulo: str) -> dict:
    """Transforma em ausente (NaN) os valores POSITIVOS fora da faixa. Zero e mantido
    ('sem taxa') e nenhuma linha e removida. Retorna o resumo do ajuste."""
    baixo, alto = faixa
    valores = df[coluna]
    abaixo = (valores > 0) & (valores < baixo)
    acima = valores > alto
    df.loc[abaixo | acima, coluna] = float("nan")
    return {
        "variavel": rotulo,
        "faixa plausivel": f"{baixo:g} a {alto:g}",
        "zeros mantidos (sem taxa)": int((valores == 0).sum()),
        "positivos abaixo do minimo -> ausente": int(abaixo.sum()),
        "acima do maximo -> ausente": int(acima.sum()),
        "informados ao final": int(df[coluna].notna().sum()),
    }


def limpar_segmento(
    df: pd.DataFrame,
    seg: SegmentoConfig,
    outlier_iqr_factor: float,
) -> tuple[pd.DataFrame, list[tuple[str, int]], list[dict]]:
    """Aplica as regras de limpeza de um segmento (df ja deduplicado e restrito a
    usage_type). Retorna o dataset, o log (etapa, linhas restantes) e os ajustes de
    valores que nao removem linhas (taxas implausiveis viram ausentes)."""
    log: list[tuple[str, int]] = []

    df = df[df["property_type"].isin(seg.property_types)].copy()
    _registrar(log, f"tipos {', '.join(seg.property_types)}", df)

    df = df.dropna(subset=["sale_price", "usable_area_m2"])
    df = df[df["usable_area_m2"] > 0]
    df["preco_m2"] = df["sale_price"] / df["usable_area_m2"]
    _registrar(log, "preco e area validos (>0)", df)

    df = df[df["sale_price"].between(*seg.sale_price)]
    _registrar(log, f"preco de venda entre {seg.sale_price[0]:,.0f} e {seg.sale_price[1]:,.0f}", df)

    df = df[df["usable_area_m2"].between(*seg.usable_area_m2)]
    _registrar(log, f"area util entre {seg.usable_area_m2[0]:g} e {seg.usable_area_m2[1]:g} m2", df)

    df = df[df["preco_m2"].between(*seg.preco_m2)]
    _registrar(log, f"preco_m2 entre {seg.preco_m2[0]:,.0f} e {seg.preco_m2[1]:,.0f}", df)

    # comodos ausentes sao mantidos; so removemos valores implausiveis
    df = df[
        (df["bedrooms"].isna() | (df["bedrooms"] <= seg.max_bedrooms))
        & (df["bathrooms"].isna() | (df["bathrooms"] <= seg.max_bathrooms))
        & (df["parking_spaces"].isna() | (df["parking_spaces"] <= seg.max_parking_spaces))
    ]
    _registrar(
        log,
        f"quartos <= {seg.max_bedrooms}, banheiros <= {seg.max_bathrooms}, vagas <= {seg.max_parking_spaces}",
        df,
    )

    grupo = df.groupby("property_type")["preco_m2"]
    q1 = grupo.transform("quantile", 0.25)
    q3 = grupo.transform("quantile", 0.75)
    iqr = q3 - q1
    df = df[df["preco_m2"].between(q1 - outlier_iqr_factor * iqr, q3 + outlier_iqr_factor * iqr)]
    _registrar(log, f"outliers de preco_m2 por IQR (fator {outlier_iqr_factor:g}) por property_type", df)

    ajustes = [
        _anular_implausiveis(df, "monthly_condo", seg.monthly_condo_range, "condominio mensal (R$)"),
        _anular_implausiveis(df, "yearly_iptu", seg.yearly_iptu_range, "IPTU anual (R$)"),
    ]
    # a ausencia da taxa carrega informacao (ex.: casas fora de condominio quase nunca tem
    # taxa), entao ela vira indicador em vez de ser imputada
    df["condominio_informado"] = df["monthly_condo"].notna().astype(int)
    df["iptu_informado"] = df["yearly_iptu"].notna().astype(int)

    df["segmento"] = seg.nome
    # em_condominio so faz sentido para casas (CONDOMINIUM = casa em condominio)
    if seg.nome == "casa":
        df["em_condominio"] = (df["property_type"] == "CONDOMINIUM").astype(int)
    else:
        df["em_condominio"] = pd.NA

    return df[OUTPUT_COLUMNS].reset_index(drop=True), log, ajustes
