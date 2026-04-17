import sqlite3
import os


DB_PATH = os.path.join('data', 'database', 'imoveis.db')


class Database:
    """
    Responsabilidade única: gerenciar conexão e schema do SQLite.
    Nada mais — não sabe de scraping, não sabe de limpeza.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        # WAL permite que 2 processos escrevam sem bloquear um ao outro
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def setup(self) -> None:
        """Cria as tabelas se ainda não existirem."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS imoveis_raw (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    segmento         TEXT,
                    preco_min_filtro INTEGER,
                    pagina           INTEGER,
                    endereco         TEXT,
                    preco            TEXT,
                    area             TEXT,
                    quartos          TEXT,
                    banheiros        TEXT,
                    vagas            TEXT,
                    coletado_em      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS imoveis_processados (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo            TEXT,
                    endereco        TEXT,
                    preco_venda     REAL,
                    area_m2         REAL,
                    qtd_quartos     INTEGER,
                    qtd_banheiros   INTEGER,
                    qtd_vagas       INTEGER,
                    preco_m2        REAL,
                    processado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabela de controle: qual (segmento, preco_min, pagina) já foi coletado
                CREATE TABLE IF NOT EXISTS progresso_scraping (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    segmento         TEXT,
                    preco_min_filtro INTEGER,
                    pagina           INTEGER,
                    UNIQUE(segmento, preco_min_filtro, pagina)
                );

                -- Indicadores macroeconômicos externos (BCB/IBGE/FGV etc.)
                CREATE TABLE IF NOT EXISTS indicadores_macro (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    fonte       TEXT NOT NULL,
                    codigo_serie TEXT NOT NULL,
                    nome_serie  TEXT,
                    data_ref    DATE NOT NULL,
                    valor       REAL,
                    unidade     TEXT,
                    frequencia  TEXT DEFAULT 'M',
                    coletado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(fonte, codigo_serie, data_ref)
                );

                CREATE INDEX IF NOT EXISTS idx_indicadores_data_ref
                    ON indicadores_macro(data_ref);

                CREATE TABLE IF NOT EXISTS fipezap_sjc (
                    id                                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    data                                DATE NOT NULL,
                    preco_m2                            REAL,
                    preco_m2_locacao_residencial        REAL,
                    var_mensal_venda_residencial        REAL,
                    var_mensal_locacao_residencial      REAL,
                    var_12m_venda_residencial           REAL,
                    var_12m_locacao_residencial         REAL,
                    rentabilidade_aluguel_residencial    REAL,
                    processado_em                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(data)
                );

                -- Recriar tabela imoveis_estatisticas com nova estrutura
                DROP TABLE IF EXISTS imoveis_estatisticas;
                CREATE TABLE imoveis_estatisticas (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo            TEXT NOT NULL,
                    campo           TEXT NOT NULL,
                    unidade         TEXT,
                    contagem        INTEGER,
                    media           REAL,
                    mediana         REAL,
                    desvio_padrao   REAL,
                    calculado_em    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tipo, campo)
                );

                CREATE INDEX IF NOT EXISTS idx_imoveis_estatisticas_tipo
                    ON imoveis_estatisticas(tipo);

                CREATE INDEX IF NOT EXISTS idx_indicadores_fonte_serie
                    ON indicadores_macro(fonte, codigo_serie);
            """)
        print(f"[DB] Banco pronto em: {self.db_path}")
