# Organizacao do repositorio

Estrutura pensada em duas trilhas independentes, separadas pelo tipo de dado:

| Trilha | Dado | Modelos | Metas |
|---|---|---|---|
| Precificacao (transversal) | VivaReal Jacarei, um snapshot | Regressao linear multipla, Random Forest | 2, 3, 4 (regressao), 7 |
| Series temporais | FipeZAP mensal + series macro | ARIMA/ARIMAX, LSTM | 4 (ARIMA), 5, 6 |

O Random Forest atual e o baseline da trilha de precificacao. Nao e modelo
temporal. ARIMA e LSTM nunca usam o VivaReal diretamente como serie de precos
(ver `docs/AUDITORIA_VIVAREAL.md`).

## Estrutura atual

```text
main.py                     interface de comandos (scrape, clean, stats, jacarei-train, all)
src/
  scraper.py, cleaner.py, database.py, repository.py, stats.py, macro/
                            fluxo legado e coleta; NAO movidos (o scraper depende de
                            scripts/chrome-win64 e do diretorio de execucao)
  vivareal/                 carga, limpeza e features da base do orientador (meta 2)
  pricing/                  trilha de precificacao
    config.py               limites de limpeza e hiperparametros do baseline
    random_forest.py        baseline atual
    linear_regression.py    regressao linear multipla por segmento
    geo.py                  modelos com lat/lon (imputacao, kNN, setor IBGE, gradient boosting) e mapas
    censo.py                variaveis do Censo 2022 por setor (renda, densidade, domicilios)
    ajuste.py               ajuste de parametros e importancia das variaveis
    modelos_avancados.py    LightGBM/CatBoost, Optuna, conjunto e intervalos conformais
    projecao.py             valor estimado por anuncio x tendencia do FipeZAP
  timeseries/               trilha temporal: catalogo, clientes de API, FipeZAP,
                            banco, validacao e paineis (feito; ver docs/SERIES_TEMPORAIS.md).
                            arima.py, arima_plus.py e lstm_painel.py (feitos)
  analysis/                 analise exploratoria: series_eda.py, vivareal_eda.py, mapa_setores.py, utils.py
  evaluation/               RMSE, MAE, R2 e comparacao, compartilhados pelas trilhas
data/
  raw/                      originais, preservados (nunca sobrescrever)
  database/                 banco do fluxo legado (ignorado pelo git)
  interim/                  saidas intermediarias
  processed/                saidas legadas + vivareal/ (dataset limpo)
  models/jacarei/           artefatos do baseline atual
reports/
  figures/  results/        saidas das analises e modelos
sql/queries/                consultas SQL de apoio
notebooks/                  reservado a notebooks Jupyter
docs/                       metas, auditoria e este documento
```

Pastas ainda nao criadas, para quando a etapa comecar: `src/visualization/`
(meta 8) e `src/reporting/` (meta 9).

## O que foi feito

- Criadas as pastas acima; `src/ml/` virou `src/pricing/`
  (`jacarei_random_forest.py` -> `random_forest.py`).
- `main.py` importa de `src.pricing.random_forest`; o comando
  `jacarei-train` continua igual.
- `notebooks/*.sql` movidos para `sql/queries/`.

## O que continua para depois

- Mover scraper, cleaner, database, repository, stats e macro para
  subpacotes, com imports de compatibilidade e um passo por vez.
- (feito) `src/vivareal/` tem o pipeline de dataset limpo: `python main.py vivareal-prep`.
- Adaptar `src/pricing/` para treinar a partir dos datasets de `data/processed/vivareal/`.
- Criar `timeseries/` e `evaluation/` com conteudo quando comecarem as metas 4 a 6.

## Observacao sobre o baseline

Os artefatos em `data/models/jacarei/` (R2 ~0,78, 18.453 linhas) foram gerados
com limites de limpeza mais largos do que os atuais em
`src/pricing/config.py`. Com a configuracao atual, o treino usa 13.781 linhas
e da R2 ~0,51 (validado em pasta temporaria, sem sobrescrever os artefatos).
Os artefatos existentes e o codigo atual nao correspondem; isso deve ser
resolvido na etapa do dataset limpo.
