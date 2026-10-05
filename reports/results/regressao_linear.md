# Regressao linear multipla de preco_m2 (VivaReal)

Gerado por `python main.py reg-linear`. Nao editar manualmente. Base: `data/processed/vivareal/*.csv`.

Variaveis: log da area, quartos, banheiros, suites, vagas, comodidades e bairro (bairros com menos de 30 anuncios no treino viram uma categoria); tipo (apartamento e residencial) ou `em_condominio` (casas). Valores ausentes sao imputados pela mediana com indicador de ausencia. **O IPTU nao entra** (unidade nao confirmada).

Variantes: **base** (area, comodos, comodidades, tipo e bairro); **+ condominio informado** (base + indicador de que a taxa de condominio existe); **+ valor do condominio** (base + indicador + valor da taxa (ausente imputado pela mediana)).

Validacoes: holdout aleatorio de 20%; validacao cruzada de 5 particoes; e divisao **temporal** (treino nos 75% de anuncios mais antigos pela data de criacao, teste nos 25% mais recentes). Metricas em R$/m2 (RMSE e MAE), % (MAPE) e R2, sempre na escala original, tambem quando o modelo e ajustado em log.

Cuidado: anuncios do mesmo predio ou loteamento sao parecidos e podem estar no treino e no teste, o que favorece a validacao aleatoria. A divisao temporal e a mais exigente.

## apartamento

### Desempenho

| variante | alvo | validacao | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|---|
| base | log | holdout aleatorio (20%) | 3193 | 799 | 1366.616 | 1036.155 | 17.238 | 0.427 |
| base | log | 5-fold | 3193 | 3992 | 1348.180 | 1032.596 | 16.942 | 0.449 |
| base | log | temporal (teste apos 2026-03-01) | 2994 | 998 | 1340.381 | 1029.990 | 16.706 | 0.465 |
| base | nivel | holdout aleatorio (20%) | 3193 | 799 | 1350.882 | 1030.508 | 17.713 | 0.440 |
| base | nivel | 5-fold | 3193 | 3992 | 1315.380 | 1016.150 | 17.274 | 0.476 |
| base | nivel | temporal (teste apos 2026-03-01) | 2994 | 998 | 1310.974 | 1011.750 | 16.991 | 0.488 |
| + condominio informado | log | holdout aleatorio (20%) | 3193 | 799 | 1366.662 | 1035.085 | 17.220 | 0.427 |
| + condominio informado | log | 5-fold | 3193 | 3992 | 1348.036 | 1033.101 | 16.944 | 0.449 |
| + condominio informado | log | temporal (teste apos 2026-03-01) | 2994 | 998 | 1340.517 | 1030.159 | 16.707 | 0.464 |
| + condominio informado | nivel | holdout aleatorio (20%) | 3193 | 799 | 1351.806 | 1031.244 | 17.720 | 0.439 |
| + condominio informado | nivel | 5-fold | 3193 | 3992 | 1314.850 | 1016.397 | 17.271 | 0.476 |
| + condominio informado | nivel | temporal (teste apos 2026-03-01) | 2994 | 998 | 1311.065 | 1012.374 | 16.996 | 0.488 |
| + valor do condominio | log | holdout aleatorio (20%) | 3193 | 799 | 1368.221 | 1033.604 | 17.209 | 0.425 |
| + valor do condominio | log | 5-fold | 3193 | 3992 | 1348.105 | 1031.377 | 16.922 | 0.449 |
| + valor do condominio | log | temporal (teste apos 2026-03-01) | 2994 | 998 | 1337.677 | 1027.956 | 16.698 | 0.467 |
| + valor do condominio | nivel | holdout aleatorio (20%) | 3193 | 799 | 1352.548 | 1030.144 | 17.716 | 0.438 |
| + valor do condominio | nivel | 5-fold | 3193 | 3992 | 1314.632 | 1015.206 | 17.255 | 0.476 |
| + valor do condominio | nivel | temporal (teste apos 2026-03-01) | 2994 | 998 | 1309.552 | 1011.023 | 16.992 | 0.489 |
| baseline: mediana do bairro | - | holdout aleatorio (20%) | 3193 | 799 | 1505.664 | 1124.819 | 19.954 | 0.304 |
| baseline: mediana do bairro | - | 5-fold | 3193 | 3992 | 1443.640 | 1075.423 | 18.762 | 0.368 |
| baseline: mediana do bairro | - | temporal (teste apos 2026-03-01) | 2994 | 998 | 1456.757 | 1084.957 | 19.065 | 0.368 |

### Coeficientes (variante `+ condominio informado`, alvo log)

R2 na base toda (log): 0.483; R2 ajustado: 0.479; n = 3992; colunas: 37; Breusch-Pagan p = 0.0000 (heterocedasticidade: usar erros robustos, como feito).

| variavel | coef | erro-padrao (HC3) | p | variacao aprox. no R$/m2 (%) |
|---|---|---|---|---|
| const | 10.1889 | 0.1125 | 0.0000 | 2660598.2247 |
| log_area | -0.4687 | 0.0311 | 0.0000 | -37.4202 |
| quartos | 0.0174 | 0.0130 | 0.1813 | 1.7537 |
| banheiros | 0.0148 | 0.0093 | 0.1091 | 1.4931 |
| suites | 0.1657 | 0.0124 | 0.0000 | 18.0222 |
| vagas | 0.1209 | 0.0105 | 0.0000 | 12.8503 |
| comodidades | 0.0065 | 0.0006 | 0.0000 | 0.6495 |
| condominio_informado | -0.0368 | 0.0144 | 0.0109 | -3.6106 |
| missingindicator_suites | -0.2359 | 0.0138 | 0.0000 | -21.0103 |
| missingindicator_vagas | 0.0373 | 0.0218 | 0.0877 | 3.7983 |
| tipo_PENTHOUSE | -0.0297 | 0.0501 | 0.5537 | -2.9235 |
| tipo_infrequent_sklearn | 0.0093 | 0.1399 | 0.9473 | 0.9298 |

Efeitos de bairro (vs. categoria de referencia): 26 coeficientes; de -22% a 54% (tabela completa em `reports/results/eda/regressao_linear_coef_apartamento.csv`).

## casa

### Desempenho

| variante | alvo | validacao | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|---|
| base | log | holdout aleatorio (20%) | 8203 | 2051 | 1258.080 | 927.109 | 21.690 | 0.580 |
| base | log | 5-fold | 8203 | 10254 | 1280.185 | 950.106 | 22.141 | 0.568 |
| base | log | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1364.503 | 996.992 | 22.065 | 0.544 |
| base | nivel | holdout aleatorio (20%) | 8203 | 2051 | 1214.743 | 912.069 | 22.476 | 0.608 |
| base | nivel | 5-fold | 8203 | 10254 | 1238.224 | 941.160 | 23.169 | 0.596 |
| base | nivel | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1306.350 | 975.400 | 22.542 | 0.582 |
| + condominio informado | log | holdout aleatorio (20%) | 8203 | 2051 | 1249.879 | 921.871 | 21.602 | 0.585 |
| + condominio informado | log | 5-fold | 8203 | 10254 | 1274.634 | 946.811 | 22.085 | 0.572 |
| + condominio informado | log | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1364.638 | 997.299 | 21.876 | 0.544 |
| + condominio informado | nivel | holdout aleatorio (20%) | 8203 | 2051 | 1210.892 | 910.356 | 22.452 | 0.611 |
| + condominio informado | nivel | 5-fold | 8203 | 10254 | 1236.353 | 940.449 | 23.169 | 0.597 |
| + condominio informado | nivel | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1305.362 | 971.686 | 22.255 | 0.583 |
| + valor do condominio | log | holdout aleatorio (20%) | 8203 | 2051 | 1207.973 | 888.098 | 20.745 | 0.612 |
| + valor do condominio | log | 5-fold | 8203 | 10254 | 1232.120 | 912.322 | 21.246 | 0.600 |
| + valor do condominio | log | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1302.043 | 959.422 | 21.432 | 0.585 |
| + valor do condominio | nivel | holdout aleatorio (20%) | 8203 | 2051 | 1173.532 | 876.968 | 21.561 | 0.634 |
| + valor do condominio | nivel | 5-fold | 8203 | 10254 | 1199.935 | 906.792 | 22.269 | 0.620 |
| + valor do condominio | nivel | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1258.861 | 942.098 | 21.983 | 0.612 |
| baseline: mediana do bairro | - | holdout aleatorio (20%) | 8203 | 2051 | 1514.706 | 1162.167 | 30.510 | 0.391 |
| baseline: mediana do bairro | - | 5-fold | 8203 | 10254 | 1524.745 | 1169.731 | 30.141 | 0.387 |
| baseline: mediana do bairro | - | temporal (teste apos 2026-02-26) | 7690 | 2564 | 1598.833 | 1208.082 | 29.906 | 0.374 |

### Coeficientes (variante `+ condominio informado`, alvo log)

R2 na base toda (log): 0.625; R2 ajustado: 0.623; n = 10254; colunas: 79; Breusch-Pagan p = 0.0000 (heterocedasticidade: usar erros robustos, como feito).

| variavel | coef | erro-padrao (HC3) | p | variacao aprox. no R$/m2 (%) |
|---|---|---|---|---|
| const | 10.1866 | 0.0489 | 0.0000 | 2654288.0694 |
| log_area | -0.5163 | 0.0093 | 0.0000 | -40.3302 |
| quartos | 0.0546 | 0.0053 | 0.0000 | 5.6148 |
| banheiros | 0.0295 | 0.0033 | 0.0000 | 2.9904 |
| suites | 0.0821 | 0.0045 | 0.0000 | 8.5545 |
| vagas | 0.0388 | 0.0024 | 0.0000 | 3.9565 |
| comodidades | 0.0095 | 0.0006 | 0.0000 | 0.9582 |
| em_condominio | 0.2199 | 0.0082 | 0.0000 | 24.5951 |
| condominio_informado | 0.0429 | 0.0067 | 0.0000 | 4.3829 |
| missingindicator_suites | -0.1617 | 0.0097 | 0.0000 | -14.9302 |
| missingindicator_vagas | 0.0076 | 0.0164 | 0.6416 | 0.7645 |

Efeitos de bairro (vs. categoria de referencia): 69 coeficientes; de -23% a 90% (tabela completa em `reports/results/eda/regressao_linear_coef_casa.csv`).

## residencial

### Desempenho

| variante | alvo | validacao | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|---|
| base | log | holdout aleatorio (20%) | 11396 | 2850 | 1305.078 | 977.071 | 20.173 | 0.592 |
| base | log | 5-fold | 11396 | 14246 | 1322.227 | 993.387 | 21.015 | 0.590 |
| base | log | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1387.627 | 1032.559 | 20.838 | 0.566 |
| base | nivel | holdout aleatorio (20%) | 11396 | 2850 | 1257.955 | 963.403 | 20.859 | 0.621 |
| base | nivel | 5-fold | 11396 | 14246 | 1283.493 | 986.301 | 21.944 | 0.614 |
| base | nivel | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1338.252 | 1013.650 | 21.272 | 0.596 |
| + condominio informado | log | holdout aleatorio (20%) | 11396 | 2850 | 1302.230 | 975.237 | 20.126 | 0.593 |
| + condominio informado | log | 5-fold | 11396 | 14246 | 1318.858 | 991.151 | 20.977 | 0.592 |
| + condominio informado | log | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1388.046 | 1032.536 | 20.702 | 0.565 |
| + condominio informado | nivel | holdout aleatorio (20%) | 11396 | 2850 | 1256.985 | 962.814 | 20.841 | 0.621 |
| + condominio informado | nivel | 5-fold | 11396 | 14246 | 1282.446 | 985.777 | 21.943 | 0.614 |
| + condominio informado | nivel | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1337.503 | 1011.038 | 21.100 | 0.596 |
| + valor do condominio | log | holdout aleatorio (20%) | 11396 | 2850 | 1279.632 | 958.900 | 19.728 | 0.607 |
| + valor do condominio | log | 5-fold | 11396 | 14246 | 1293.221 | 970.500 | 20.487 | 0.608 |
| + valor do condominio | log | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1344.012 | 1006.024 | 20.522 | 0.593 |
| + valor do condominio | nivel | holdout aleatorio (20%) | 11396 | 2850 | 1236.132 | 944.497 | 20.350 | 0.634 |
| + valor do condominio | nivel | 5-fold | 11396 | 14246 | 1260.758 | 964.184 | 21.382 | 0.627 |
| + valor do condominio | nivel | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1309.143 | 992.998 | 21.053 | 0.613 |
| baseline: mediana do bairro | - | holdout aleatorio (20%) | 11396 | 2850 | 1672.196 | 1312.125 | 30.023 | 0.329 |
| baseline: mediana do bairro | - | 5-fold | 11396 | 14246 | 1677.853 | 1311.766 | 31.419 | 0.340 |
| baseline: mediana do bairro | - | temporal (teste apos 2026-02-27) | 10684 | 3562 | 1719.190 | 1339.054 | 31.171 | 0.333 |

### Coeficientes (variante `+ condominio informado`, alvo log)

R2 na base toda (log): 0.651; R2 ajustado: 0.649; n = 14246; colunas: 91; Breusch-Pagan p = 0.0000 (heterocedasticidade: usar erros robustos, como feito).

| variavel | coef | erro-padrao (HC3) | p | variacao aprox. no R$/m2 (%) |
|---|---|---|---|---|
| const | 10.3131 | 0.0367 | 0.0000 | 3012337.2181 |
| log_area | -0.5123 | 0.0088 | 0.0000 | -40.0872 |
| quartos | 0.0585 | 0.0049 | 0.0000 | 6.0222 |
| banheiros | 0.0275 | 0.0030 | 0.0000 | 2.7893 |
| suites | 0.0883 | 0.0043 | 0.0000 | 9.2342 |
| vagas | 0.0418 | 0.0023 | 0.0000 | 4.2684 |
| comodidades | 0.0090 | 0.0004 | 0.0000 | 0.9070 |
| condominio_informado | 0.0384 | 0.0061 | 0.0000 | 3.9130 |
| missingindicator_suites | -0.1765 | 0.0075 | 0.0000 | -16.1829 |
| missingindicator_vagas | 0.0048 | 0.0137 | 0.7276 | 0.4775 |
| tipo_CONDOMINIUM | 0.0929 | 0.0103 | 0.0000 | 9.7401 |
| tipo_HOME | -0.1265 | 0.0085 | 0.0000 | -11.8797 |
| tipo_PENTHOUSE | 0.0388 | 0.0459 | 0.3984 | 3.9547 |
| tipo_infrequent_sklearn | -0.0174 | 0.0944 | 0.8539 | -1.7235 |

Efeitos de bairro (vs. categoria de referencia): 78 coeficientes; de -25% a 83% (tabela completa em `reports/results/eda/regressao_linear_coef_residencial.csv`).

## Figuras

- `reports/figures/reg_linear_apartamento.png`
- `reports/figures/reg_linear_casa.png`
- `reports/figures/reg_linear_residencial.png`
