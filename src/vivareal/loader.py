from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd


def carregar_listings(db_path: str) -> pd.DataFrame:
    """Le a tabela `listings` do banco original em modo somente leitura."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {db_path}. Coloque o banco VivaReal nesse caminho."
        )

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        return pd.read_sql_query("SELECT * FROM listings", connection)
    finally:
        connection.close()
