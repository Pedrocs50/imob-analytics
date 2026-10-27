# LSTM com indicadores macroeconomicos x regressao tradicional e ARIMA

Gerado por `python main.py lstm-macro`. Nao editar manualmente.

Alvos: crescimento do preco medio de venda residencial do FipeZAP em **SJC** (proxy de Jacarei, que nao esta no FipeZAP) e no **indice nacional**. Entrada do LSTM: ultimos 12 meses de crescimento padronizado de **50 cidades** (painel) e, na variante com macro, 8 indicadores do BCB e do IPEA (bcb_selic_meta, bcb_ipca, bcb_incc, bcb_ptax, bcb_ibcbr, bcb_credimob_saldo, ipea_icc, selic_real_mes); saida direta de 12 meses. Media de 5 sementes; reajuste a cada 12 meses; walk-forward com janela expansiva (mesmos horizontes, ARIMA e testes dos demais relatorios).

- **Sem vazamento:** o macro vem do painel *as-of* (cada mes so contem o que ja estava publicado) e sua escala e calculada so com o treino de cada reajuste.
- **Regressao tradicional:** Ridge (alfa 5.0) direta por horizonte, com crescimento de 3 e 12 meses do alvo (e o macro do mes, na variante com macro), reajustada todo mes.
- **Ablacao:** `LSTM painel (sem macro)` e `LSTM painel + macro` usam a mesma construcao e as mesmas sementes; a diferenca entre eles e o efeito do macro.
- **Caracteristicas dos imoveis:** entram pelo modelo de precificacao de Jacarei (R$/m2 por anuncio, `docs/MODELOS_AVANCADOS.md`), combinado com a tendencia prevista aqui em `docs/PROJECAO_JACAREI.md`. O VivaReal e uma fotografia de um unico mes; nao ha historico de anuncios para alimentar o LSTM.

Tempo total: 4.4 min.

## SJC (nominal) (44 origens)

### Erro por horizonte (MAE e RMSE em R$/m2; MAPE em %)

| h (meses) | modelo | n origens | MAE | RMSE | MAPE (%) | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 44 | 24.689 | 33.761 | 0.313 | 1.000 |
| 1 | Tendencia (12 meses) | 44 | 36.161 | 48.496 | 0.458 | 1.436 |
| 1 | Regressao linear (so o alvo) | 44 | 31.787 | 43.598 | 0.401 | 1.291 |
| 1 | Regressao linear (alvo + macro) | 44 | 32.582 | 44.080 | 0.410 | 1.306 |
| 1 | LSTM painel (sem macro) | 44 | 26.048 | 35.038 | 0.330 | 1.038 |
| 1 | LSTM painel + macro | 44 | 37.036 | 49.849 | 0.471 | 1.477 |
| 3 | ARIMA(0,2,3) | 42 | 94.615 | 130.362 | 1.184 | 1.000 |
| 3 | Tendencia (12 meses) | 42 | 100.506 | 132.438 | 1.264 | 1.016 |
| 3 | Regressao linear (so o alvo) | 42 | 90.808 | 131.340 | 1.147 | 1.008 |
| 3 | Regressao linear (alvo + macro) | 42 | 100.697 | 136.287 | 1.267 | 1.045 |
| 3 | LSTM painel (sem macro) | 42 | 88.619 | 124.155 | 1.119 | 0.952 |
| 3 | LSTM painel + macro | 42 | 119.197 | 156.068 | 1.484 | 1.197 |
| 6 | ARIMA(0,2,3) | 39 | 220.979 | 282.846 | 2.752 | 1.000 |
| 6 | Tendencia (12 meses) | 39 | 176.910 | 217.991 | 2.191 | 0.771 |
| 6 | Regressao linear (so o alvo) | 39 | 172.705 | 230.969 | 2.170 | 0.817 |
| 6 | Regressao linear (alvo + macro) | 39 | 201.697 | 252.824 | 2.494 | 0.894 |
| 6 | LSTM painel (sem macro) | 39 | 177.015 | 232.218 | 2.212 | 0.821 |
| 6 | LSTM painel + macro | 39 | 238.009 | 292.430 | 2.877 | 1.034 |
| 12 | ARIMA(0,2,3) | 33 | 447.191 | 532.633 | 5.376 | 1.000 |
| 12 | Tendencia (12 meses) | 33 | 290.055 | 322.779 | 3.446 | 0.606 |
| 12 | Regressao linear (so o alvo) | 33 | 305.392 | 436.961 | 3.765 | 0.820 |
| 12 | Regressao linear (alvo + macro) | 33 | 293.711 | 332.085 | 3.459 | 0.623 |
| 12 | LSTM painel (sem macro) | 33 | 276.597 | 305.372 | 3.265 | 0.573 |
| 12 | LSTM painel + macro | 33 | 454.229 | 498.957 | 5.328 | 0.937 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| LSTM painel + macro | ARIMA(0,2,3) | 1 | 2.014 | 0.050 |
| LSTM painel + macro | ARIMA(0,2,3) | 3 | 1.180 | 0.245 |
| LSTM painel + macro | ARIMA(0,2,3) | 6 | 0.159 | 0.875 |
| LSTM painel + macro | ARIMA(0,2,3) | 12 | -0.169 | 0.867 |
| LSTM painel + macro | LSTM painel (sem macro) | 1 | 2.306 | 0.026 |
| LSTM painel + macro | LSTM painel (sem macro) | 3 | 1.287 | 0.205 |
| LSTM painel + macro | LSTM painel (sem macro) | 6 | 0.997 | 0.325 |
| LSTM painel + macro | LSTM painel (sem macro) | 12 | 1.941 | 0.061 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 1 | 1.427 | 0.161 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 3 | 0.952 | 0.347 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 6 | 0.711 | 0.481 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 12 | 1.439 | 0.160 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 1 | 1.551 | 0.128 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 3 | 0.507 | 0.615 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 6 | -0.839 | 0.407 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 12 | -1.345 | 0.188 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 1 | 0.315 | 0.754 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 3 | 0.770 | 0.446 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 6 | 0.580 | 0.566 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 12 | -0.583 | 0.564 |

### Amostras de treino por reajuste (sem macro / com macro)

- 2022-12: 3660 / 3660
- 2023-12: 4260 / 4260
- 2024-12: 4860 / 4860
- 2025-12: 5460 / 5460

## nacional (nominal) (140 origens)

### Erro por horizonte (MAE e RMSE em R$/m2; MAPE em %)

| h (meses) | modelo | n origens | MAE | RMSE | MAPE (%) | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 140 | 5.454 | 7.136 | 0.071 | 1.000 |
| 1 | Tendencia (12 meses) | 140 | 8.384 | 10.909 | 0.111 | 1.529 |
| 1 | Regressao linear (so o alvo) | 140 | 6.676 | 8.516 | 0.087 | 1.193 |
| 1 | Regressao linear (alvo + macro) | 140 | 7.592 | 9.897 | 0.098 | 1.387 |
| 1 | LSTM painel (sem macro) | 140 | 9.147 | 11.662 | 0.124 | 1.634 |
| 1 | LSTM painel + macro | 140 | 12.814 | 15.737 | 0.165 | 2.205 |
| 3 | ARIMA(0,2,3) | 138 | 18.389 | 24.409 | 0.238 | 1.000 |
| 3 | Tendencia (12 meses) | 138 | 24.434 | 32.596 | 0.323 | 1.335 |
| 3 | Regressao linear (so o alvo) | 138 | 20.993 | 26.830 | 0.273 | 1.099 |
| 3 | Regressao linear (alvo + macro) | 138 | 26.269 | 33.487 | 0.344 | 1.372 |
| 3 | LSTM painel (sem macro) | 138 | 28.031 | 35.044 | 0.375 | 1.436 |
| 3 | LSTM painel + macro | 138 | 43.652 | 53.143 | 0.554 | 2.177 |
| 6 | ARIMA(0,2,3) | 135 | 41.006 | 52.616 | 0.532 | 1.000 |
| 6 | Tendencia (12 meses) | 135 | 51.286 | 67.426 | 0.674 | 1.281 |
| 6 | Regressao linear (so o alvo) | 135 | 44.710 | 58.121 | 0.589 | 1.105 |
| 6 | Regressao linear (alvo + macro) | 135 | 57.370 | 74.976 | 0.758 | 1.425 |
| 6 | LSTM painel (sem macro) | 135 | 59.209 | 72.462 | 0.786 | 1.377 |
| 6 | LSTM painel + macro | 135 | 92.934 | 113.076 | 1.160 | 2.149 |
| 12 | ARIMA(0,2,3) | 129 | 91.030 | 117.690 | 1.182 | 1.000 |
| 12 | Tendencia (12 meses) | 129 | 112.433 | 148.575 | 1.465 | 1.262 |
| 12 | Regressao linear (so o alvo) | 129 | 105.663 | 149.982 | 1.400 | 1.274 |
| 12 | Regressao linear (alvo + macro) | 129 | 144.131 | 182.069 | 1.885 | 1.547 |
| 12 | LSTM painel (sem macro) | 129 | 132.698 | 161.410 | 1.748 | 1.371 |
| 12 | LSTM painel + macro | 129 | 202.173 | 242.403 | 2.509 | 2.060 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| LSTM painel + macro | ARIMA(0,2,3) | 1 | 7.437 | 0.000 |
| LSTM painel + macro | ARIMA(0,2,3) | 3 | 5.125 | 0.000 |
| LSTM painel + macro | ARIMA(0,2,3) | 6 | 3.453 | 0.001 |
| LSTM painel + macro | ARIMA(0,2,3) | 12 | 2.474 | 0.015 |
| LSTM painel + macro | LSTM painel (sem macro) | 1 | 2.595 | 0.010 |
| LSTM painel + macro | LSTM painel (sem macro) | 3 | 2.629 | 0.010 |
| LSTM painel + macro | LSTM painel (sem macro) | 6 | 1.791 | 0.076 |
| LSTM painel + macro | LSTM painel (sem macro) | 12 | 1.285 | 0.201 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 1 | 5.253 | 0.000 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 3 | 3.541 | 0.001 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 6 | 1.955 | 0.053 |
| LSTM painel + macro | Regressao linear (alvo + macro) | 12 | 0.944 | 0.347 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 1 | 3.409 | 0.001 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 3 | 3.005 | 0.003 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 6 | 2.713 | 0.008 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 12 | 2.160 | 0.033 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 1 | 2.018 | 0.046 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 3 | 2.214 | 0.028 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 6 | 2.051 | 0.042 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 12 | 0.995 | 0.322 |

### Amostras de treino por reajuste (sem macro / com macro)

- 2014-12: 435 / 435
- 2015-12: 730 / 730
- 2016-12: 1044 / 1044
- 2017-12: 1356 / 1356
- 2018-12: 1668 / 1668
- 2019-12: 1980 / 1980
- 2020-12: 2592 / 2592
- 2021-12: 3204 / 3204
- 2022-12: 3816 / 3816
- 2023-12: 4428 / 4428
- 2024-12: 5040 / 5040
- 2025-12: 5652 / 5652

## Figura

- `reports/figures/lstm_macro_comparacao.png`

