"""
main.py — Ponto de entrada único do projeto.

Uso:
    python main.py scrape    → coleta todos os imóveis (paralelo)
    python main.py clean     → limpa e processa os dados brutos
    python main.py all       → scrape + clean em sequência
"""

import sys
from src.database import Database, DB_PATH
from src.scraper import ScraperOrchestrator
from src.cleaner import DataCleaner


def cmd_scrape():
    orchestrator = ScraperOrchestrator(db_path=DB_PATH)
    orchestrator.executar()


def cmd_clean():
    db = Database(DB_PATH)
    db.setup()
    cleaner = DataCleaner(db)
    cleaner.executar()


def cmd_all():
    cmd_scrape()
    cmd_clean()


COMANDOS = {
    "scrape": cmd_scrape,
    "clean":  cmd_clean,
    "all":    cmd_all,
}


if __name__ == "__main__":
    # Guarda obrigatória para multiprocessing funcionar no Windows
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(1)

    COMANDOS[sys.argv[1]]()