# ARIMA: combinacao, ARIMAX, cidades vizinhas e avaliacao ampliada

Gerado por `python main.py arima-plus`. Nao editar manualmente. Leitura em `docs/MODELOS_TEMPORAIS.md`.

Mesmo walk-forward do ARIMA (`docs/MODELOS_TEMPORAIS.md`), ordem (0, 2, 3) fixa, alvos nominais. Comparacao **contra o ARIMA(0,2,3)** (RMSE relativo menor que 1 = melhor que o ARIMA). Modelos:

- **Tendencia (12 meses):** crescimento medio dos ultimos 12 meses; **Combinacao ARIMA + tendencia:** media simples dos dois.
- **ARIMAX:** ARMA(0,3) em d2 do log do preco com preditores estacionarios **defasados 12 meses** (conhecidos em todos os horizontes ate 12) e previsao reintegrada ao nivel. Os preditores usam a diferenciacao decidida na analise exploratoria.

Tempo total: 115 s.

## nacional (nominal)

### Erro por horizonte (MAPE em %, RMSE em R$/m2 e RMSE relativo ao ARIMA)

| h (meses) | modelo | n origens | MAPE (%) | RMSE | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 140 | 0.071 | 7.136 | 1.000 |
| 1 | Tendencia (12 meses) | 140 | 0.111 | 10.909 | 1.529 |
| 1 | Combinacao ARIMA + tendencia | 140 | 0.080 | 7.935 | 1.112 |
| 1 | ARIMAX credito | 129 | 0.071 | 6.815 | 0.955 |
| 1 | ARIMAX juros e confianca | 129 | 0.074 | 6.914 | 0.969 |
| 1 | ARIMAX credito + juros + confianca + IBC-Br | 129 | 0.075 | 6.928 | 0.971 |
| 3 | ARIMA(0,2,3) | 138 | 0.238 | 24.409 | 1.000 |
| 3 | Tendencia (12 meses) | 138 | 0.323 | 32.596 | 1.335 |
| 3 | Combinacao ARIMA + tendencia | 138 | 0.253 | 25.788 | 1.056 |
| 3 | ARIMAX credito | 129 | 0.234 | 22.907 | 0.938 |
| 3 | ARIMAX juros e confianca | 129 | 0.241 | 23.330 | 0.956 |
| 3 | ARIMAX credito + juros + confianca + IBC-Br | 129 | 0.249 | 23.570 | 0.966 |
| 6 | ARIMA(0,2,3) | 135 | 0.532 | 52.616 | 1.000 |
| 6 | Tendencia (12 meses) | 135 | 0.674 | 67.426 | 1.281 |
| 6 | Combinacao ARIMA + tendencia | 135 | 0.534 | 55.219 | 1.049 |
| 6 | ARIMAX credito | 129 | 0.525 | 51.072 | 0.971 |
| 6 | ARIMAX juros e confianca | 129 | 0.550 | 52.645 | 1.001 |
| 6 | ARIMAX credito + juros + confianca + IBC-Br | 129 | 0.570 | 53.420 | 1.015 |
| 12 | ARIMA(0,2,3) | 129 | 1.182 | 117.690 | 1.000 |
| 12 | Tendencia (12 meses) | 129 | 1.465 | 148.575 | 1.262 |
| 12 | Combinacao ARIMA + tendencia | 129 | 1.228 | 125.301 | 1.065 |
| 12 | ARIMAX credito | 129 | 1.190 | 118.219 | 1.005 |
| 12 | ARIMAX juros e confianca | 129 | 1.266 | 123.757 | 1.052 |
| 12 | ARIMAX credito + juros + confianca + IBC-Br | 129 | 1.318 | 125.941 | 1.070 |

### Diebold-Mariano contra o ARIMA (estatistica negativa: o modelo e melhor que o ARIMA)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) | n |
|---|---|---|---|---|---|
| Tendencia (12 meses) | ARIMA(0,2,3) | 1 | 4.864 | 0.000 | 140 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 1 | 2.104 | 0.037 | 140 |
| ARIMAX credito | ARIMA(0,2,3) | 1 | -1.245 | 0.216 | 129 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 1 | 0.161 | 0.872 | 129 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 1 | 0.193 | 0.847 | 129 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 3 | 2.793 | 0.006 | 138 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 3 | 1.325 | 0.187 | 138 |
| ARIMAX credito | ARIMA(0,2,3) | 3 | -0.022 | 0.983 | 129 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 3 | 0.570 | 0.569 | 129 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 3 | 0.997 | 0.320 | 129 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 6 | 1.843 | 0.068 | 135 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 6 | 0.911 | 0.364 | 135 |
| ARIMAX credito | ARIMA(0,2,3) | 6 | 0.393 | 0.695 | 129 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 6 | 0.908 | 0.366 | 129 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 6 | 1.365 | 0.175 | 129 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 12 | 1.428 | 0.156 | 129 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 12 | 0.856 | 0.393 | 129 |
| ARIMAX credito | ARIMA(0,2,3) | 12 | 0.290 | 0.772 | 129 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 12 | 0.839 | 0.403 | 129 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 12 | 1.244 | 0.216 | 129 |

### Cobertura e largura dos intervalos de previsao do ARIMA (nominal 95%)

| h (meses) | cobertura do IC 95% (%) | largura media do IC (% do preco) | n |
|---|---|---|---|
| 1 | 99.29 | 0.62 | 140 |
| 3 | 100.00 | 2.38 | 138 |
| 6 | 100.00 | 5.56 | 135 |
| 12 | 100.00 | 13.78 | 129 |

### Erro por periodo (MAPE em %; 3 e 12 meses)

| periodo | h (meses) | modelo | n | MAPE (%) |
|---|---|---|---|---|
| origens ate 2019 | 3 | ARIMA(0,2,3) | 61 | 0.213 |
| origens ate 2019 | 3 | Tendencia (12 meses) | 61 | 0.324 |
| origens ate 2019 | 3 | Combinacao ARIMA + tendencia | 61 | 0.238 |
| origens ate 2019 | 12 | ARIMA(0,2,3) | 61 | 1.226 |
| origens ate 2019 | 12 | Tendencia (12 meses) | 61 | 1.379 |
| origens ate 2019 | 12 | Combinacao ARIMA + tendencia | 61 | 1.202 |
| origens de 2020 em diante | 3 | ARIMA(0,2,3) | 77 | 0.257 |
| origens de 2020 em diante | 3 | Tendencia (12 meses) | 77 | 0.323 |
| origens de 2020 em diante | 3 | Combinacao ARIMA + tendencia | 77 | 0.264 |
| origens de 2020 em diante | 12 | ARIMA(0,2,3) | 68 | 1.143 |
| origens de 2020 em diante | 12 | Tendencia (12 meses) | 68 | 1.543 |
| origens de 2020 em diante | 12 | Combinacao ARIMA + tendencia | 68 | 1.252 |

## SJC (nominal)

### Erro por horizonte (MAPE em %, RMSE em R$/m2 e RMSE relativo ao ARIMA)

| h (meses) | modelo | n origens | MAPE (%) | RMSE | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 44 | 0.316 | 33.810 | 1.000 |
| 1 | Tendencia (12 meses) | 44 | 0.458 | 48.496 | 1.434 |
| 1 | Combinacao ARIMA + tendencia | 44 | 0.337 | 36.230 | 1.072 |
| 1 | ARIMAX credito | 33 | 0.337 | 34.564 | 1.022 |
| 1 | ARIMAX juros e confianca | 33 | 0.361 | 36.441 | 1.078 |
| 1 | ARIMAX credito + juros + confianca + IBC-Br | 33 | 0.347 | 36.365 | 1.076 |
| 3 | ARIMA(0,2,3) | 42 | 1.193 | 130.576 | 1.000 |
| 3 | Tendencia (12 meses) | 42 | 1.264 | 132.438 | 1.014 |
| 3 | Combinacao ARIMA + tendencia | 42 | 1.105 | 119.540 | 0.915 |
| 3 | ARIMAX credito | 33 | 1.269 | 136.794 | 1.048 |
| 3 | ARIMAX juros e confianca | 33 | 1.363 | 142.435 | 1.091 |
| 3 | ARIMAX credito + juros + confianca + IBC-Br | 33 | 1.278 | 140.297 | 1.074 |
| 6 | ARIMA(0,2,3) | 39 | 2.776 | 283.313 | 1.000 |
| 6 | Tendencia (12 meses) | 39 | 2.191 | 217.991 | 0.769 |
| 6 | Combinacao ARIMA + tendencia | 39 | 2.203 | 229.422 | 0.810 |
| 6 | ARIMAX credito | 33 | 2.861 | 288.665 | 1.019 |
| 6 | ARIMAX juros e confianca | 33 | 2.993 | 294.053 | 1.038 |
| 6 | ARIMAX credito + juros + confianca + IBC-Br | 33 | 2.838 | 292.739 | 1.033 |
| 12 | ARIMA(0,2,3) | 33 | 5.455 | 533.101 | 1.000 |
| 12 | Tendencia (12 meses) | 33 | 3.446 | 322.779 | 0.605 |
| 12 | Combinacao ARIMA + tendencia | 33 | 3.790 | 375.134 | 0.704 |
| 12 | ARIMAX credito | 33 | 4.769 | 463.649 | 0.870 |
| 12 | ARIMAX juros e confianca | 33 | 4.935 | 504.686 | 0.947 |
| 12 | ARIMAX credito + juros + confianca + IBC-Br | 33 | 4.606 | 463.266 | 0.869 |

### Diebold-Mariano contra o ARIMA (estatistica negativa: o modelo e melhor que o ARIMA)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) | n |
|---|---|---|---|---|---|
| Tendencia (12 meses) | ARIMA(0,2,3) | 1 | 2.000 | 0.052 | 44 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 1 | 0.665 | 0.509 | 44 |
| ARIMAX credito | ARIMA(0,2,3) | 1 | -0.784 | 0.439 | 33 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 1 | -0.056 | 0.955 | 33 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 1 | 0.066 | 0.948 | 33 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 3 | 0.048 | 0.962 | 42 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 3 | -1.026 | 0.311 | 42 |
| ARIMAX credito | ARIMA(0,2,3) | 3 | -1.047 | 0.303 | 33 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 3 | -0.292 | 0.772 | 33 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 3 | -0.438 | 0.664 | 33 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 6 | -1.375 | 0.177 | 39 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 6 | -1.745 | 0.089 | 39 |
| ARIMAX credito | ARIMA(0,2,3) | 6 | -1.295 | 0.205 | 33 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 6 | -0.818 | 0.419 | 33 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 6 | -1.028 | 0.312 | 33 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 12 | -1.214 | 0.234 | 33 |
| Combinacao ARIMA + tendencia | ARIMA(0,2,3) | 12 | -1.469 | 0.152 | 33 |
| ARIMAX credito | ARIMA(0,2,3) | 12 | -1.071 | 0.292 | 33 |
| ARIMAX juros e confianca | ARIMA(0,2,3) | 12 | -0.667 | 0.510 | 33 |
| ARIMAX credito + juros + confianca + IBC-Br | ARIMA(0,2,3) | 12 | -1.834 | 0.076 | 33 |

### Cobertura e largura dos intervalos de previsao do ARIMA (nominal 95%)

| h (meses) | cobertura do IC 95% (%) | largura media do IC (% do preco) | n |
|---|---|---|---|
| 1 | 90.91 | 1.37 | 44 |
| 3 | 85.71 | 5.24 | 42 |
| 6 | 84.62 | 11.50 | 39 |
| 12 | 100.00 | 26.55 | 33 |

### Erro por periodo (MAPE em %; 3 e 12 meses)

| periodo | h (meses) | modelo | n | MAPE (%) |
|---|---|---|---|---|
| origens de 2020 em diante | 3 | ARIMA(0,2,3) | 42 | 1.193 |
| origens de 2020 em diante | 3 | Tendencia (12 meses) | 42 | 1.264 |
| origens de 2020 em diante | 3 | Combinacao ARIMA + tendencia | 42 | 1.105 |
| origens de 2020 em diante | 12 | ARIMA(0,2,3) | 33 | 5.455 |
| origens de 2020 em diante | 12 | Tendencia (12 meses) | 33 | 3.446 |
| origens de 2020 em diante | 12 | Combinacao ARIMA + tendencia | 33 | 3.790 |

## Cidades que antecipam o FipeZAP de nacional (nominal)? (50 cidades; d2 do log, lags de 1 a 6)

Limiar de Bonferroni: p < 0.00017. Dez menores p:

| cidade | n | maior |r| (lag 1-6) | lag do maior |r| | menor p (Granger) | lag do menor p |
|---|---|---|---|---|---|
| Salvador | 191 | 0.1633 | 3 | 0.0004 | 3 |
| Guarulhos | 163 | 0.2191 | 1 | 0.0010 | 6 |
| Niterói | 175 | 0.2346 | 1 | 0.0017 | 2 |
| João Pessoa | 102 | 0.2951 | 2 | 0.0029 | 2 |
| Londrina | 102 | 0.2453 | 1 | 0.0038 | 5 |
| Curitiba | 169 | 0.1599 | 5 | 0.0072 | 6 |
| São Paulo | 222 | 0.1874 | 2 | 0.0092 | 2 |
| Recife | 193 | 0.2091 | 4 | 0.0093 | 1 |
| Osasco | 163 | 0.1626 | 6 | 0.0108 | 6 |
| Joinville | 102 | 0.2945 | 4 | 0.0109 | 1 |

## Cidades que antecipam o FipeZAP de SJC (nominal)? (50 cidades; d2 do log, lags de 1 a 6)

Limiar de Bonferroni: p < 0.00017. Dez menores p:

| cidade | n | maior |r| (lag 1-6) | lag do maior |r| | menor p (Granger) | lag do menor p |
|---|---|---|---|---|---|
| Blumenau | 102 | 0.2602 | 6 | 0.0153 | 1 |
| Campo Grande | 102 | 0.2675 | 2 | 0.0238 | 4 |
| Novo Hamburgo | 102 | 0.1893 | 6 | 0.0268 | 2 |
| Porto Alegre | 102 | 0.1980 | 4 | 0.0340 | 3 |
| Salvador | 102 | 0.1952 | 4 | 0.0359 | 2 |
| Balneário Camboriú | 102 | 0.1962 | 2 | 0.0413 | 2 |
| Caxias do Sul | 102 | 0.2365 | 3 | 0.0475 | 4 |
| Goiânia | 102 | 0.1820 | 1 | 0.0615 | 1 |
| Brasília | 102 | 0.2238 | 4 | 0.0675 | 1 |
| Florianópolis | 102 | 0.1912 | 3 | 0.0908 | 1 |

## Figuras

- `reports/figures/arima_plus_comparacao.png`
