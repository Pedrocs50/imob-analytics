"""Trabalhos da literatura usados na comparacao. Cada entrada traz so o que foi lido nas fontes (resumo/pagina indicada),
as condicoes do estudo e a ressalva de comparabilidade. Nada aqui e numero deste projeto."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Referencia:
    chave: str
    citacao: str
    tema: str  # "precificacao" | "series" | "incerteza" | "texto" | "preco de anuncio" | "avm"
    dados: str
    metodo: str
    resultado: str
    ressalva: str  # por que nao e diretamente comparavel
    url: str


REFERENCIAS: list[Referencia] = [
    Referencia(
        "neri2020", "Neri (2020). Modelo preditivo do preço de venda de apartamentos em Belo Horizonte utilizando Random Forest. UFMG, especialização em Estatística.",
        "precificacao", "Apartamentos de Belo Horizonte-MG; 18.796 observações (16.919 treino e 1.877 teste).", "Random Forest; separação aleatória 90% treino / 10% teste.",
        "Erro médio absoluto percentual de 8,21% e R² de 93,92% no teste.",
        "Divisão aleatória (não temporal); o R² é do preço total (a área explica boa parte da variação), enquanto este projeto reporta o R² do R$/m².",
        "https://repositorio.ufmg.br//bitstreams/da9afed9-5cf3-4589-be88-519119e1adab/download"),
    Referencia(
        "pereira2025", "Pereira (2025). Uso de aprendizado de máquina na modelagem preditiva dos valores de imóveis na cidade de João Pessoa. UFPB.",
        "precificacao", "Anúncios de imóveis de João Pessoa-PB obtidos por web scraping (número de observações não informado no resumo).",
        "Gradient boosting (modelo principal).", "R² de 85,42%, MAPE de 18,21% e RMSE de R$ 227.677 (nível de preço total); área foi a variável mais influente, seguida da razão quartos/área, vagas, coordenadas e aluguel médio do bairro.",
        "Não informa a divisão de validação no resumo; métrica sobre o preço total (RMSE em reais, não em R$/m²).",
        "https://repositorio.ufpb.br/jspui/handle/123456789/35103"),
    Referencia(
        "zilli2024", "Zilli & Bastos (2024). Avaliação em massa de apartamentos com Random Forest e Gradient Boosting: estudo de caso de Florianópolis. Rev. Dep. Geografia (USP).",
        "precificacao", "1.572 apartamentos da região central de Florianópolis-SC (de 8.694 registros), preços anunciados coletados por web scraping.",
        "Random Forest, Gradient Boosting e regressão linear clássica.", "Gradient boosting superou os demais em RMSE, MAE, MAPE, COD, PRD e R², com previsões até 30% mais precisas.",
        "O resumo não traz os valores absolutos das métricas por modelo; compara-se apenas a ordenação dos métodos.",
        "https://revistas.usp.br/rdg/article/view/212297"),
    Referencia(
        "bastos2024", "Bastos & Paquette (2024). On the uncertainty of real estate price predictions. REM Working Paper 0314-2024 (ISEG, Univ. de Lisboa).",
        "incerteza", "Preços de imóveis da Baía de São Francisco (EUA).", "Regressão quantílica conformal (conformal quantile regression).",
        "Os intervalos conformais têm cobertura exata; os de regressão quantílica não conformal cobrem muito menos que o nominal. Imóveis maiores, mais antigos, em bairros de renda baixa ou alta e há menos de um ano no mercado são mais difíceis de avaliar.",
        "Outro país, dados de venda e método conformal com calibração em dados separados; este projeto usa o erro relativo fora da amostra.",
        "https://rem.rc.iseg.ulisboa.pt/wps/pdf/REM_WP_0314_2024.pdf"),
    Referencia(
        "hansson2019", "Hansson & Rostami (2019). Time series forecasting of house prices: an evaluation of a support vector machine and a recurrent neural network with LSTM cells. Uppsala University (bachelor's thesis).",
        "series", "Preços mensais de casas na área de Estocolmo e em Uppsala, 2005 a início de 2019.", "LSTM e SVM; o melhor foi comparado a um ARIMA sazonal, previsão de 12 meses.",
        "O LSTM foi o melhor método de aprendizado de máquina, mas não previu tão bem quanto o ARIMA no horizonte de 12 meses.",
        "Outro mercado e outra frequência/periodo; trabalho de graduação.",
        "https://www.maklarstatistik.se/wp-content/uploads/Time-Series-Forecasting-of-House-Prices-FredrikHansson_JakoRostami_kandidatuppsats2019.pdf"),
    Referencia(
        "siami2018", "Siami-Namini & Siami Namin (2018). Forecasting economics and financial time series: ARIMA vs. LSTM. arXiv:1803.06386.",
        "series", "Séries econômicas e financeiras (não são preços de imóveis).", "ARIMA contra LSTM, comparação por RMSE.",
        "Relatam redução média do erro de 84% a 87% do LSTM em relação ao ARIMA.",
        "Séries financeiras/econômicas, muito mais ruidosas e longas que um índice imobiliário suavizado; o resumo não detalha a reestimação ao longo do tempo (walk-forward).",
        "https://arxiv.org/pdf/1803.06386"),
    Referencia(
        "texto", "Cambridge, Natural Language Engineering: \"Describe the house and I will tell you the price\"; e UConn: \"Information value of property description: a machine learning approach\" (2019).",
        "texto", "Anúncios e descrições textuais de imóveis.", "Vetorização de texto (TF-IDF, Word2Vec, BERT) combinada a atributos numéricos.",
        "O desempenho é melhor quando se combinam atributos textuais e numéricos; modelos de ML superam a regressão hedônica linear. O UConn estima que um desvio-padrão de qualidade não observada, medida pelo texto, corresponde a cerca de +15% no preço de venda.",
        "Lidos pelos resumos/páginas de busca; mercados e métodos diferentes. Este projeto usa só indicadores de palavras e remove preços e números do texto.",
        "https://www.cambridge.org/core/journals/natural-language-engineering/article/describe-the-house-and-i-will-tell-you-the-price-house-price-prediction-with-textual-description-data/807584C6B9D76F555DA61E220BF39F9B"),
    Referencia(
        "fipezap_desconto", "FipeZAP, via B3 Bora Investir: desconto médio entre o preço anunciado e o de fechamento.",
        "preco de anuncio", "Compras de imóveis no Brasil; série histórica de 12 anos, dado mais recente de set/2025.", "Levantamento de descontos em negociações.",
        "Desconto médio de 8% em todas as transações (média de 12 anos) e de 12% nas negociações com desconto; 68% das compras de set/2025 tiveram desconto.",
        "Fonte secundária (reportagem); é o desconto de negociação no Brasil, não de Jacareí.",
        "https://borainvestir.b3.com.br/objetivos-financeiros/organizar-as-contas/qual-o-desconto-medio-que-se-consegue-na-hora-de-fechar-a-compra-de-imovel/"),
    Referencia(
        "zillow", "Zillow: precisão do Zestimate (valor automatizado de imóveis nos EUA).",
        "avm", "Imóveis dos EUA, comparados ao preço final de venda.", "Modelo automatizado de avaliação (AVM) da própria empresa.",
        "Erro mediano de cerca de 1,8% nos imóveis à venda e de cerca de 7% nos que não estão à venda (varia ligeiramente com a atualização).",
        "O Zestimate de imóveis à venda usa o preço anunciado como entrada, o que este projeto não faz (o preço pedido é o alvo); o de imóveis fora do mercado é o mais comparável.",
        "https://www.zillow.com/zestimate"),
]


def por_tema(tema: str) -> list[Referencia]:
    return [r for r in REFERENCIAS if r.tema == tema]
