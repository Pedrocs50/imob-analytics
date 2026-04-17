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

### 1. Inicializar o banco

```bash
python -c "from src.database import Database; Database().setup()"
```

### 2. Coleta de imóveis (scraper)

```bash
python main.py scrape
```

### 3. Limpeza e processamento de imóveis

```bash
python main.py clean
```

### 4. Rodar scraper + cleaner em sequência

```bash
python main.py all
```

### 5. Processar o CSV FIPEZap SJC para SQLite

```bash
python -m src.macro.fipezap_processor
```

Isso lê `data/raw/fipezap_sjc.csv`, aplica limpeza e grava o resultado na tabela `fipezap_sjc` do banco.

### 6. Ingerir macro indicadores

```bash
python -m src.macro.ingest
```

Isso carrega séries BCB, IBGE e IPEA e persiste em `indicadores_macro`.

## Banco de dados

O banco SQLite contém as seguintes tabelas principais:

- `imoveis_raw`
- `imoveis_processados`
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
