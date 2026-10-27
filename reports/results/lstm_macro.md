# LSTM com indicadores macroeconomicos x regressao tradicional e ARIMA

Gerado por `python main.py lstm-macro`. Nao editar manualmente.

Alvos: crescimento do preco medio de venda residencial do FipeZAP em **SJC** (proxy de Jacarei, que nao esta no FipeZAP) e no **indice nacional**. Entrada do LSTM: ultimos 12 meses de crescimento padronizado de **50 cidades** (painel) e, na variante com macro, 8 indicadores do BCB e do IPEA (bcb_selic_meta, bcb_ipca, bcb_incc, bcb_ptax, bcb_ibcbr, bcb_credimob_saldo, ipea_icc, selic_real_mes); saida direta de 12 meses. Media de 5 sementes; reajuste a cada 12 meses; walk-forward com janela expansiva (mesmos horizontes, ARIMA e testes dos demais relatorios).

- **Sem vazamento:** o macro vem do painel *as-of* (cada mes so contem o que ja estava publicado) e sua escala e calculada so com o treino de cada reajuste.
- **Regressao tradicional:** Ridge (alfa 5.0) direta por horizonte, com crescimento de 3 e 12 meses do alvo (e o macro do mes, na variante com macro), reajustada todo mes.
- **Ablacao:** todas as redes usam a mesma construcao e as mesmas sementes; a diferenca para `LSTM painel (sem macro)` e o efeito do macro. Alem do conjunto completo, testam-se dois subconjuntos definidos antes (ARIMAX de `arima_plus.py`): juros e confianca (bcb_selic_meta, ipea_icc); credito + juros + confianca + IBC-Br (bcb_credimob_saldo, bcb_selic_meta, ipea_icc, bcb_ibcbr). Todos os modelos testados estao reportados.
- **Caracteristicas dos imoveis:** entram pelo modelo de precificacao de Jacarei (R$/m2 por anuncio, `docs/MODELOS_AVANCADOS.md`), combinado com a tendencia prevista aqui em `docs/PROJECAO_JACAREI.md`. O VivaReal e uma fotografia de um unico mes; nao ha historico de anuncios para alimentar o LSTM.

Tempo total: 20.5 min.

## SJC (nominal) (44 origens)

### Escolha da variante: selecao x confirmacao (as primeiras 60% das origens escolhem; as demais confirmam)

Melhor LSTM pelo periodo de **selecao**: `LSTM painel (credito + juros + confianca + IBC-Br; base)`. Se a nota dele piora muito na confirmacao, a vantagem era sorte.

| modelo | origens - confirmacao | origens - selecao | RMSE relativo ao ARIMA (media dos horizontes) - confirmacao | RMSE relativo ao ARIMA (media dos horizontes) - selecao | MAPE medio (%) - confirmacao | MAPE medio (%) - selecao |
|---|---|---|---|---|---|---|
| LSTM painel (credito + juros + confianca + IBC-Br; base) | 18 | 26 | 1.341 | 0.832 | 1.466 | 1.824 |
| LSTM painel (sem macro; pequena) | 18 | 26 | 0.965 | 0.836 | 0.942 | 1.912 |
| LSTM painel (sem macro; base) | 18 | 26 | 1.049 | 0.839 | 1.030 | 2.062 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | 18 | 26 | 1.287 | 0.855 | 1.391 | 1.815 |
| LSTM painel (sem macro; grande) | 18 | 26 | 1.005 | 0.861 | 1.002 | 2.187 |
| LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 18 | 26 | 1.267 | 0.892 | 1.357 | 2.028 |
| Regressao linear (alvo + juros e confianca) | 18 | 26 | 0.882 | 0.962 | 0.657 | 2.290 |
| Tendencia (12 meses) | 18 | 26 | 1.056 | 0.967 | 1.033 | 2.219 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 18 | 26 | 0.893 | 0.971 | 0.728 | 2.290 |
| Regressao linear (alvo + macro) | 18 | 26 | 0.987 | 0.977 | 0.728 | 2.427 |
| ARIMA(0,2,3) | 18 | 26 | 1.000 | 1.000 | 0.910 | 2.973 |
| LSTM painel (juros e confianca; pequena) | 18 | 26 | 1.381 | 1.001 | 1.520 | 2.428 |
| LSTM painel (juros e confianca; grande) | 18 | 26 | 1.153 | 1.013 | 1.251 | 2.552 |
| Regressao linear (so o alvo) | 18 | 26 | 0.500 | 1.014 | 0.275 | 2.507 |
| LSTM painel (juros e confianca; base) | 18 | 26 | 1.143 | 1.017 | 1.231 | 2.570 |
| LSTM painel (macro completo; grande) | 18 | 26 | 2.163 | 1.033 | 2.570 | 2.740 |
| LSTM painel (macro completo; base) | 18 | 26 | 2.225 | 1.080 | 2.627 | 2.579 |
| LSTM painel (macro completo; pequena) | 18 | 26 | 2.129 | 1.138 | 2.487 | 2.768 |

### Erro por horizonte (MAE e RMSE em R$/m2; MAPE em %)

| h (meses) | modelo | n origens | MAE | RMSE | MAPE (%) | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 44 | 24.689 | 33.761 | 0.313 | 1.000 |
| 1 | Tendencia (12 meses) | 44 | 36.161 | 48.496 | 0.458 | 1.436 |
| 1 | Regressao linear (so o alvo) | 44 | 31.787 | 43.598 | 0.401 | 1.291 |
| 1 | Regressao linear (alvo + macro) | 44 | 32.582 | 44.080 | 0.410 | 1.306 |
| 1 | Regressao linear (alvo + juros e confianca) | 44 | 31.772 | 43.602 | 0.400 | 1.291 |
| 1 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 44 | 32.533 | 44.871 | 0.410 | 1.329 |
| 1 | LSTM painel (sem macro; base) | 44 | 26.048 | 35.038 | 0.330 | 1.038 |
| 1 | LSTM painel (sem macro; pequena) | 44 | 26.408 | 37.213 | 0.334 | 1.102 |
| 1 | LSTM painel (sem macro; grande) | 44 | 26.469 | 34.864 | 0.335 | 1.033 |
| 1 | LSTM painel (macro completo; base) | 44 | 37.036 | 49.849 | 0.471 | 1.477 |
| 1 | LSTM painel (macro completo; pequena) | 44 | 38.614 | 52.468 | 0.491 | 1.554 |
| 1 | LSTM painel (macro completo; grande) | 44 | 33.356 | 43.704 | 0.424 | 1.295 |
| 1 | LSTM painel (juros e confianca; base) | 44 | 30.289 | 41.881 | 0.384 | 1.241 |
| 1 | LSTM painel (juros e confianca; pequena) | 44 | 33.294 | 45.951 | 0.420 | 1.361 |
| 1 | LSTM painel (juros e confianca; grande) | 44 | 31.257 | 42.111 | 0.397 | 1.247 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 44 | 30.389 | 39.458 | 0.387 | 1.169 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 44 | 31.183 | 42.247 | 0.397 | 1.251 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 44 | 30.712 | 40.088 | 0.391 | 1.187 |
| 3 | ARIMA(0,2,3) | 42 | 94.615 | 130.362 | 1.184 | 1.000 |
| 3 | Tendencia (12 meses) | 42 | 100.506 | 132.438 | 1.264 | 1.016 |
| 3 | Regressao linear (so o alvo) | 42 | 90.808 | 131.340 | 1.147 | 1.008 |
| 3 | Regressao linear (alvo + macro) | 42 | 100.697 | 136.287 | 1.267 | 1.045 |
| 3 | Regressao linear (alvo + juros e confianca) | 42 | 94.326 | 132.289 | 1.189 | 1.015 |
| 3 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 42 | 98.331 | 134.865 | 1.237 | 1.035 |
| 3 | LSTM painel (sem macro; base) | 42 | 88.619 | 124.155 | 1.119 | 0.952 |
| 3 | LSTM painel (sem macro; pequena) | 42 | 84.331 | 122.739 | 1.064 | 0.942 |
| 3 | LSTM painel (sem macro; grande) | 42 | 90.496 | 125.358 | 1.144 | 0.962 |
| 3 | LSTM painel (macro completo; base) | 42 | 119.197 | 156.068 | 1.484 | 1.197 |
| 3 | LSTM painel (macro completo; pequena) | 42 | 120.820 | 159.922 | 1.506 | 1.227 |
| 3 | LSTM painel (macro completo; grande) | 42 | 120.999 | 152.972 | 1.504 | 1.173 |
| 3 | LSTM painel (juros e confianca; base) | 42 | 103.183 | 143.133 | 1.310 | 1.098 |
| 3 | LSTM painel (juros e confianca; pequena) | 42 | 104.399 | 139.802 | 1.313 | 1.072 |
| 3 | LSTM painel (juros e confianca; grande) | 42 | 107.397 | 146.367 | 1.365 | 1.123 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 42 | 98.071 | 129.116 | 1.233 | 0.990 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 42 | 94.930 | 130.413 | 1.195 | 1.000 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 42 | 100.556 | 133.407 | 1.265 | 1.023 |
| 6 | ARIMA(0,2,3) | 39 | 220.979 | 282.846 | 2.752 | 1.000 |
| 6 | Tendencia (12 meses) | 39 | 176.910 | 217.991 | 2.191 | 0.771 |
| 6 | Regressao linear (so o alvo) | 39 | 172.705 | 230.969 | 2.170 | 0.817 |
| 6 | Regressao linear (alvo + macro) | 39 | 201.697 | 252.824 | 2.494 | 0.894 |
| 6 | Regressao linear (alvo + juros e confianca) | 39 | 183.889 | 235.757 | 2.287 | 0.834 |
| 6 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 39 | 189.972 | 239.396 | 2.350 | 0.846 |
| 6 | LSTM painel (sem macro; base) | 39 | 177.015 | 232.218 | 2.212 | 0.821 |
| 6 | LSTM painel (sem macro; pequena) | 39 | 165.418 | 219.114 | 2.061 | 0.775 |
| 6 | LSTM painel (sem macro; grande) | 39 | 181.772 | 236.949 | 2.275 | 0.838 |
| 6 | LSTM painel (macro completo; base) | 39 | 238.009 | 292.430 | 2.877 | 1.034 |
| 6 | LSTM painel (macro completo; pequena) | 39 | 238.817 | 295.649 | 2.895 | 1.045 |
| 6 | LSTM painel (macro completo; grande) | 39 | 249.520 | 292.762 | 3.017 | 1.035 |
| 6 | LSTM painel (juros e confianca; base) | 39 | 209.224 | 272.183 | 2.629 | 0.962 |
| 6 | LSTM painel (juros e confianca; pequena) | 39 | 205.489 | 253.556 | 2.542 | 0.896 |
| 6 | LSTM painel (juros e confianca; grande) | 39 | 211.783 | 268.589 | 2.670 | 0.950 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 39 | 171.212 | 212.767 | 2.102 | 0.752 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 39 | 176.167 | 218.863 | 2.165 | 0.774 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 39 | 175.699 | 222.128 | 2.161 | 0.785 |
| 12 | ARIMA(0,2,3) | 33 | 447.191 | 532.633 | 5.376 | 1.000 |
| 12 | Tendencia (12 meses) | 33 | 290.055 | 322.779 | 3.446 | 0.606 |
| 12 | Regressao linear (so o alvo) | 33 | 305.392 | 436.961 | 3.765 | 0.820 |
| 12 | Regressao linear (alvo + macro) | 33 | 293.711 | 332.085 | 3.459 | 0.623 |
| 12 | Regressao linear (alvo + juros e confianca) | 33 | 275.346 | 344.543 | 3.261 | 0.647 |
| 12 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 33 | 273.585 | 327.870 | 3.208 | 0.616 |
| 12 | LSTM painel (sem macro; base) | 33 | 276.597 | 305.372 | 3.265 | 0.573 |
| 12 | LSTM painel (sem macro; pequena) | 33 | 248.283 | 280.434 | 2.927 | 0.527 |
| 12 | LSTM painel (sem macro; grande) | 33 | 296.436 | 327.917 | 3.508 | 0.616 |
| 12 | LSTM painel (macro completo; base) | 33 | 454.229 | 498.957 | 5.328 | 0.937 |
| 12 | LSTM painel (macro completo; pequena) | 33 | 483.607 | 520.898 | 5.698 | 0.978 |
| 12 | LSTM painel (macro completo; grande) | 33 | 481.185 | 508.893 | 5.650 | 0.955 |
| 12 | LSTM painel (juros e confianca; base) | 33 | 355.980 | 402.199 | 4.279 | 0.755 |
| 12 | LSTM painel (juros e confianca; pequena) | 33 | 357.254 | 390.135 | 4.253 | 0.732 |
| 12 | LSTM painel (juros e confianca; grande) | 33 | 341.775 | 386.876 | 4.110 | 0.726 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 33 | 248.987 | 286.656 | 2.936 | 0.538 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 33 | 287.827 | 322.778 | 3.412 | 0.606 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 33 | 230.675 | 275.415 | 2.733 | 0.517 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 1 | 0.325 | 0.747 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 3 | -0.581 | 0.564 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 6 | -1.874 | 0.069 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 12 | -1.549 | 0.131 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 1 | 2.014 | 0.050 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 3 | 1.180 | 0.245 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 6 | 0.159 | 0.875 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 12 | -0.169 | 0.867 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | ARIMA(0,2,3) | 1 | 1.238 | 0.223 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | ARIMA(0,2,3) | 3 | 0.008 | 0.993 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | ARIMA(0,2,3) | 6 | -1.583 | 0.122 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | ARIMA(0,2,3) | 12 | -1.450 | 0.157 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 1 | 1.551 | 0.128 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 3 | 0.507 | 0.615 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 6 | -0.839 | 0.407 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 12 | -1.345 | 0.188 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 1 | 1.501 | 0.141 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 3 | 0.168 | 0.867 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 6 | -1.289 | 0.205 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 12 | -1.042 | 0.305 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 1 | 1.620 | 0.113 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 3 | 0.403 | 0.689 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 6 | -1.198 | 0.238 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 12 | -1.195 | 0.241 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 1 | 2.306 | 0.026 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 3 | 1.287 | 0.205 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 6 | 0.997 | 0.325 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 12 | 1.941 | 0.061 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | LSTM painel (sem macro; base) | 1 | 1.483 | 0.145 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | LSTM painel (sem macro; base) | 3 | 0.353 | 0.726 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | LSTM painel (sem macro; base) | 6 | -0.477 | 0.636 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | LSTM painel (sem macro; base) | 12 | -0.321 | 0.750 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | Regressao linear (so o alvo) | 1 | -0.834 | 0.409 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | Regressao linear (so o alvo) | 3 | -0.032 | 0.975 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | Regressao linear (so o alvo) | 6 | -0.320 | 0.751 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | Regressao linear (so o alvo) | 12 | -0.773 | 0.445 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 1 | 0.315 | 0.754 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 3 | 0.770 | 0.446 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 6 | 0.580 | 0.566 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 12 | -0.583 | 0.564 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 1 | -0.062 | 0.951 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 3 | 0.163 | 0.871 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 6 | 0.094 | 0.925 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 12 | -0.644 | 0.524 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 1 | 0.985 | 0.330 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 3 | 0.533 | 0.597 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 6 | 0.196 | 0.845 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 12 | -0.624 | 0.537 |

### Amostras de treino por reajuste (sem macro / com macro)

- 2022-12: 3660 / 3660
- 2023-12: 4260 / 4260
- 2024-12: 4860 / 4860
- 2025-12: 5460 / 5460

## nacional (nominal) (140 origens)

### Escolha da variante: selecao x confirmacao (as primeiras 60% das origens escolhem; as demais confirmam)

Melhor LSTM pelo periodo de **selecao**: `LSTM painel (credito + juros + confianca + IBC-Br; grande)`. Se a nota dele piora muito na confirmacao, a vantagem era sorte.

| modelo | origens - confirmacao | origens - selecao | RMSE relativo ao ARIMA (media dos horizontes) - confirmacao | RMSE relativo ao ARIMA (media dos horizontes) - selecao | MAPE medio (%) - confirmacao | MAPE medio (%) - selecao |
|---|---|---|---|---|---|---|
| ARIMA(0,2,3) | 56 | 84 | 1.000 | 1.000 | 0.475 | 0.522 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | 56 | 84 | 2.184 | 1.161 | 1.250 | 0.590 |
| LSTM painel (macro completo; grande) | 56 | 84 | 2.889 | 1.163 | 1.702 | 0.625 |
| Regressao linear (so o alvo) | 56 | 84 | 1.077 | 1.214 | 0.451 | 0.663 |
| Regressao linear (alvo + juros e confianca) | 56 | 84 | 1.081 | 1.259 | 0.461 | 0.733 |
| LSTM painel (macro completo; pequena) | 56 | 84 | 2.852 | 1.264 | 1.628 | 0.680 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 56 | 84 | 1.186 | 1.292 | 0.533 | 0.748 |
| Regressao linear (alvo + macro) | 56 | 84 | 1.420 | 1.447 | 0.733 | 0.794 |
| Tendencia (12 meses) | 56 | 84 | 1.173 | 1.482 | 0.508 | 0.721 |
| LSTM painel (sem macro; grande) | 56 | 84 | 1.127 | 1.502 | 0.575 | 0.772 |
| LSTM painel (macro completo; base) | 56 | 84 | 2.751 | 1.516 | 1.629 | 0.794 |
| LSTM painel (credito + juros + confianca + IBC-Br; base) | 56 | 84 | 1.808 | 1.551 | 0.951 | 0.802 |
| LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 56 | 84 | 1.690 | 1.650 | 0.940 | 0.878 |
| LSTM painel (sem macro; base) | 56 | 84 | 1.010 | 1.738 | 0.497 | 0.908 |
| LSTM painel (sem macro; pequena) | 56 | 84 | 1.175 | 1.889 | 0.626 | 1.030 |
| LSTM painel (juros e confianca; grande) | 56 | 84 | 2.133 | 1.946 | 1.021 | 0.998 |
| LSTM painel (juros e confianca; pequena) | 56 | 84 | 2.126 | 1.946 | 1.002 | 1.047 |
| LSTM painel (juros e confianca; base) | 56 | 84 | 2.208 | 1.950 | 1.047 | 1.040 |

### Erro por horizonte (MAE e RMSE em R$/m2; MAPE em %)

| h (meses) | modelo | n origens | MAE | RMSE | MAPE (%) | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 140 | 5.454 | 7.136 | 0.071 | 1.000 |
| 1 | Tendencia (12 meses) | 140 | 8.384 | 10.909 | 0.111 | 1.529 |
| 1 | Regressao linear (so o alvo) | 140 | 6.676 | 8.516 | 0.087 | 1.193 |
| 1 | Regressao linear (alvo + macro) | 140 | 7.592 | 9.897 | 0.098 | 1.387 |
| 1 | Regressao linear (alvo + juros e confianca) | 140 | 6.746 | 8.741 | 0.088 | 1.225 |
| 1 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 140 | 7.029 | 9.034 | 0.091 | 1.266 |
| 1 | LSTM painel (sem macro; base) | 140 | 9.147 | 11.662 | 0.124 | 1.634 |
| 1 | LSTM painel (sem macro; pequena) | 140 | 9.694 | 12.206 | 0.130 | 1.711 |
| 1 | LSTM painel (sem macro; grande) | 140 | 8.234 | 10.538 | 0.110 | 1.477 |
| 1 | LSTM painel (macro completo; base) | 140 | 12.814 | 15.737 | 0.165 | 2.205 |
| 1 | LSTM painel (macro completo; pequena) | 140 | 12.434 | 15.981 | 0.157 | 2.240 |
| 1 | LSTM painel (macro completo; grande) | 140 | 11.699 | 14.891 | 0.148 | 2.087 |
| 1 | LSTM painel (juros e confianca; base) | 140 | 11.728 | 15.306 | 0.154 | 2.145 |
| 1 | LSTM painel (juros e confianca; pequena) | 140 | 11.480 | 14.900 | 0.150 | 2.088 |
| 1 | LSTM painel (juros e confianca; grande) | 140 | 12.411 | 15.568 | 0.163 | 2.182 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 140 | 10.507 | 12.947 | 0.139 | 1.814 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 140 | 11.114 | 13.266 | 0.148 | 1.859 |
| 1 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 140 | 10.034 | 12.155 | 0.130 | 1.703 |
| 3 | ARIMA(0,2,3) | 138 | 18.389 | 24.409 | 0.238 | 1.000 |
| 3 | Tendencia (12 meses) | 138 | 24.434 | 32.596 | 0.323 | 1.335 |
| 3 | Regressao linear (so o alvo) | 138 | 20.993 | 26.830 | 0.273 | 1.099 |
| 3 | Regressao linear (alvo + macro) | 138 | 26.269 | 33.487 | 0.344 | 1.372 |
| 3 | Regressao linear (alvo + juros e confianca) | 138 | 21.343 | 27.778 | 0.278 | 1.138 |
| 3 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 138 | 23.029 | 29.245 | 0.301 | 1.198 |
| 3 | LSTM painel (sem macro; base) | 138 | 28.031 | 35.044 | 0.375 | 1.436 |
| 3 | LSTM painel (sem macro; pequena) | 138 | 31.035 | 38.398 | 0.415 | 1.573 |
| 3 | LSTM painel (sem macro; grande) | 138 | 26.514 | 33.477 | 0.353 | 1.372 |
| 3 | LSTM painel (macro completo; base) | 138 | 43.652 | 53.143 | 0.554 | 2.177 |
| 3 | LSTM painel (macro completo; pequena) | 138 | 40.808 | 51.716 | 0.509 | 2.119 |
| 3 | LSTM painel (macro completo; grande) | 138 | 40.723 | 53.024 | 0.507 | 2.172 |
| 3 | LSTM painel (juros e confianca; base) | 138 | 40.170 | 52.180 | 0.527 | 2.138 |
| 3 | LSTM painel (juros e confianca; pequena) | 138 | 40.067 | 51.104 | 0.527 | 2.094 |
| 3 | LSTM painel (juros e confianca; grande) | 138 | 40.962 | 51.607 | 0.535 | 2.114 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 138 | 33.953 | 42.209 | 0.447 | 1.729 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 138 | 35.138 | 41.044 | 0.464 | 1.682 |
| 3 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 138 | 33.421 | 42.726 | 0.430 | 1.750 |
| 6 | ARIMA(0,2,3) | 135 | 41.006 | 52.616 | 0.532 | 1.000 |
| 6 | Tendencia (12 meses) | 135 | 51.286 | 67.426 | 0.674 | 1.281 |
| 6 | Regressao linear (so o alvo) | 135 | 44.710 | 58.121 | 0.589 | 1.105 |
| 6 | Regressao linear (alvo + macro) | 135 | 57.370 | 74.976 | 0.758 | 1.425 |
| 6 | Regressao linear (alvo + juros e confianca) | 135 | 45.707 | 59.018 | 0.603 | 1.122 |
| 6 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 135 | 49.905 | 63.121 | 0.661 | 1.200 |
| 6 | LSTM painel (sem macro; base) | 135 | 59.209 | 72.462 | 0.786 | 1.377 |
| 6 | LSTM painel (sem macro; pequena) | 135 | 69.723 | 83.487 | 0.929 | 1.587 |
| 6 | LSTM painel (sem macro; grande) | 135 | 53.716 | 67.339 | 0.709 | 1.280 |
| 6 | LSTM painel (macro completo; base) | 135 | 92.934 | 113.076 | 1.160 | 2.149 |
| 6 | LSTM painel (macro completo; pequena) | 135 | 88.824 | 110.121 | 1.096 | 2.093 |
| 6 | LSTM painel (macro completo; grande) | 135 | 88.510 | 113.089 | 1.088 | 2.149 |
| 6 | LSTM painel (juros e confianca; base) | 135 | 83.311 | 108.539 | 1.092 | 2.063 |
| 6 | LSTM painel (juros e confianca; pequena) | 135 | 83.222 | 105.458 | 1.094 | 2.004 |
| 6 | LSTM painel (juros e confianca; grande) | 135 | 85.212 | 106.417 | 1.110 | 2.023 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 135 | 69.729 | 84.688 | 0.910 | 1.610 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 135 | 71.138 | 82.630 | 0.937 | 1.570 |
| 6 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 135 | 67.915 | 88.638 | 0.870 | 1.685 |
| 12 | ARIMA(0,2,3) | 129 | 91.030 | 117.690 | 1.182 | 1.000 |
| 12 | Tendencia (12 meses) | 129 | 112.433 | 148.575 | 1.465 | 1.262 |
| 12 | Regressao linear (so o alvo) | 129 | 105.663 | 149.982 | 1.400 | 1.274 |
| 12 | Regressao linear (alvo + macro) | 129 | 144.131 | 182.069 | 1.885 | 1.547 |
| 12 | Regressao linear (alvo + juros e confianca) | 129 | 117.891 | 153.185 | 1.576 | 1.302 |
| 12 | Regressao linear (alvo + credito + juros + confianca + IBC-Br) | 129 | 123.128 | 158.070 | 1.631 | 1.343 |
| 12 | LSTM painel (sem macro; base) | 129 | 132.698 | 161.410 | 1.748 | 1.371 |
| 12 | LSTM painel (sem macro; pequena) | 129 | 156.339 | 183.288 | 2.058 | 1.557 |
| 12 | LSTM painel (sem macro; grande) | 129 | 124.282 | 147.353 | 1.629 | 1.252 |
| 12 | LSTM painel (macro completo; base) | 129 | 202.173 | 242.403 | 2.509 | 2.060 |
| 12 | LSTM painel (macro completo; pequena) | 129 | 191.029 | 237.212 | 2.335 | 2.016 |
| 12 | LSTM painel (macro completo; grande) | 129 | 190.063 | 238.196 | 2.322 | 2.024 |
| 12 | LSTM painel (juros e confianca; base) | 129 | 184.572 | 224.978 | 2.400 | 1.912 |
| 12 | LSTM painel (juros e confianca; pequena) | 129 | 180.857 | 223.982 | 2.354 | 1.903 |
| 12 | LSTM painel (juros e confianca; grande) | 129 | 170.733 | 210.332 | 2.219 | 1.787 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; base) | 129 | 149.702 | 177.237 | 1.924 | 1.506 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; pequena) | 129 | 158.425 | 180.380 | 2.048 | 1.533 |
| 12 | LSTM painel (credito + juros + confianca + IBC-Br; grande) | 129 | 150.334 | 191.241 | 1.884 | 1.625 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 1 | 4.722 | 0.000 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 3 | 2.833 | 0.005 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 6 | 2.107 | 0.037 |
| LSTM painel (sem macro; base) | ARIMA(0,2,3) | 12 | 1.967 | 0.051 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 1 | 7.437 | 0.000 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 3 | 5.125 | 0.000 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 6 | 3.453 | 0.001 |
| LSTM painel (macro completo; base) | ARIMA(0,2,3) | 12 | 2.474 | 0.015 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | ARIMA(0,2,3) | 1 | 6.002 | 0.000 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | ARIMA(0,2,3) | 3 | 3.432 | 0.001 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | ARIMA(0,2,3) | 6 | 2.437 | 0.016 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | ARIMA(0,2,3) | 12 | 1.857 | 0.066 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 1 | 3.409 | 0.001 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 3 | 3.005 | 0.003 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 6 | 2.713 | 0.008 |
| Regressao linear (alvo + macro) | ARIMA(0,2,3) | 12 | 2.160 | 0.033 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 1 | 2.366 | 0.019 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 3 | 2.154 | 0.033 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 6 | 1.907 | 0.059 |
| Regressao linear (alvo + juros e confianca) | ARIMA(0,2,3) | 12 | 1.761 | 0.081 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 1 | 2.813 | 0.006 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 3 | 2.471 | 0.015 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 6 | 2.468 | 0.015 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | ARIMA(0,2,3) | 12 | 2.317 | 0.022 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 1 | 2.595 | 0.010 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 3 | 2.629 | 0.010 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 6 | 1.791 | 0.076 |
| LSTM painel (macro completo; base) | LSTM painel (sem macro; base) | 12 | 1.285 | 0.201 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | LSTM painel (sem macro; base) | 1 | -0.460 | 0.646 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | LSTM painel (sem macro; base) | 3 | 0.898 | 0.371 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | LSTM painel (sem macro; base) | 6 | 0.657 | 0.512 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | LSTM painel (sem macro; base) | 12 | 0.412 | 0.681 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | Regressao linear (so o alvo) | 1 | 5.321 | 0.000 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | Regressao linear (so o alvo) | 3 | 3.114 | 0.002 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | Regressao linear (so o alvo) | 6 | 1.987 | 0.049 |
| LSTM painel (credito + juros + confianca + IBC-Br; grande) | Regressao linear (so o alvo) | 12 | 0.617 | 0.539 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 1 | 2.018 | 0.046 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 3 | 2.214 | 0.028 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 6 | 2.051 | 0.042 |
| Regressao linear (alvo + macro) | Regressao linear (so o alvo) | 12 | 0.995 | 0.322 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 1 | 1.132 | 0.260 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 3 | 1.554 | 0.122 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 6 | 0.761 | 0.448 |
| Regressao linear (alvo + juros e confianca) | Regressao linear (so o alvo) | 12 | 0.312 | 0.755 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 1 | 2.068 | 0.041 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 3 | 2.101 | 0.037 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 6 | 1.490 | 0.139 |
| Regressao linear (alvo + credito + juros + confianca + IBC-Br) | Regressao linear (so o alvo) | 12 | 0.407 | 0.685 |

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

