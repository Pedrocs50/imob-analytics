import pandas as pd
from src.database import Database


class DataRepository:
    """
    Responsabilidade única: toda comunicação com o banco de dados.
    O scraper e o cleaner não sabem que o banco existe — só falam com esta classe.
    Trocar SQLite por PostgreSQL no futuro = reescrever só esta classe.
    """

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # ESCRITA — dados brutos (usada pelo scraper)
    # ------------------------------------------------------------------

    def salvar_raw(self, dados: list[dict]) -> None:
        if not dados:
            return
        with self._db.get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO imoveis_raw
                    (segmento, preco_min_filtro, pagina, endereco, preco, area, quartos, banheiros, vagas)
                VALUES
                    (:segmento, :preco_min_filtro, :pagina, :endereco, :preco, :area, :quartos, :banheiros, :vagas)
                """,
                dados,
            )

    def marcar_pagina_coletada(self, segmento: str, preco_min: int, pagina: int) -> None:
        with self._db.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO progresso_scraping (segmento, preco_min_filtro, pagina) VALUES (?, ?, ?)",
                (segmento, preco_min, pagina),
            )

    # ------------------------------------------------------------------
    # LEITURA — controle de progresso (usada pelo scraper para retomar)
    # ------------------------------------------------------------------

    def pagina_ja_coletada(self, segmento: str, preco_min: int, pagina: int) -> bool:
        with self._db.get_connection() as conn:
            result = conn.execute(
                "SELECT 1 FROM progresso_scraping WHERE segmento=? AND preco_min_filtro=? AND pagina=?",
                (segmento, preco_min, pagina),
            ).fetchone()
            return result is not None

    def total_raw(self) -> int:
        with self._db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM imoveis_raw").fetchone()[0]

    # ------------------------------------------------------------------
    # LEITURA / ESCRITA — dados processados (usada pelo cleaner e análise)
    # ------------------------------------------------------------------

    def carregar_raw_como_df(self) -> pd.DataFrame:
        with self._db.get_connection() as conn:
            return pd.read_sql("SELECT * FROM imoveis_raw", conn)

    def salvar_processados(self, df: pd.DataFrame) -> None:
        colunas_finais = [
            "tipo", "endereco", "preco_venda", "area_m2",
            "qtd_quartos", "qtd_banheiros", "qtd_vagas", "preco_m2"
        ]
        df_final = df[colunas_finais].copy()

        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM imoveis_processados")
            df_final.to_sql("imoveis_processados", conn, if_exists="append", index=False)

    def carregar_processados_como_df(self) -> pd.DataFrame:
        with self._db.get_connection() as conn:
            return pd.read_sql("SELECT * FROM imoveis_processados", conn)

    def total_processados(self) -> int:
        with self._db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM imoveis_processados").fetchone()[0]

    def salvar_fipezap_sjc(self, df: pd.DataFrame) -> None:
        if df.empty:
            return

        colunas_finais = [
            "data",
            "preco_m2",
            "preco_m2_locacao_residencial",
            "var_mensal_venda_residencial",
            "var_mensal_locacao_residencial",
            "var_12m_venda_residencial",
            "var_12m_locacao_residencial",
            "rentabilidade_aluguel_residencial",
        ]
        df_final = df[colunas_finais].copy()

        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM fipezap_sjc")
            df_final.to_sql("fipezap_sjc", conn, if_exists="append", index=False)

    def carregar_fipezap_sjc_como_df(self) -> pd.DataFrame:
        with self._db.get_connection() as conn:
            return pd.read_sql("SELECT * FROM fipezap_sjc ORDER BY data", conn)

    def total_fipezap_sjc(self) -> int:
        with self._db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM fipezap_sjc").fetchone()[0]

    # ------------------------------------------------------------------
    # LEITURA / ESCRITA — indicadores macroeconômicos
    # ------------------------------------------------------------------

    def salvar_indicadores(self, dados: list[dict]) -> None:
        if not dados:
            return
        with self._db.get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO indicadores_macro
                    (fonte, codigo_serie, nome_serie, data_ref, valor, unidade, frequencia)
                VALUES
                    (:fonte, :codigo_serie, :nome_serie, :data_ref, :valor, :unidade, :frequencia)
                ON CONFLICT(fonte, codigo_serie, data_ref)
                DO UPDATE SET
                    nome_serie = excluded.nome_serie,
                    valor = excluded.valor,
                    unidade = excluded.unidade,
                    frequencia = excluded.frequencia
                """,
                dados,
            )

    def carregar_indicadores_como_df(self) -> pd.DataFrame:
        with self._db.get_connection() as conn:
            return pd.read_sql(
                """
                SELECT *
                FROM indicadores_macro
                ORDER BY data_ref, fonte, codigo_serie
                """,
                conn,
            )
