from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

from src.database import Database, DB_PATH
from src.repository import DataRepository
from src.macro.catalogo_series import SERIES_BCB, SERIES_IBGE, SERIES_IPEA
from src.macro.clients import BCBClient, IBGESidraClient, IpeaDataClient


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("macro.ingest")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _agregar_mensal_registros(registros: list[dict], metodo: str = "last") -> list[dict]:
    if not registros:
        return []

    df = pd.DataFrame(registros).copy()
    df["data_ref"] = pd.to_datetime(df["data_ref"])
    df["mes"] = df["data_ref"].dt.to_period("M").dt.to_timestamp()
    df = df.sort_values("data_ref")

    if metodo == "mean":
        agg = df.groupby("mes", as_index=False)["valor"].mean()
    elif metodo == "sum":
        agg = df.groupby("mes", as_index=False)["valor"].sum()
    else:
        agg = df.groupby("mes", as_index=False).tail(1)[["mes", "valor"]]

    return [
        {"data_ref": row["mes"].date(), "valor": float(row["valor"])}
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Coleta BCB/SGS
# ---------------------------------------------------------------------------

def coletar_bcb() -> list[dict]:
    client = BCBClient()
    rows_out: list[dict] = []

    for serie in SERIES_BCB:
        if not serie.get("ativo", True):
            continue

        codigo = str(serie["codigo_serie"])
        logger.info("BCB: coletando serie %s (%s)", codigo, serie["nome_serie"])

        bruto = client.fetch_sgs(
            codigo_serie=codigo,
            data_inicial=serie.get("data_inicial"),
            data_final=serie.get("data_final"),
        )

        mensal = _agregar_mensal_registros(
            bruto,
            metodo=serie.get("agregacao_mensal", "last"),
        )

        for p in mensal:
            rows_out.append({
                "fonte":        serie["fonte"],
                "codigo_serie": codigo,
                "nome_serie":   serie["nome_serie"],
                "data_ref":     _month_start(p["data_ref"]).isoformat(),
                "valor":        p["valor"],
                "unidade":      serie.get("unidade"),
                "frequencia":   "M",
            })

        logger.info("BCB: %s pontos mensais preparados para %s", len(mensal), codigo)

    return rows_out


# ---------------------------------------------------------------------------
# Coleta IBGE/SIDRA
# ---------------------------------------------------------------------------

def coletar_ibge() -> list[dict]:
    client = IBGESidraClient()
    rows_out: list[dict] = []

    for serie in SERIES_IBGE:
        if not serie.get("ativo", True):
            continue

        paths = serie.get("sidra_paths") or [serie.get("sidra_path")]
        paths = [p for p in paths if p and "<PREENCHER" not in str(p)]

        if not paths:
            logger.warning("IBGE: serie %s sem sidra_path. Pulando.", serie["codigo_serie"])
            continue

        norm = []
        for sidra_path in paths:
            try:
                logger.info("IBGE: tentando %s -> %s", serie["codigo_serie"], sidra_path)
                raw  = client.fetch_sidra(sidra_path)
                norm = client.normalize_sidra_rows(raw, serie)

                if norm:
                    logger.info(
                        "IBGE: OK %s com %s pontos (%s)",
                        serie["codigo_serie"], len(norm), sidra_path,
                    )
                    break

            except Exception as e:
                logger.warning("IBGE: falha no path %s -> %s", sidra_path, e)

        if not norm:
            logger.warning("IBGE: nenhum path funcionou para %s", serie["codigo_serie"])
            continue

        for p in norm:
            rows_out.append({
                "fonte":        p["fonte"],
                "codigo_serie": p["codigo_serie"],
                "nome_serie":   p["nome_serie"],
                "data_ref":     _month_start(p["data_ref"]).isoformat(),
                "valor":        p["valor"],
                "unidade":      p.get("unidade"),
                "frequencia":   p.get("frequencia", serie.get("frequencia_origem", "M")),
            })

        logger.info("IBGE: %s pontos preparados para %s", len(norm), serie["codigo_serie"])

    return rows_out


# ---------------------------------------------------------------------------
# Coleta IpeaData  ← NOVO
# ---------------------------------------------------------------------------

def coletar_ipea() -> list[dict]:
    """
    Coleta séries do IpeaData via OData4 (sem token).
    Suporta lista de `codigos_fallback` por série.
    """
    client = IpeaDataClient()
    rows_out: list[dict] = []

    for serie in SERIES_IPEA:
        if not serie.get("ativo", True):
            continue

        # Monta lista: código principal + fallbacks
        codigos_tentar = [str(serie["codigo_serie"])] + [
            str(c) for c in serie.get("codigos_fallback", [])
        ]

        bruto: list[dict] = []
        codigo_usado: str | None = None

        for codigo in codigos_tentar:
            try:
                logger.info(
                    "IPEA: tentando %s (%s)", codigo, serie["nome_serie"]
                )
                bruto = client.fetch_serie(codigo)
                if bruto:
                    codigo_usado = codigo
                    break
                logger.warning("IPEA: serie %s retornou vazia, tentando fallback...", codigo)
            except Exception as e:
                logger.warning("IPEA: falha ao coletar %s -> %s", codigo, e)

        if not bruto or codigo_usado is None:
            logger.warning(
                "IPEA: todos os codigos falharam para '%s'. Pulando.",
                serie["nome_serie"],
            )
            continue

        mensal = _agregar_mensal_registros(
            bruto,
            metodo=serie.get("agregacao_mensal", "last"),
        )

        for p in mensal:
            rows_out.append({
                "fonte":        serie["fonte"],
                "codigo_serie": codigo_usado,   # registra o código que funcionou
                "nome_serie":   serie["nome_serie"],
                "data_ref":     _month_start(p["data_ref"]).isoformat(),
                "valor":        p["valor"],
                "unidade":      serie.get("unidade"),
                "frequencia":   "M",
            })

        logger.info(
            "IPEA: %s pontos mensais preparados para %s (codigo: %s)",
            len(mensal), serie["nome_serie"], codigo_usado,
        )

    return rows_out


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def executar_ingestao() -> None:
    db = Database(DB_PATH)
    db.setup()
    repo = DataRepository(db)

    if not hasattr(repo, "salvar_indicadores"):
        raise RuntimeError(
            "DataRepository sem metodo salvar_indicadores. Atualize src/repository.py primeiro."
        )

    dados: list[dict] = []
    dados.extend(coletar_bcb())   # Selic, IPCA, Dólar, IBC-Br
    dados.extend(coletar_ibge())  # Desemprego SP, Renda SP
    dados.extend(coletar_ipea())  # IGP-M, INCC-DI, ICC FGV

    if not dados:
        logger.warning("Nenhum dado macro preparado.")
        return

    repo.salvar_indicadores(dados)
    logger.info("Ingestao concluida. Total de linhas enviadas: %s", len(dados))


if __name__ == "__main__":
    executar_ingestao()