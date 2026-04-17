# IC Mercado Imobiliário POO

Projeto de captura, limpeza e armazenamento de dados imobiliários e macroeconômicos em SQLite.

## Visão geral

Este repositório reúne:

- um scraper para coletar anúncios de imóveis do Zap
- um pipeline de limpeza para transformar dados brutos em dados processados
- um banco SQLite centralizado em `data/database/imoveis.db`
- ingestão de séries macroeconômicas (BCB, IBGE, IPEA)
- extração e persistência do dataset FIPEZap SJC no banco

## Estrutura principal

- `main.py` — ponto de entrada do projeto
- `src/database.py` — gerencia a conexão SQLite e cria o schema
- `src/repository.py` — abstrai leitura/escrita no banco
- `src/scraper.py` — coleta dados do Zap
- `src/cleaner.py` — limpa e processa os dados brutos do scraper
- `src/macro/fipezap_processor.py` — processa o CSV `data/raw/fipezap_sjc.csv` e salva no banco
- `src/macro/ingest.py` — ingestão de séries macroeconômicas em `indicadores_macro`

## Dados

- `data/raw/fipezap_sjc.csv` — CSV bruto FIPEZap SJC
- `data/processed/fipezap_sjc.csv` — versão processada do CSV
- `data/database/imoveis.db` — banco SQLite com tabelas de imóveis, indicadores e FIPEZap

## Dependências

Instale as dependências com:

```bash
python -m pip install -r requirements.txt
```

## Como rodar

### Menu Interativo (Recomendado)

```bash
python main.py          # ou python main.py --menu
```

Mostra um menu interativo com todas as opções disponíveis. Basta escolher o número da operação desejada.

### Comandos Diretos

```bash
python main.py scrape   # coleta todos os imóveis (paralelo)
python main.py clean    # limpa e processa os dados brutos
python main.py all      # scrape + clean em sequência
```

### Estatísticas

```bash
python main.py stats                    # Barras (padrão) - salva PNG
python main.py stats --gui             # Mostra gráfico na interface gráfica
python main.py stats --no-plot         # Apenas estatísticas, sem gráfico
python main.py stats --tipo=distribuicao  # Boxplot + histograma
python main.py stats --tipo=scatter    # Scatter plot preço vs área
python main.py stats --tipo=pizza      # Proporção dos tipos de imóvel
python main.py stats --tipo=correlacao # Heatmap de correlação com macro
python main.py stats --correlacao      # Análise numérica de correlação
```

```bash
python main.py stats                    # Barras (padrão) - salva PNG
python main.py stats --gui             # Mostra gráfico na interface gráfica
python main.py stats --no-plot         # Apenas estatísticas, sem gráfico
python main.py stats --tipo=distribuicao  # Boxplot + histograma
python main.py stats --tipo=scatter    # Scatter plot preço vs área
python main.py stats --tipo=pizza      # Proporção dos tipos de imóvel
python main.py stats --tipo=correlacao # Heatmap de correlação com macro
python main.py stats --correlacao      # Análise numérica de correlação
```

Isso calcula e imprime média, mediana e desvio padrão para `preco_venda` e `area_m2`, segmentado por tipo de imóvel (Apartamento, Casa, Terreno, etc.). Valores são arredondados para 2 casas decimais, com coluna de unidade (R$ ou m²). Os resultados são salvos na tabela `imoveis_estatisticas` do banco. Se matplotlib estiver instalado, gera diferentes tipos de gráficos conforme opção.

- estatísticas são geradas globalmente e por `tipo` (`Apartamento`, `Casa`, `Terreno`, etc.)
- o resultado é salvo em `imoveis_estatisticas` dentro de `data/database/imoveis.db`
- se `matplotlib` estiver instalado, o próprio comando `python main.py stats` tentará gerar gráficos em `data/processed`
- **correlação macroeconômica**: analisa correlação entre indicadores macro (dólar, inflação, atividade econômica, etc.) e gera heatmap visual. Use `--tipo=correlacao` para o gráfico e `--correlacao` para análise numérica

## Banco de dados

O banco SQLite contém as seguintes tabelas principais:

- `imoveis_raw`
- `imoveis_processados`
- `imoveis_estatisticas`
- `progresso_scraping`
- `indicadores_macro`
- `fipezap_sjc`

## Observações importantes

- O fluxo de scraping e limpeza está separado do processamento do CSV FIPEZap.
- O arquivo `src/repository.py` centraliza a lógica de escrita/leitura do banco.
- O arquivo `src/database.py` é responsável apenas pelo schema e pela conexão SQLite.
- O projeto está sendo organizado no Jira; isso é apenas para controle interno, não é preciso acessar o board para executar o código.

## Uso sugerido

1. instale dependências
2. faça o scrape com `python main.py scrape`
3. limpe os dados com `python main.py clean`
4. processe o FIPEZap com `python -m src.macro.fipezap_processor`
5. carregue indicadores macro com `python -m src.macro.ingest`

Assim você mantém todos os dados em `data/database/imoveis.db` e evita depender apenas de CSVs.
