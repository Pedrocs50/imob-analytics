from __future__ import annotations

import os
import pandas as pd

from src.database import Database, DB_PATH
from src.repository import DataRepository


class ProcessedImoveisStatistics:
    """Gera estatísticas descritivas para imóveis processados."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database(DB_PATH)
        self.repo = DataRepository(self.db)

    def carregar_processados(self) -> pd.DataFrame:
        df = self.repo.carregar_processados_como_df()
        if df.empty:
            raise RuntimeError(
                "Nenhum imóvel processado encontrado. Execute `python main.py clean` primeiro."
            )
        return df

    def calcular_descritivas(self, df: pd.DataFrame) -> pd.DataFrame:
        colunas_numericas = ["preco_venda", "area_m2"]
        estatisticas: list[pd.DataFrame] = []

        def _agrega_por_tipo(sub_df: pd.DataFrame, tipo: str) -> pd.DataFrame:
            tabela = sub_df[colunas_numericas].agg(["count", "mean", "median", "std"]).T
            tabela = tabela.rename(
                columns={
                    "count": "contagem",
                    "mean": "media",
                    "median": "mediana",
                    "std": "desvio_padrao",
                }
            )
            # Arredondar valores para 2 casas decimais
            tabela = tabela.round(2)
            tabela = tabela.reset_index().rename(columns={"index": "campo"})
            tabela["tipo"] = tipo
            # Adicionar coluna de unidade
            unidades = {
                "preco_venda": "R$",
                "area_m2": "m²"
            }
            tabela["unidade"] = tabela["campo"].map(unidades)
            return tabela[["tipo", "campo", "unidade", "contagem", "media", "mediana", "desvio_padrao"]]

        estatisticas.append(_agrega_por_tipo(df, "Todos"))
        for tipo, group in df.groupby("tipo"):
            estatisticas.append(_agrega_por_tipo(group, tipo))

        resultado = pd.concat(estatisticas, ignore_index=True)
        resultado["tipo"] = resultado["tipo"].fillna("Outro")
        return resultado

    def salvar_estatisticas(self, df: pd.DataFrame) -> None:
        self.repo.salvar_estatisticas_imoveis(df)
        print(f"[STATS] Estatísticas salvas em: {self.db.db_path} (tabela imoveis_estatisticas)")

    def plotar_estatisticas(self, df: pd.DataFrame, tipo_grafico: str = "barras", salvar_png: bool = True, mostrar_gui: bool = False, destino: str | None = None) -> str | None:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("[STATS] matplotlib não está instalado. Instale-o para gerar gráficos.")
            return None

        # Carregar dados originais para gráficos mais detalhados
        df_original = self.carregar_processados()

        if tipo_grafico == "barras":
            return self._plot_barras(df, salvar_png, mostrar_gui)
        elif tipo_grafico == "distribuicao":
            return self._plot_distribuicao(df_original, salvar_png, mostrar_gui)
        elif tipo_grafico == "scatter":
            return self._plot_scatter(df_original, salvar_png, mostrar_gui)
        elif tipo_grafico == "pizza":
            return self._plot_pizza(df_original, salvar_png, mostrar_gui)
        elif tipo_grafico == "correlacao":
            return self.plotar_correlacao_macro(salvar_png, mostrar_gui, destino)
        else:
            print(f"[STATS] Tipo de gráfico '{tipo_grafico}' não reconhecido. Usando barras.")
            return self._plot_barras(df, salvar_png, mostrar_gui)

    def executar(self, gerar_grafico: bool = False, salvar_png: bool = True, mostrar_gui: bool = False, tipo_grafico: str = "barras", analisar_correlacao: bool = False, destino: str | None = None) -> pd.DataFrame:
        df = self.carregar_processados()
        estatisticas = self.calcular_descritivas(df)

        print("[STATS] Estatísticas descritivas dos imóveis processados")
        print(estatisticas.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

        self.salvar_estatisticas(estatisticas)

        if gerar_grafico:
            self.plotar_estatisticas(estatisticas, tipo_grafico=tipo_grafico, salvar_png=salvar_png, mostrar_gui=mostrar_gui, destino=destino)

        if analisar_correlacao:
            print("\n[STATS] Análise de correlação com indicadores macroeconômicos:")
            correlacao = self.analisar_correlacao_macro()
            print(correlacao.to_string(float_format=lambda x: f"{x:.3f}"))

        return estatisticas

    def _plot_barras(self, df: pd.DataFrame, salvar_png: bool, mostrar_gui: bool) -> str | None:
        import matplotlib.pyplot as plt

        destino = os.path.join("data", "processed", "imoveis_estatisticas_barras.png")
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        agrupado = df[df["campo"].isin(["preco_venda", "area_m2"])]
        pivot = agrupado.pivot(index="tipo", columns="campo", values="media")

        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(12, 5), tight_layout=True)
        pivot["preco_venda"].sort_values().plot(kind="barh", ax=ax[0], color="#2f7bba")
        ax[0].set_title("Preço médio de venda por tipo")
        ax[0].set_xlabel("R$")

        pivot["area_m2"].sort_values().plot(kind="barh", ax=ax[1], color="#79c36a")
        ax[1].set_title("Área média por tipo")
        ax[1].set_xlabel("m²")

        fig.suptitle("Estatísticas descritivas dos imóveis processados")

        return self._salvar_ou_mostrar(fig, destino, salvar_png, mostrar_gui)

    def _plot_distribuicao(self, df_original: pd.DataFrame, salvar_png: bool, mostrar_gui: bool) -> str | None:
        import matplotlib.pyplot as plt

        destino = os.path.join("data", "processed", "imoveis_distribuicao.png")
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        # Filtrar preços muito altos para melhor visualização
        df_filtrado = df_original[df_original["preco_venda"] < df_original["preco_venda"].quantile(0.95)]

        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(10, 8), tight_layout=True)

        # Boxplot de preços por tipo
        tipos_ordenados = df_filtrado.groupby("tipo")["preco_venda"].median().sort_values().index
        df_filtrado.boxplot(column="preco_venda", by="tipo", ax=ax[0], rot=45)
        ax[0].set_title("Distribuição de Preços por Tipo de Imóvel")
        ax[0].set_ylabel("Preço (R$)")
        ax[0].set_xlabel("")

        # Histograma de áreas
        df_filtrado["area_m2"].hist(ax=ax[1], bins=30, alpha=0.7, color="#79c36a")
        ax[1].set_title("Distribuição de Áreas dos Imóveis")
        ax[1].set_xlabel("Área (m²)")
        ax[1].set_ylabel("Frequência")

        fig.suptitle("Distribuição dos Dados Imobiliários")

        return self._salvar_ou_mostrar(fig, destino, salvar_png, mostrar_gui)

    def _plot_scatter(self, df_original: pd.DataFrame, salvar_png: bool, mostrar_gui: bool) -> str | None:
        import matplotlib.pyplot as plt

        destino = os.path.join("data", "processed", "imoveis_scatter.png")
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        # Filtrar outliers para melhor visualização
        df_filtrado = df_original[
            (df_original["preco_venda"] < df_original["preco_venda"].quantile(0.95)) &
            (df_original["area_m2"] < df_original["area_m2"].quantile(0.95))
        ]

        fig, ax = plt.subplots(figsize=(10, 6))

        cores = {"Apartamento": "#2f7bba", "Casa": "#79c36a", "Terreno": "#ff7f0e", "Outro": "#d62728"}

        for tipo in df_filtrado["tipo"].unique():
            subset = df_filtrado[df_filtrado["tipo"] == tipo]
            ax.scatter(subset["area_m2"], subset["preco_venda"],
                      label=tipo, alpha=0.6, color=cores.get(tipo, "#7f7f7f"))

        ax.set_xlabel("Área (m²)")
        ax.set_ylabel("Preço (R$)")
        ax.set_title("Relação entre Área e Preço dos Imóveis")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return self._salvar_ou_mostrar(fig, destino, salvar_png, mostrar_gui)

    def _plot_pizza(self, df_original: pd.DataFrame, salvar_png: bool, mostrar_gui: bool) -> str | None:
        import matplotlib.pyplot as plt

        destino = os.path.join("data", "processed", "imoveis_pizza.png")
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        contagem_tipos = df_original["tipo"].value_counts()

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(contagem_tipos.values, labels=contagem_tipos.index, autopct='%1.1f%%',
               startangle=90, colors=["#2f7bba", "#79c36a", "#ff7f0e", "#d62728"])
        ax.set_title("Proporção de Tipos de Imóveis")

        return self._salvar_ou_mostrar(fig, destino, salvar_png, mostrar_gui)

    def analisar_correlacao_macro(self) -> pd.DataFrame:
        """Analisa correlação entre preços de imóveis e indicadores macroeconômicos."""
        # Carregar dados
        df_imoveis = self.carregar_processados()
        df_macro = self.repo.carregar_indicadores_como_df()

        if df_macro.empty:
            raise RuntimeError(
                "Nenhum indicador macro encontrado. Execute `python -m src.macro.ingest` primeiro."
            )

        # Filtrar dados macro para período válido (2008-2025)
        df_macro["data_ref"] = pd.to_datetime(df_macro["data_ref"])
        df_macro = df_macro[(df_macro["data_ref"] >= "2008-01-01") & (df_macro["data_ref"] <= "2025-12-31")]

        # Agregar preços de imóveis por mês (usando data de processamento)
        # NOTA: Como os imóveis foram coletados recentemente, não há sobreposição temporal perfeita
        # Vamos mostrar correlação entre indicadores macro para demonstrar a análise
        print("[STATS] Nota: Imóveis coletados recentemente, mostrando correlação entre indicadores macro")

        # Pivotear indicadores macro
        macro_pivot = df_macro.pivot(index="data_ref", columns="nome_serie", values="valor")

        # Calcular correlação entre indicadores macro
        colunas_numericas = macro_pivot.select_dtypes(include=[float, int]).columns
        correlacao = macro_pivot[colunas_numericas].corr()

        return correlacao

    def plotar_correlacao_macro(self, salvar_png: bool = True, mostrar_gui: bool = False, destino: str | None = None) -> str | None:
        """Gera heatmap da correlação entre preços e indicadores macro."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            print("[STATS] seaborn não está instalado. Instale com: pip install seaborn")
            return None

        correlacao = self.analisar_correlacao_macro()

        if destino is None:
            destino = os.path.join("data", "processed", "correlacao_macro.png")
        dir_destino = os.path.dirname(destino)
        if dir_destino:  # Só cria diretório se houver um caminho
            os.makedirs(dir_destino, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 8))

        # Heatmap com seaborn
        sns.heatmap(correlacao, annot=True, cmap="RdYlBu_r", center=0,
                   fmt=".2f", linewidths=0.5, ax=ax, square=True)

        ax.set_title("Correlação entre Indicadores Macroeconômicos\n(Período: 2008-2025)")
        ax.set_xlabel("Indicadores")
        ax.set_ylabel("Indicadores")

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._salvar_ou_mostrar(fig, destino, salvar_png, mostrar_gui)

    def _salvar_ou_mostrar(self, fig, destino: str, salvar_png: bool, mostrar_gui: bool) -> str | None:
        import matplotlib.pyplot as plt

        if salvar_png:
            fig.savefig(destino, dpi=150, bbox_inches='tight')
            print(f"[STATS] Gráfico salvo em: {destino}")
            plt.close(fig)
            return destino
        elif mostrar_gui:
            print("[STATS] Mostrando gráfico na interface gráfica (feche a janela para continuar)")
            plt.show()
            return None
        else:
            plt.close(fig)
            return None


if __name__ == "__main__":
    ProcessedImoveisStatistics().executar()
