"""
main.py — Ponto de entrada único do projeto.

Uso:
    python main.py              → mostra menu interativo
    python main.py --menu       → mostra menu interativo
    python main.py scrape       → coleta todos os imóveis (paralelo)
    python main.py clean        → limpa e processa os dados brutos
    python main.py stats        → gera estatísticas (salva PNG por padrão)
    python main.py stats --gui  → mostra gráfico na interface gráfica
    python main.py stats --no-plot → apenas estatísticas, sem gráfico
    python main.py stats --tipo=distribuicao → gráfico de distribuição
    python main.py stats --tipo=scatter → scatter plot preço vs área
    python main.py stats --tipo=pizza → gráfico de pizza dos tipos
    python main.py stats --tipo=correlacao → heatmap de correlação macro
    python main.py stats --correlacao → análise numérica de correlação
    python main.py all          → scrape + clean em sequência
"""

import sys
from src.database import Database, DB_PATH
from src.scraper import ScraperOrchestrator
from src.cleaner import DataCleaner
from src.stats import ProcessedImoveisStatistics


def mostrar_menu():
    """Exibe menu interativo para escolher operações."""
    while True:
        print("\n" + "="*50)
        print("🏠 SISTEMA DE ANÁLISE IMOBILIÁRIA")
        print("="*50)
        print("1. Coletar imóveis (scrape)")
        print("2. Limpar e processar dados (clean)")
        print("3. Gerar estatísticas (stats)")
        print("4. Executar tudo (scrape + clean)")
        print("5. Estatísticas - Barras (padrão)")
        print("6. Estatísticas - Distribuição (boxplot + histograma)")
        print("7. Estatísticas - Scatter (preço vs área)")
        print("8. Estatísticas - Pizza (proporção tipos)")
        print("9. Estatísticas - Correlação Macro (heatmap)")
        print("0. Sair")
        print("="*50)

        try:
            opcao = input("Escolha uma opção (0-9): ").strip()

            if opcao == "0":
                print("Até logo!")
                break
            elif opcao == "1":
                print("\nIniciando coleta de imóveis...")
                cmd_scrape()
            elif opcao == "2":
                print("\nIniciando limpeza de dados...")
                cmd_clean()
            elif opcao == "3":
                print("\nGerando estatísticas básicas...")
                cmd_stats_basico()
            elif opcao == "4":
                print("\nExecutando scrape + clean...")
                cmd_all()
            elif opcao == "5":
                print("\nGerando gráfico de barras...")
                cmd_stats_tipo("barras")
            elif opcao == "6":
                print("\nGerando gráfico de distribuição...")
                cmd_stats_tipo("distribuicao")
            elif opcao == "7":
                print("\nGerando scatter plot...")
                cmd_stats_tipo("scatter")
            elif opcao == "8":
                print("\nGerando gráfico de pizza...")
                cmd_stats_tipo("pizza")
            elif opcao == "9":
                print("\nGerando heatmap de correlação macro...")
                cmd_stats_tipo("correlacao")
            else:
                print("Opção inválida! Digite um número de 0 a 9.")

        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário!")
            break
        except Exception as e:
            print(f"Erro: {e}")

        input("\nPressione Enter para continuar...")


def cmd_scrape():
    orchestrator = ScraperOrchestrator(db_path=DB_PATH)
    orchestrator.executar()


def cmd_clean():
    db = Database(DB_PATH)
    db.setup()
    cleaner = DataCleaner(db)
    cleaner.executar()


def cmd_stats():
    db = Database(DB_PATH)
    db.setup()
    stats = ProcessedImoveisStatistics(db)

    # Argumentos: stats [--png] [--gui] [--no-plot] [--tipo=TIPO]
    salvar_png = "--png" in sys.argv or ("--no-plot" not in sys.argv and "--gui" not in sys.argv)
    mostrar_gui = "--gui" in sys.argv
    gerar_grafico = not ("--no-plot" in sys.argv)

    # Extrair tipo de gráfico
    tipo_grafico = "barras"
    analisar_correlacao = "--correlacao" in sys.argv
    destino = None
    for arg in sys.argv:
        if arg.startswith("--tipo="):
            tipo_grafico = arg.split("=", 1)[1]
        elif arg.startswith("--destino="):
            destino = arg.split("=", 1)[1]

    stats.executar(gerar_grafico=gerar_grafico, salvar_png=salvar_png, mostrar_gui=mostrar_gui, tipo_grafico=tipo_grafico, analisar_correlacao=analisar_correlacao, destino=destino)


def cmd_stats_basico():
    """Estatísticas básicas sem argumentos especiais."""
    db = Database(DB_PATH)
    db.setup()
    stats = ProcessedImoveisStatistics(db)
    stats.executar(gerar_grafico=True, salvar_png=True, mostrar_gui=False)


def cmd_stats_tipo(tipo: str):
    """Estatísticas com tipo específico."""
    db = Database(DB_PATH)
    db.setup()
    stats = ProcessedImoveisStatistics(db)
    stats.executar(gerar_grafico=True, salvar_png=True, mostrar_gui=False, tipo_grafico=tipo)


def cmd_all():
    cmd_scrape()
    cmd_clean()


COMANDOS = {
    "scrape": cmd_scrape,
    "clean":  cmd_clean,
    "stats":  cmd_stats,
    "all":    cmd_all,
}


if __name__ == "__main__":
    # Se não há argumentos ou --menu, mostra o menu interativo
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--menu"):
        mostrar_menu()
    # Se há argumentos e é um comando válido, executa normalmente
    elif len(sys.argv) >= 2 and sys.argv[1] in COMANDOS:
        COMANDOS[sys.argv[1]]()
    # Caso contrário, mostra ajuda
    else:
        print(__doc__)
        sys.exit(1)