# IC Mercado Imobiliario (Jacarei-SP)

Iniciacao cientifica sobre analise e previsao do mercado imobiliario, com foco
inicial em Jacarei-SP. O projeto compara tecnicas de previsao aplicadas ao setor
(regressao, ARIMA e redes neurais LSTM) usando dados abertos (anuncios, FipeZAP,
IBGE, BCB, IPEA).

## Estado do projeto

| Meta | Descricao | Estado |
|---|---|---|
| 1 | Mapeamento e coleta de dados publicos | Atingida |
| 2 | Tratamento, padronizacao e organizacao | Atingida (VivaReal e series temporais) |
| 3 | Estatistica descritiva e exploratoria | Atingida |
| 4 | Regressao linear multipla e ARIMA | Atingida para precos (demanda nao coberta) |
| 5 | LSTM multivariado | Atingida (sem preditores macro) |
| 6 | Comparacao ARIMA x LSTM (RMSE, MAE, R2) | Atingida com ressalvas |
| 7 | Sensibilidade e relevancia das variaveis | Nao iniciada |
| 8 | Visualizacoes interativas | Nao iniciada |
| 9 | Relatorios analiticos automaticos | Nao iniciada |

Detalhes e proximas etapas em [`docs/METAS.md`](docs/METAS.md).

## Duas trilhas, separadas pelo tipo de dado

| Trilha | Dado | Modelos | Estado |
|---|---|---|---|
| **Precificacao** (transversal) | Anuncios VivaReal de Jacarei, um unico snapshot (marco/2026) | Regressao linear, Random Forest | Datasets limpos prontos; so existe o Random Forest baseline |
| **Series temporais** | FipeZAP (nacional e Sao Jose dos Campos) + variaveis macro | ARIMA/ARIMAX, LSTM | Base, paineis, exploracao, ARIMA, ARIMAX e LSTM em painel prontos |

O snapshot do VivaReal **nao e uma serie temporal**: nao permite treinar ARIMA ou
LSTM sobre os precos dos anuncios. A trilha temporal usa o FipeZAP, cujos precos sao
medias moveis trimestrais, e nao ha serie especifica de Jacarei.

## Estrutura do projeto

```text
main.py                     ponto de entrada (comandos e menu)
src/
  scraper.py, cleaner.py, database.py, repository.py, stats.py, macro/
                            coleta e fluxo legado (nao usar o macro/ legado para modelar)
  vivareal/                 carga e limpeza da base do orientador por segmento
  pricing/                  modelos de precificacao (Random Forest baseline)
  timeseries/               FipeZAP + macro: catalogo, coleta por API, banco, validacao,
                            paineis "as-of" e teste de vazamento temporal
  analysis/                 analise exploratoria (series e VivaReal)
  evaluation/               metricas e comparacao de modelos (a preencher)
data/
  raw/                      dados brutos de fontes publicas (nunca sobrescrever)
  models/                   metricas e figuras do baseline (o .pkl nao e versionado)
reports/
  results/                  relatorios e tabelas geradas
  figures/                  figuras das analises
sql/queries/                consultas SQL de apoio
docs/                       metas, auditoria, series temporais e analise exploratoria
```

## Dados: o que esta e o que nao esta no repositorio

O repositorio e **publico**, entao alguns dados ficam de fora de proposito.

| Dado | No git? | Como obter |
|---|---|---|
| Excel do FipeZAP (`data/raw/fipezap-serieshistoricas (2).xlsx`) | Sim | Download manual em [fipe.org.br](https://www.fipe.org.br/pt-br/indices/fipezap/) |
| Recorte de Jacarei da malha de setores do IBGE (`data/raw/ibge/jacarei_setores_2022.gpkg`, 0,9 MB) | Sim | Gerado da malha completa de SP (`SP_setores_CD2022`, 335 MB, **nao versionada**), baixada de [geoftp.ibge.gov.br](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/) e salva em `data/raw/SP_setores_CD2022/` |
| Respostas das APIs (`data/raw/macro/`) | Sim | `python main.py series-coletar` |
| **Base VivaReal do orientador** | **Nao** | Pedir ao orientador e salvar em `data/raw/vivareal_jacarei/vivareal_jacarei_20260324.db`. Contem nome, telefone, WhatsApp e CRECI de anunciantes. |
| `data/database/*.db` (banco do scraper e `series_temporais.db`) | Nao | Gerados pelos comandos abaixo |
| `data/processed/` (datasets e paineis) | Nao | Gerados pelos comandos abaixo |
| Modelo treinado (`*.pkl`) | Nao | `python main.py jacarei-train` |

## Instalacao

Requer Python 3.11 ou superior (desenvolvido com 3.14).

```bash
python -m venv venv
python -m pip install -r requirements.txt
```

Ative o ambiente virtual antes (`venv\Scripts\activate` no Windows). O scraper
(`scrape`) tambem exige o Chrome for Testing e o chromedriver em `scripts/`, que nao
sao versionados.

## Como rodar

Ordem sugerida do pipeline atual:

| Comando | O que faz |
|---|---|
| `python main.py vivareal-prep` | Gera `apartamento.csv`, `casa.csv` e `residencial.csv` em `data/processed/vivareal/` (1 registro por anuncio, limpeza por segmento, taxas de condominio/IPTU implausiveis viram ausentes) e o relatorio `reports/results/vivareal_limpeza.md`. Le o banco original so em modo leitura. |
| `python main.py series-coletar` | Coleta 14 series macro (BCB, IPEA, IBGE) pelas APIs publicas. |
| `python main.py series-fipezap` | Le o Excel do FipeZAP. |
| `python main.py series-painel` | Valida as series, testa vazamento temporal e gera os paineis mensal e trimestral. Termina com erro se houver vazamento. |
| `python main.py eda-series` | Analise exploratoria das series temporais. |
| `python main.py eda-vivareal` | Analise exploratoria dos datasets do VivaReal. |
| `python main.py reg-linear` | Regressao linear multipla de `preco_m2` por segmento, com tres validacoes e baseline por bairro (`docs/MODELOS_PRECIFICACAO.md`). |
| `python main.py arima` | ARIMA do FipeZAP (nacional, SJC e preco real) com walk-forward e benchmarks (~45 s; `docs/MODELOS_TEMPORAIS.md`). |
| `python main.py reg-geo` | Modelos com latitude/longitude (coordenadas imputadas pelo bairro, preco dos vizinhos, setor IBGE) e gradient boosting (`docs/ANALISE_GEOGRAFICA.md`). |
| `python main.py lstm` | LSTM e gradient boosting globais em painel de 50 cidades do FipeZAP, com semelhanca entre cidades, contra o ARIMA (~7 min; `docs/MODELOS_LSTM.md`). |
| `python main.py ajuste-gb` | Ajuste de parametros do gradient boosting, comparacao com o Random Forest original e importancia das variaveis (~7 min). |
| `python main.py modelos-avancados` | Terreno e texto do anuncio, LightGBM/CatBoost, busca bayesiana (Optuna), conjunto e intervalos conformais (~66 min; `docs/MODELOS_AVANCADOS.md`). |
| `python main.py projecao` | Projecao de preco de Jacarei: valor estimado de cada anuncio x tendencia do FipeZAP de SJC (~4 min; precisa de `modelos-avancados`; `docs/PROJECAO_JACAREI.md`). |
| `python main.py mapa-setores` | Mapa de R$/m2 por setor censitario do IBGE: PNG e HTML interativo. |
| `python main.py arima-plus` | Combinacao, ARIMAX, cidades vizinhas e avaliacao ampliada do ARIMA (~2 min). |
| `python main.py jacarei-train` | Treina o baseline Random Forest. |
| `python main.py` | Menu interativo. |

Comandos do fluxo legado: `scrape`, `clean`, `stats`, `all`.

## O que ler primeiro

- [`docs/METAS.md`](docs/METAS.md): metas, dados disponiveis e proximas etapas.
- [`docs/ANALISE_EXPLORATORIA.md`](docs/ANALISE_EXPLORATORIA.md): o que a analise mostrou e as decisoes para a modelagem.
- [`docs/MODELOS_PRECIFICACAO.md`](docs/MODELOS_PRECIFICACAO.md): regressao linear por segmento, desempenho e coeficientes.
- [`docs/MODELOS_AVANCADOS.md`](docs/MODELOS_AVANCADOS.md): terreno, texto, ajuste bayesiano, conjunto e intervalos (R2 temporal 0,71 a 0,80).
- [`docs/PROJECAO_JACAREI.md`](docs/PROJECAO_JACAREI.md): valor estimado e projecao de preco de Jacarei, com premissas.
- [`docs/MODELOS_LSTM.md`](docs/MODELOS_LSTM.md): LSTM em painel de cidades, semelhanca e comparacao com o ARIMA.
- [`docs/MODELOS_TEMPORAIS.md`](docs/MODELOS_TEMPORAIS.md): ARIMA do FipeZAP, desempenho contra benchmarks e limitacoes.
- [`docs/DIARIO_MODELAGEM.md`](docs/DIARIO_MODELAGEM.md): tecnicas, tratamento de dados faltantes e evolucao do R2 (base do relatorio final).
- [`docs/ANALISE_GEOGRAFICA.md`](docs/ANALISE_GEOGRAFICA.md): latitude/longitude nos modelos de preco e mapas.
- [`docs/SERIES_TEMPORAIS.md`](docs/SERIES_TEMPORAIS.md): fontes, defasagens de publicacao, correcoes do fluxo antigo e teste de vazamento.
- [`docs/AUDITORIA_VIVAREAL.md`](docs/AUDITORIA_VIVAREAL.md): qualidade da base do orientador.
- [`docs/ORGANIZACAO_REPOSITORIO.md`](docs/ORGANIZACAO_REPOSITORIO.md): estrutura e decisoes de organizacao.

## Paineis de series temporais

Os arquivos `painel_mensal.csv` e `painel_trimestral.csv` (em
`data/processed/series/`) sao **"as-of"**: cada linha traz so o que ja estava
publicado naquele mes. Use-os como variaveis explicativas. Os `*_referencia.csv`
alinham cada valor pela data a que ele se refere e servem **so para definir o
alvo**.

## Baseline atual (Random Forest)

`python main.py jacarei-train` treina um `RandomForestRegressor` para prever
`preco_m2` (alvo com `log1p`/`expm1`). Este e o baseline de **precificacao de
anuncios**, nao um modelo temporal.

Atencao: os artefatos em `data/models/jacarei/` (R2 de 0,78 em 18.453 linhas) foram
gerados com limites de limpeza mais largos do que os atuais em
`src/pricing/config.py`, que hoje resultam em R2 de ~0,51 em 13.781 linhas. Os dois
nao correspondem e isso ainda precisa ser resolvido; nao cite o R2 de 0,78 como
resultado atual.

## Limitacoes conhecidas

- A base do VivaReal e uma fotografia de anuncios ativos, com vies de
  sobrevivencia; as datas de criacao nao formam uma serie de precos.
- O FipeZAP e media movel trimestral e nao tem Jacarei (Sao Jose dos Campos e a
  cidade coberta mais proxima).
- Cinco defasagens de publicacao sao estimativas e o IBC-Br dessazonalizado e
  revisado pela fonte (ver `docs/SERIES_TEMPORAIS.md`).

## Proximos passos

1. comando para precificar um imovel (confirmar antes a unidade do IPTU, cuja mediana de R$ 100 a R$ 150 por ano e suspeita)
2. variaveis de qualidade do imovel e mais arquivos do Censo; snapshots periodicos do VivaReal
3. metas 7 a 9: sensibilidade das variaveis, visualizacoes interativas e relatorios automaticos
