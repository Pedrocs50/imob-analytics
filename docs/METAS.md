# Metas da iniciacao cientifica e estado atual

Documento de rastreamento. Atualizar o status a cada etapa concluida.
Ultima verificacao do repositorio: 2026-09-29.

## Regras do projeto

- `data/raw/` nunca e sobrescrito. Isso inclui o banco do orientador
  (`data/raw/vivareal_jacarei/vivareal_jacarei_20260324.db`).
- O scraper (`src/scraper.py`) e o comando `python main.py scrape` devem ser
  preservados em qualquer reorganizacao.
- O Random Forest atual e o baseline de precificacao de anuncios (dados
  transversais). Nao e ARIMA, LSTM nem regressao temporal.
- Precificacao de anuncios e previsao temporal sao problemas diferentes e ficam
  em trilhas separadas.

## Status das metas

| Meta | Descricao resumida | Status | Onde esta / o que falta |
|---|---|---|---|
| 1 | Mapeamento e coleta de dados publicos | Atingida | Scraper, base VivaReal do orientador, FipeZAP (Excel) e 14 series BCB/IBGE/IPEA coletadas por API. Fontes documentadas em `docs/SERIES_TEMPORAIS.md`. Faltam registros municipais. |
| 2 | Tratamento, padronizacao e organizacao | Atingida para VivaReal e series temporais | `python main.py vivareal-prep` (3 datasets limpos) e `series-coletar` / `series-fipezap` / `series-painel` (banco `series_temporais.db`, validacao e paineis mensal/trimestral). O fluxo legado (`cleaner.py`) segue separado. |
| 3 | Estatistica descritiva e exploratoria | Atingida | `python main.py eda-series` e `eda-vivareal`: estacionariedade, autocorrelacao, sazonalidade, correlacao cruzada, Granger e estabilidade por subperiodo (series); distribuicao, ausentes, correlacoes, VIF, bairros, condominio e coordenadas (VivaReal). Leitura em `docs/ANALISE_EXPLORATORIA.md`; relatorios em `reports/results/eda_*.md`; figuras em `reports/figures/eda_*.png`. |
| 4 | Regressao linear multipla e ARIMA | Nao iniciada | Existe apenas o Random Forest baseline. |
| 5 | LSTM multivariado | Nao iniciada | - |
| 6 | Comparacao ARIMA x LSTM (RMSE, MAE, R2) | Nao iniciada | Depende das metas 4 e 5. |
| 7 | Sensibilidade e relevancia das variaveis | Nao iniciada | O Random Forest pode fornecer importancia de variaveis como ponto de partida. |
| 8 | Visualizacoes interativas | Nao iniciada | Os graficos atuais sao PNGs estaticos. |
| 9 | Relatorios analiticos automaticos | Nao iniciada | - |

## Dados disponiveis

| Fonte | Local | Conteudo | Dimensao temporal |
|---|---|---|---|
| VivaReal Jacarei (orientador) | `data/raw/vivareal_jacarei/*.db`, tabela `listings` | 23.128 linhas, 20.960 `external_id` distintos | Um unico snapshot (coletado em 20-21/03/2026). `created_at` vai de 2017 a 2026, mas ~83% dos anuncios sao de 2025-2026. |
| Base legada do projeto | `data/database/imoveis.db` | `imoveis_raw` (12.954), `imoveis_processados` (8.891) | Coleta em 2 dias (abril/2026). Sem historico. |
| FipeZAP (Excel) | `data/raw/fipezap-serieshistoricas (2).xlsx` -> `series_temporais.db` | 35 series: indice nacional (com 1 a 4 dormitorios) e Sao Jose dos Campos; venda, locacao e yield | Nacional 2008-01 a 2026-08 (224 meses); SJC 2018-01 a 2026-08 (104 meses) |
| Series macro (API) | `data/database/series_temporais.db` | 14 series: Selic, IPCA, IGP-M, INCC, PTAX, IBC-Br, credito e juros imobiliarios, ICC, desocupacao e renda | Mensais desde 2005 (algumas desde 2007/2011/2012); PNAD de SP trimestral |
| Paineis para modelagem | `data/processed/series/painel_mensal.csv`, `painel_trimestral.csv` (as-of, para preditores) e `*_referencia.csv` (so para o alvo) | FipeZAP + macro; preco real (IPCA) e derivadas. Cada linha contem so o que estava publicado no mes (teste de vazamento em `series-painel`) | 224 meses / 74 trimestres |
| Macro do fluxo legado | tabela `indicadores_macro` em `imoveis.db` | **Nao usar**: contem erros (ver `docs/SERIES_TEMPORAIS.md`) | - |

Observacoes:

- O `created_at` do VivaReal descreve anuncios ativos em marco/2026, agrupados
  pela data de publicacao. Ha vies de sobrevivencia e o preco pode ter sido
  atualizado depois; nao e uma serie historica de precos.
- As unicas series temporais reais sao o FipeZAP e as series macro.
- Jacarei nao consta na planilha do FipeZAP. Sao Jose dos Campos (104 meses) e a
  cidade coberta mais proxima; o indice nacional tem 224 meses.
- Os precos do FipeZAP sao medias moveis trimestrais (nota da propria planilha),
  o que suaviza a serie e deve constar na metodologia.

## Direcao acordada

1. Usar a base VivaReal para precificacao transversal (regressao linear
   multipla e comparacao com o Random Forest).
2. ARIMA/ARIMAX e LSTM sobre o indice FipeZAP com variaveis exogenas macro. O
   indice nacional (224 meses) da mais folga que SJC (104 meses). O LSTM pode
   nao superar o ARIMA; isso e um resultado valido para a meta 6 e deve constar
   na metodologia. Series originalmente trimestrais ficam trimestrais no painel
   trimestral e, no mensal, entram repetidas e com defasagem de divulgacao.
3. Ajustes no scraper e coleta periodica de snapshots ficam para uma etapa
   posterior, quando o objetivo for formar historico proprio.

## Pendencias de decisao

- Confirmar com o orientador que ARIMA/LSTM sobre FipeZAP + macro atende a
  proposta.
- Confirmar se o FipeZAP de Sao Jose dos Campos (ou o indice nacional) e
  aceitavel como referencia para Jacarei, ja que a planilha nao tem Jacarei.
- Definir se o banco do orientador entra no versionamento git ou fica apenas
  ignorado (nada sera commitado por enquanto).

## Proximas etapas

1. (feito) Registrar metas, dados e regras.
2. (feito) Auditoria da base VivaReal: `docs/AUDITORIA_VIVAREAL.md`.
3. (feito) Reorganizacao minima do repositorio (`docs/ORGANIZACAO_REPOSITORIO.md`).
4. (feito) Datasets limpos do VivaReal por segmento: `vivareal-prep`.
5. (feito) Series temporais: FipeZAP + macro corrigidos, com banco proprio,
   validacao e paineis (`docs/SERIES_TEMPORAIS.md`).
5b. (feito) Paineis as-of com defasagem de publicacao (IPCA, ICC, FipeZAP e PNAD
   confirmados em fontes) e teste automatico de vazamento temporal.
6. (feito) Analise exploratoria das series e dos 3 datasets VivaReal (meta 3):
   `docs/ANALISE_EXPLORATORIA.md`.
7. Proximo: ajustar a limpeza do VivaReal (condominio e IPTU implausiveis),
   depois ARIMA/ARIMAX e regressao linear multipla (meta 4), com os alvos e
   cuidados descritos na analise exploratoria.
