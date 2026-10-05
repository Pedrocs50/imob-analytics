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
| 4 | Regressao linear multipla e ARIMA | Atingida para precos (demanda nao coberta) | **Regressao linear multipla** por segmento (`reg-linear`; R2 de 0,45-0,49 em apartamento e 0,58-0,63 nos demais; `docs/MODELOS_PRECIFICACAO.md`) e **ARIMA** do FipeZAP (`arima`; walk-forward com benchmarks; `docs/MODELOS_TEMPORAIS.md`). O meta cita "preco e demanda": nao ha serie de demanda no projeto. |
| 5 | LSTM multivariado | Atingida (univariado/painel; sem preditores macro) | `python main.py lstm`: LSTM e gradient boosting global em painel de 50 cidades, com variantes por semelhanca (`docs/MODELOS_LSTM.md`). O LSTM usa so o crescimento passado das series; nao foi testado com preditores macro. |
| 6 | Comparacao ARIMA x LSTM (RMSE, MAE, R2) | Atingida com ressalvas | Mesmo walk-forward e Diebold-Mariano: ARIMA melhor no indice nacional; redes menores em SJC aos 6 e 12 meses, sem significancia. Nenhum modelo e uniformemente melhor (`docs/MODELOS_LSTM.md`). |
| 7 | Sensibilidade e relevancia das variaveis | Parcial | Importancia por permutacao do gradient boosting (`ajuste-gb`; `docs/DIARIO_MODELAGEM.md`, secao 4) e coeficientes da regressao linear. Falta sensibilidade/cenarios formais. |
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
7. (feito) Limpeza do VivaReal ajustada: taxas de condominio/IPTU implausiveis viram
   ausentes e ha indicadores `condominio_informado` e `iptu_informado`.
8. (feito) Regressao linear multipla por segmento: `docs/MODELOS_PRECIFICACAO.md`.
9. (feito) ARIMA do FipeZAP nacional, SJC e preco real: `docs/MODELOS_TEMPORAIS.md`.
10. (feito) Modelos com latitude e longitude e gradient boosting: `docs/ANALISE_GEOGRAFICA.md`.
11. (feito) Combinacao, ARIMAX, cidades vizinhas e avaliacao ampliada: `docs/MODELOS_TEMPORAIS.md`
    (sem ganho significativo no nacional).
12. (feito) Coordenadas imputadas e setores censitarios do IBGE (mapas estatico e interativo):
    `docs/ANALISE_GEOGRAFICA.md`.
13. (feito) Censo 2022 por setor (renda, densidade, domicilios), ajuste de parametros e importancia das
    variaveis; tudo registrado em `docs/DIARIO_MODELAGEM.md` (evolucao do R2).
14. (feito) LSTM e modelos globais em painel de 50 cidades com semelhanca: `docs/MODELOS_LSTM.md`.
15. (feito) Modelos avancados de precificacao (terreno, texto, Optuna, LightGBM/CatBoost, conjunto, intervalos conformais):
    R2 temporal 0,71 / 0,79 / 0,80 (apartamento / casa / residencial): `docs/MODELOS_AVANCADOS.md`.
16. (feito) Projecao de preco de Jacarei (precificacao x tendencia do FipeZAP de SJC): `docs/PROJECAO_JACAREI.md`.
17. Proximo: comando para precificar um imovel; variaveis de qualidade e arquivos de domicilios/entorno do Censo; metas 7 a 9.
    Pendencia: confirmar a unidade do IPTU (mediana de R$ 100 a R$ 150 por ano e suspeita).
