"""
main.py - Ponto de entrada unico do projeto.

Uso:
    python main.py
    python main.py --menu
    python main.py scrape
    python main.py clean
    python main.py stats
    python main.py stats --gui
    python main.py stats --no-plot
    python main.py stats --tipo=distribuicao
    python main.py stats --tipo=scatter
    python main.py stats --tipo=pizza
    python main.py stats --tipo=correlacao
    python main.py stats --correlacao
    python main.py jacarei-train
    python main.py vivareal-prep
    python main.py series-coletar
    python main.py series-fipezap
    python main.py series-painel
    python main.py eda-series
    python main.py eda-vivareal
    python main.py reg-linear
    python main.py arima
    python main.py reg-geo
    python main.py arima-plus
    python main.py mapa-setores
    python main.py ajuste-gb
    python main.py lstm
    python main.py modelos-avancados
    python main.py projecao
    python main.py all
"""

import sys

from src.cleaner import DataCleaner
from src.database import DB_PATH, Database
from src.scraper import ScraperOrchestrator
from src.stats import ProcessedImoveisStatistics


def mostrar_menu():
    """Exibe menu interativo para escolher operacoes."""
    while True:
        print("\n" + "=" * 50)
        print("SISTEMA DE ANALISE IMOBILIARIA")
        print("=" * 50)
        print("1. Coletar imoveis (scrape)")
        print("2. Limpar e processar dados (clean)")
        print("3. Gerar estatisticas (stats)")
        print("4. Executar tudo (scrape + clean)")
        print("5. Estatisticas - Barras (padrao)")
        print("6. Estatisticas - Distribuicao (boxplot + histograma)")
        print("7. Estatisticas - Scatter (preco vs area)")
        print("8. Estatisticas - Pizza (proporcao tipos)")
        print("9. Estatisticas - Correlacao Macro (heatmap)")
        print("10. Treinar baseline VivaReal Jacarei")
        print("11. Gerar datasets limpos VivaReal (apartamento, casa, residencial)")
        print("0. Sair")
        print("=" * 50)

        try:
            opcao = input("Escolha uma opcao (0-11): ").strip()

            if opcao == "0":
                print("Ate logo!")
                break
            if opcao == "1":
                print("\nIniciando coleta de imoveis...")
                cmd_scrape()
            elif opcao == "2":
                print("\nIniciando limpeza de dados...")
                cmd_clean()
            elif opcao == "3":
                print("\nGerando estatisticas basicas...")
                cmd_stats_basico()
            elif opcao == "4":
                print("\nExecutando scrape + clean...")
                cmd_all()
            elif opcao == "5":
                print("\nGerando grafico de barras...")
                cmd_stats_tipo("barras")
            elif opcao == "6":
                print("\nGerando grafico de distribuicao...")
                cmd_stats_tipo("distribuicao")
            elif opcao == "7":
                print("\nGerando scatter plot...")
                cmd_stats_tipo("scatter")
            elif opcao == "8":
                print("\nGerando grafico de pizza...")
                cmd_stats_tipo("pizza")
            elif opcao == "9":
                print("\nGerando heatmap de correlacao macro...")
                cmd_stats_tipo("correlacao")
            elif opcao == "10":
                print("\nTreinando baseline de regressao para Jacarei...")
                cmd_jacarei_train()
            elif opcao == "11":
                print("\nGerando datasets limpos do VivaReal...")
                cmd_vivareal_prep()
            else:
                print("Opcao invalida! Digite um numero de 0 a 11.")

        except KeyboardInterrupt:
            print("\nOperacao cancelada pelo usuario!")
            break
        except Exception as exc:
            print(f"Erro: {exc}")

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

    salvar_png = "--png" in sys.argv or ("--no-plot" not in sys.argv and "--gui" not in sys.argv)
    mostrar_gui = "--gui" in sys.argv
    gerar_grafico = "--no-plot" not in sys.argv

    tipo_grafico = "barras"
    analisar_correlacao = "--correlacao" in sys.argv
    destino = None
    for arg in sys.argv:
        if arg.startswith("--tipo="):
            tipo_grafico = arg.split("=", 1)[1]
        elif arg.startswith("--destino="):
            destino = arg.split("=", 1)[1]

    stats.executar(
        gerar_grafico=gerar_grafico,
        salvar_png=salvar_png,
        mostrar_gui=mostrar_gui,
        tipo_grafico=tipo_grafico,
        analisar_correlacao=analisar_correlacao,
        destino=destino,
    )


def cmd_stats_basico():
    """Estatisticas basicas sem argumentos especiais."""
    db = Database(DB_PATH)
    db.setup()
    stats = ProcessedImoveisStatistics(db)
    stats.executar(gerar_grafico=True, salvar_png=True, mostrar_gui=False)


def cmd_stats_tipo(tipo: str):
    """Estatisticas com tipo especifico."""
    db = Database(DB_PATH)
    db.setup()
    stats = ProcessedImoveisStatistics(db)
    stats.executar(gerar_grafico=True, salvar_png=True, mostrar_gui=False, tipo_grafico=tipo)


def cmd_all():
    cmd_scrape()
    cmd_clean()


def cmd_jacarei_train():
    from src.pricing.random_forest import JacareiPricePerM2Model

    modelo = JacareiPricePerM2Model()
    modelo.train()


def cmd_vivareal_prep():
    from src.vivareal.build_dataset import construir_datasets

    construir_datasets()


def cmd_series_coletar():
    from src.timeseries.collect import coletar_series

    coletar_series()


def cmd_series_fipezap():
    from src.timeseries.fipezap import importar_fipezap

    importar_fipezap()


def cmd_series_painel():
    from src.timeseries import vazamento
    from src.timeseries.panel import carregar_wide, construir_paineis
    from src.timeseries.quality import escrever_relatorio, validar

    resultados = validar()
    escrever_relatorio(resultados)
    falhas = [r for r in resultados if r.falhas]
    print(f"[SERIES] validacao: {len(resultados)} series, {len(falhas)} com falha (ver reports/results/series_qualidade.md)")
    paineis = construir_paineis()

    wide, meta = carregar_wide()
    teste = vazamento.validar_vazamento(wide, meta, paineis)
    vazamento.escrever_relatorio(teste, meta, paineis)
    print(f"[SERIES] vazamento temporal: {len(teste['falhas'])} falha(s) (ver {vazamento.RELATORIO})")
    if teste["falhas"]:
        sys.exit(1)


def cmd_eda_series():
    from src.analysis.series_eda import executar

    executar()
    print("[EDA] series: relatorio em reports/results/eda_series.md; tabelas em reports/results/eda/; figuras em reports/figures/")


def cmd_eda_vivareal():
    from src.analysis.vivareal_eda import executar

    executar()
    print("[EDA] vivareal: relatorio em reports/results/eda_vivareal.md; tabelas em reports/results/eda/; figuras em reports/figures/")


def cmd_reg_linear():
    from src.pricing.linear_regression import executar

    executar()
    print("[REGRESSAO] relatorio em reports/results/regressao_linear.md; figuras em reports/figures/")


def cmd_arima():
    from src.timeseries.arima import executar

    executar()
    print("[ARIMA] relatorio em reports/results/arima.md; figuras em reports/figures/")


def cmd_reg_geo():
    from src.pricing.geo import executar

    executar()
    print("[GEO] relatorio em reports/results/regressao_geo.md; mapas em reports/figures/")


def cmd_arima_plus():
    from src.timeseries.arima_plus import executar

    executar()
    print("[ARIMA+] relatorio em reports/results/arima_plus.md")


def cmd_mapa_setores():
    from src.analysis.mapa_setores import executar

    executar()
    print("[MAPA] relatorio em reports/results/mapa_setores.md; mapa interativo em reports/figures/mapa_setores_interativo.html")


def cmd_ajuste_gb():
    from src.pricing.ajuste import executar

    executar()
    print("[AJUSTE] relatorio em reports/results/ajuste_gradient_boosting.md")


def cmd_lstm():
    from src.timeseries.lstm_painel import executar

    executar()
    print("[LSTM] relatorio em reports/results/lstm.md")


def cmd_modelos_avancados():
    from src.pricing.modelos_avancados import executar

    executar()
    print("[AVANCADOS] relatorio em reports/results/modelos_avancados.md")


def cmd_projecao():
    from src.pricing.projecao import executar

    executar()
    print("[PROJECAO] relatorio em reports/results/projecao_jacarei.md")


COMANDOS = {
    "scrape": cmd_scrape,
    "clean": cmd_clean,
    "stats": cmd_stats,
    "jacarei-train": cmd_jacarei_train,
    "vivareal-prep": cmd_vivareal_prep,
    "series-coletar": cmd_series_coletar,
    "series-fipezap": cmd_series_fipezap,
    "series-painel": cmd_series_painel,
    "eda-series": cmd_eda_series,
    "eda-vivareal": cmd_eda_vivareal,
    "reg-linear": cmd_reg_linear,
    "arima": cmd_arima,
    "reg-geo": cmd_reg_geo,
    "arima-plus": cmd_arima_plus,
    "mapa-setores": cmd_mapa_setores,
    "ajuste-gb": cmd_ajuste_gb,
    "lstm": cmd_lstm,
    "modelos-avancados": cmd_modelos_avancados,
    "projecao": cmd_projecao,
    "all": cmd_all,
}


if __name__ == "__main__":
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--menu"):
        mostrar_menu()
    elif len(sys.argv) >= 2 and sys.argv[1] in COMANDOS:
        COMANDOS[sys.argv[1]]()
    else:
        print(__doc__)
        sys.exit(1)
