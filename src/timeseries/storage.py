from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Iterable, Iterator

from src.timeseries.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS series (
    id              TEXT PRIMARY KEY,
    fonte           TEXT NOT NULL,
    codigo          TEXT,
    nome            TEXT NOT NULL,
    unidade         TEXT,
    tipo            TEXT NOT NULL,       -- taxa | indice | nivel | saldo
    frequencia      TEXT NOT NULL,       -- M | Q
    defasagem_meses INTEGER NOT NULL DEFAULT 0,
    escopo          TEXT                 -- ex.: cidade, no caso do FipeZAP
);

CREATE TABLE IF NOT EXISTS observacoes (
    serie_id    TEXT NOT NULL REFERENCES series(id),
    data_ref    TEXT NOT NULL,           -- primeiro dia do periodo (AAAA-MM-DD)
    valor       REAL NOT NULL,
    coletado_em TEXT NOT NULL,
    PRIMARY KEY (serie_id, data_ref)
);

CREATE TABLE IF NOT EXISTS coletas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    serie_id     TEXT NOT NULL,
    coletado_em  TEXT NOT NULL,
    n_pontos     INTEGER NOT NULL,
    status       TEXT NOT NULL,          -- ok | erro
    erro         TEXT,
    arquivo_bruto TEXT
);
"""


@contextmanager
def conectar(db_path: str = DB_PATH) -> Iterator[sqlite3.Connection]:
    pasta = os.path.dirname(db_path)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    conexao = sqlite3.connect(db_path)
    try:
        conexao.executescript(SCHEMA)
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def registrar_serie(conexao: sqlite3.Connection, meta: dict) -> None:
    conexao.execute(
        """
        INSERT INTO series (id, fonte, codigo, nome, unidade, tipo, frequencia, defasagem_meses, escopo)
        VALUES (:id, :fonte, :codigo, :nome, :unidade, :tipo, :frequencia, :defasagem_meses, :escopo)
        ON CONFLICT(id) DO UPDATE SET
            fonte=excluded.fonte, codigo=excluded.codigo, nome=excluded.nome,
            unidade=excluded.unidade, tipo=excluded.tipo, frequencia=excluded.frequencia,
            defasagem_meses=excluded.defasagem_meses, escopo=excluded.escopo
        """,
        {"codigo": None, "unidade": None, "defasagem_meses": 0, "escopo": None, **meta},
    )


def gravar_observacoes(
    conexao: sqlite3.Connection, serie_id: str, pontos: Iterable[tuple[date, float]]
) -> int:
    """Substitui a serie inteira pelo que acabou de ser coletado: a fonte devolve o
    historico completo, entao pontos antigos que sairam do escopo ou foram revisados
    nao podem sobrar. A resposta original continua guardada em data/raw."""
    pontos = list(pontos)
    if pontos:  # so apaga se ha dado novo para colocar no lugar
        conexao.execute("DELETE FROM observacoes WHERE serie_id = ?", (serie_id,))
    agora = _agora()
    linhas = [(serie_id, data.isoformat(), float(valor), agora) for data, valor in pontos]
    conexao.executemany(
        """
        INSERT INTO observacoes (serie_id, data_ref, valor, coletado_em) VALUES (?, ?, ?, ?)
        ON CONFLICT(serie_id, data_ref) DO UPDATE SET
            valor=excluded.valor, coletado_em=excluded.coletado_em
        """,
        linhas,
    )
    return len(linhas)


def registrar_coleta(
    conexao: sqlite3.Connection,
    serie_id: str,
    n_pontos: int,
    status: str,
    erro: str | None = None,
    arquivo_bruto: str | None = None,
) -> None:
    conexao.execute(
        "INSERT INTO coletas (serie_id, coletado_em, n_pontos, status, erro, arquivo_bruto) VALUES (?,?,?,?,?,?)",
        (serie_id, _agora(), n_pontos, status, erro, arquivo_bruto),
    )
