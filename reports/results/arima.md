# ARIMA do FipeZAP (meta 4)

Gerado por `python main.py arima`. Nao editar manualmente. Leitura em `docs/MODELOS_TEMPORAIS.md`.

Alvo em **log** do preco medio de venda do FipeZAP (painel de referencia, 224 meses no nacional, 104 em SJC). Ordem de diferenciacao da analise exploratoria: `d = 2` nos nominais (sem constante) e `d = 0` com constante no preco real. A ordem `(p, q)` e escolhida por AIC (p e q de 0 a 3) **so na janela inicial de treino**.

Avaliacao por **walk-forward** com janela expansiva: em cada mes de origem o modelo e reajustado com os dados ate ela (a ordem fica fixa) e preve 1, 3, 6 e 12 meses a frente da ultima observacao disponivel. Como o FipeZAP do mes `t` so e publicado em `t+1`, na pratica o primeiro mes que se consegue prever a partir do fim do mes `t` e `t+2`. Metricas na escala do preco (RMSE e MAE em R$/m2, MAPE em %), e R2 da variacao acumulada em log.

Benchmarks: ingenuo (ultimo valor); tendencia (crescimento medio de 12 meses); tendencia (ultimo crescimento). Um ARIMA so se justifica se superar a tendencia simples.

Tempo total de execucao: 44 s.

## nacional (nominal) (R$/m2)

Treino inicial: 84 meses; ordem escolhida: **ARIMA(0, 2, 3)**; 140 origens no walk-forward.

### Selecao de ordem (5 menores AIC, janela inicial)

| ordem (p,d,q) | p | q | AIC | BIC |
|---|---|---|---|---|
| (0,2,3) | 0 | 3 | -787.070 | -777.440 |
| (3,2,0) | 3 | 0 | -785.380 | -775.750 |
| (0,2,0) | 0 | 0 | -784.720 | -782.310 |
| (1,2,0) | 1 | 0 | -784.360 | -779.540 |
| (0,2,1) | 0 | 1 | -784.300 | -779.490 |

### Desempenho fora da amostra

| h (meses) | modelo | n origens | RMSE | MAE | MAPE (%) | R2 da variacao | RMSE relativo ao ingenuo |
|---|---|---|---|---|---|---|---|
| 1 | arima | 140 | 7.136 | 5.454 | 0.071 | 0.866 | 0.229 |
| 1 | ingenuo (ultimo valor) | 140 | 31.186 | 24.300 | 0.297 | -1.143 | 1.000 |
| 1 | tendencia (crescimento medio de 12 meses) | 140 | 10.909 | 8.384 | 0.111 | 0.679 | 0.350 |
| 1 | tendencia (ultimo crescimento) | 140 | 7.264 | 5.616 | 0.073 | 0.866 | 0.233 |
| 3 | arima | 138 | 24.409 | 18.389 | 0.238 | 0.824 | 0.265 |
| 3 | ingenuo (ultimo valor) | 138 | 92.102 | 71.539 | 0.870 | -1.184 | 1.000 |
| 3 | tendencia (crescimento medio de 12 meses) | 138 | 32.596 | 24.434 | 0.323 | 0.660 | 0.354 |
| 3 | tendencia (ultimo crescimento) | 138 | 25.652 | 19.607 | 0.252 | 0.812 | 0.279 |
| 6 | arima | 135 | 52.616 | 41.006 | 0.532 | 0.782 | 0.289 |
| 6 | ingenuo (ultimo valor) | 135 | 181.824 | 139.982 | 1.690 | -1.213 | 1.000 |
| 6 | tendencia (crescimento medio de 12 meses) | 135 | 67.426 | 51.286 | 0.674 | 0.620 | 0.371 |
| 6 | tendencia (ultimo crescimento) | 135 | 56.276 | 44.078 | 0.566 | 0.760 | 0.310 |
| 12 | arima | 129 | 117.690 | 91.030 | 1.182 | 0.713 | 0.327 |
| 12 | ingenuo (ultimo valor) | 129 | 360.316 | 272.049 | 3.239 | -1.249 | 1.000 |
| 12 | tendencia (crescimento medio de 12 meses) | 129 | 148.575 | 112.433 | 1.465 | 0.530 | 0.412 |
| 12 | tendencia (ultimo crescimento) | 129 | 121.980 | 94.822 | 1.230 | 0.698 | 0.339 |

### Teste de Diebold-Mariano (estatistica negativa: ARIMA melhor)

| h (meses) | contra | estatistica DM | p (bilateral) | n |
|---|---|---|---|---|
| 1 | ingenuo (ultimo valor) | -10.292 | 0.000 | 140 |
| 1 | tendencia (crescimento medio de 12 meses) | -4.864 | 0.000 | 140 |
| 1 | tendencia (ultimo crescimento) | 0.069 | 0.945 | 140 |
| 3 | ingenuo (ultimo valor) | -5.988 | 0.000 | 138 |
| 3 | tendencia (crescimento medio de 12 meses) | -2.793 | 0.006 | 138 |
| 3 | tendencia (ultimo crescimento) | -1.160 | 0.248 | 138 |
| 6 | ingenuo (ultimo valor) | -4.098 | 0.000 | 135 |
| 6 | tendencia (crescimento medio de 12 meses) | -1.843 | 0.068 | 135 |
| 6 | tendencia (ultimo crescimento) | -1.344 | 0.181 | 135 |
| 12 | ingenuo (ultimo valor) | -2.660 | 0.009 | 129 |
| 12 | tendencia (crescimento medio de 12 meses) | -1.428 | 0.156 | 129 |
| 12 | tendencia (ultimo crescimento) | -0.656 | 0.513 | 129 |

### Ajuste na amostra toda (n = 224)

AIC -2289.6; BIC -2276.0; Ljung-Box (12 lags) nos residuos: p = 0.231.

| parametro | coef | erro-padrao | p |
|---|---|---|---|
| ma.L1 | 0.0510 | 0.0559 | 0.3614 |
| ma.L2 | -0.0615 | 0.0482 | 0.2019 |
| ma.L3 | -0.2565 | 0.0575 | 0.0000 |
| sigma2 | 0.0000 | 0.0000 | 0.0000 |

### Previsao para os proximos 12 meses (R$/m2; IC de 95%)

| mes de referencia | previsao | limite inferior (95%) | limite superior (95%) |
|---|---|---|---|
| 2026-09-01 00:00:00 | 10005.1 | 9978.3 | 10031.9 |
| 2026-10-01 00:00:00 | 10056.3 | 9995.1 | 10117.9 |
| 2026-11-01 00:00:00 | 10106.4 | 10004.1 | 10209.7 |
| 2026-12-01 00:00:00 | 10156.7 | 10012.2 | 10303.4 |
| 2027-01-01 00:00:00 | 10207.3 | 10017.9 | 10400.3 |
| 2027-02-01 00:00:00 | 10258.2 | 10020.9 | 10501.0 |
| 2027-03-01 00:00:00 | 10309.3 | 10021.2 | 10605.6 |
| 2027-04-01 00:00:00 | 10360.6 | 10018.9 | 10714.0 |
| 2027-05-01 00:00:00 | 10412.2 | 10013.9 | 10826.4 |
| 2027-06-01 00:00:00 | 10464.1 | 10006.5 | 10942.6 |
| 2027-07-01 00:00:00 | 10516.2 | 9996.6 | 11062.8 |
| 2027-08-01 00:00:00 | 10568.6 | 9984.5 | 11186.9 |

## SJC (nominal) (R$/m2)

Treino inicial: 60 meses; ordem escolhida: **ARIMA(0, 2, 3)**; 44 origens no walk-forward.

### Selecao de ordem (5 menores AIC, janela inicial)

| ordem (p,d,q) | p | q | AIC | BIC |
|---|---|---|---|---|
| (0,2,3) | 0 | 3 | -505.220 | -496.980 |
| (1,2,3) | 1 | 3 | -504.070 | -493.770 |
| (3,2,0) | 3 | 0 | -503.010 | -494.770 |
| (2,2,2) | 2 | 2 | -502.150 | -491.850 |
| (2,2,3) | 2 | 3 | -502.000 | -489.640 |

### Desempenho fora da amostra

| h (meses) | modelo | n origens | RMSE | MAE | MAPE (%) | R2 da variacao | RMSE relativo ao ingenuo |
|---|---|---|---|---|---|---|---|
| 1 | arima | 44 | 33.810 | 24.988 | 0.316 | 0.411 | 0.428 |
| 1 | ingenuo (ultimo valor) | 44 | 78.967 | 67.194 | 0.828 | -2.055 | 1.000 |
| 1 | tendencia (crescimento medio de 12 meses) | 44 | 48.496 | 36.161 | 0.458 | -0.200 | 0.614 |
| 1 | tendencia (ultimo crescimento) | 44 | 36.667 | 27.017 | 0.340 | 0.324 | 0.464 |
| 3 | arima | 42 | 130.576 | 95.400 | 1.193 | -0.330 | 0.578 |
| 3 | ingenuo (ultimo valor) | 42 | 226.081 | 198.063 | 2.409 | -2.818 | 1.000 |
| 3 | tendencia (crescimento medio de 12 meses) | 42 | 132.438 | 100.506 | 1.264 | -0.350 | 0.586 |
| 3 | tendencia (ultimo crescimento) | 42 | 144.966 | 104.592 | 1.308 | -0.604 | 0.641 |
| 6 | arima | 39 | 283.313 | 223.268 | 2.776 | -2.010 | 0.686 |
| 6 | ingenuo (ultimo valor) | 39 | 412.806 | 381.844 | 4.580 | -5.171 | 1.000 |
| 6 | tendencia (crescimento medio de 12 meses) | 39 | 217.991 | 176.910 | 2.191 | -0.736 | 0.528 |
| 6 | tendencia (ultimo crescimento) | 39 | 333.654 | 254.809 | 3.160 | -3.055 | 0.808 |
| 12 | arima | 33 | 533.101 | 454.998 | 5.455 | -11.882 | 0.696 |
| 12 | ingenuo (ultimo valor) | 33 | 765.645 | 754.413 | 8.864 | -27.653 | 1.000 |
| 12 | tendencia (crescimento medio de 12 meses) | 33 | 322.779 | 290.055 | 3.446 | -3.662 | 0.422 |
| 12 | tendencia (ultimo crescimento) | 33 | 742.011 | 562.786 | 6.756 | -22.554 | 0.969 |

### Teste de Diebold-Mariano (estatistica negativa: ARIMA melhor)

| h (meses) | contra | estatistica DM | p (bilateral) | n |
|---|---|---|---|---|
| 1 | ingenuo (ultimo valor) | -4.157 | 0.000 | 44 |
| 1 | tendencia (crescimento medio de 12 meses) | -2.000 | 0.052 | 44 |
| 1 | tendencia (ultimo crescimento) | -0.979 | 0.333 | 44 |
| 3 | ingenuo (ultimo valor) | -2.999 | 0.005 | 42 |
| 3 | tendencia (crescimento medio de 12 meses) | -0.048 | 0.962 | 42 |
| 3 | tendencia (ultimo crescimento) | -1.121 | 0.269 | 42 |
| 6 | ingenuo (ultimo valor) | -2.247 | 0.031 | 39 |
| 6 | tendencia (crescimento medio de 12 meses) | 1.375 | 0.177 | 39 |
| 6 | tendencia (ultimo crescimento) | -1.506 | 0.140 | 39 |
| 12 | ingenuo (ultimo valor) | -2.128 | 0.041 | 33 |
| 12 | tendencia (crescimento medio de 12 meses) | 1.214 | 0.234 | 33 |
| 12 | tendencia (ultimo crescimento) | -1.493 | 0.145 | 33 |

### Ajuste na amostra toda (n = 104)

AIC -855.8; BIC -845.3; Ljung-Box (12 lags) nos residuos: p = 0.004.

| parametro | coef | erro-padrao | p |
|---|---|---|---|
| ma.L1 | 0.0331 | 0.0827 | 0.6892 |
| ma.L2 | -0.0271 | 0.1025 | 0.7916 |
| ma.L3 | -0.4587 | 0.0711 | 0.0000 |
| sigma2 | 0.0000 | 0.0000 | 0.0000 |

### Previsao para os proximos 12 meses (R$/m2; IC de 95%)

| mes de referencia | previsao | limite inferior (95%) | limite superior (95%) |
|---|---|---|---|
| 2026-09-01 00:00:00 | 9663.2 | 9597.2 | 9729.6 |
| 2026-10-01 00:00:00 | 9714.7 | 9565.2 | 9866.6 |
| 2026-11-01 00:00:00 | 9781.7 | 9531.1 | 10038.9 |
| 2026-12-01 00:00:00 | 9849.1 | 9503.4 | 10207.3 |
| 2027-01-01 00:00:00 | 9916.9 | 9475.1 | 10379.4 |
| 2027-02-01 00:00:00 | 9985.3 | 9444.1 | 10557.4 |
| 2027-03-01 00:00:00 | 10054.1 | 9409.8 | 10742.4 |
| 2027-04-01 00:00:00 | 10123.4 | 9371.9 | 10935.1 |
| 2027-05-01 00:00:00 | 10193.1 | 9330.3 | 11135.7 |
| 2027-06-01 00:00:00 | 10263.3 | 9285.0 | 11344.7 |
| 2027-07-01 00:00:00 | 10334.1 | 9236.2 | 11562.4 |
| 2027-08-01 00:00:00 | 10405.3 | 9184.0 | 11788.9 |

## nacional (real) (R$/m2 constantes de 2008)

Treino inicial: 84 meses; ordem escolhida: **ARIMA(2, 0, 2)** com constante; 140 origens no walk-forward.

### Selecao de ordem (5 menores AIC, janela inicial)

| ordem (p,d,q) | p | q | AIC | BIC |
|---|---|---|---|---|
| (2,0,2) | 2 | 2 | -725.610 | -711.030 |
| (2,0,3) | 2 | 3 | -723.200 | -706.180 |
| (2,0,0) | 2 | 0 | -723.000 | -713.280 |
| (2,0,1) | 2 | 1 | -722.220 | -710.060 |
| (3,0,0) | 3 | 0 | -722.040 | -709.890 |

### Desempenho fora da amostra

| h (meses) | modelo | n origens | RMSE | MAE | MAPE (%) | R2 da variacao | RMSE relativo ao ingenuo |
|---|---|---|---|---|---|---|---|
| 1 | arima | 140 | 13.491 | 10.406 | 0.284 | 0.334 | 0.722 |
| 1 | ingenuo (ultimo valor) | 140 | 18.698 | 14.414 | 0.385 | -0.155 | 1.000 |
| 1 | tendencia (crescimento medio de 12 meses) | 140 | 15.281 | 11.185 | 0.303 | 0.176 | 0.817 |
| 1 | tendencia (ultimo crescimento) | 140 | 14.084 | 10.717 | 0.294 | 0.269 | 0.753 |
| 3 | arima | 138 | 36.787 | 29.255 | 0.807 | 0.188 | 0.758 |
| 3 | ingenuo (ultimo valor) | 138 | 48.504 | 39.181 | 1.049 | -0.228 | 1.000 |
| 3 | tendencia (crescimento medio de 12 meses) | 138 | 38.273 | 28.838 | 0.782 | 0.166 | 0.789 |
| 3 | tendencia (ultimo crescimento) | 138 | 42.455 | 33.309 | 0.921 | -0.095 | 0.875 |
| 6 | arima | 135 | 68.492 | 54.652 | 1.512 | 0.002 | 0.803 |
| 6 | ingenuo (ultimo valor) | 135 | 85.340 | 69.192 | 1.853 | -0.311 | 1.000 |
| 6 | tendencia (crescimento medio de 12 meses) | 135 | 65.370 | 49.692 | 1.343 | 0.150 | 0.766 |
| 6 | tendencia (ultimo crescimento) | 135 | 89.711 | 67.390 | 1.870 | -0.749 | 1.051 |
| 12 | arima | 129 | 101.214 | 76.952 | 2.139 | 0.246 | 0.673 |
| 12 | ingenuo (ultimo valor) | 129 | 150.465 | 118.960 | 3.204 | -0.395 | 1.000 |
| 12 | tendencia (crescimento medio de 12 meses) | 129 | 119.978 | 89.601 | 2.440 | 0.018 | 0.797 |
| 12 | tendencia (ultimo crescimento) | 129 | 165.842 | 123.483 | 3.451 | -1.119 | 1.102 |

### Teste de Diebold-Mariano (estatistica negativa: ARIMA melhor)

| h (meses) | contra | estatistica DM | p (bilateral) | n |
|---|---|---|---|---|
| 1 | ingenuo (ultimo valor) | -3.426 | 0.001 | 140 |
| 1 | tendencia (crescimento medio de 12 meses) | -1.375 | 0.171 | 140 |
| 1 | tendencia (ultimo crescimento) | -2.140 | 0.034 | 140 |
| 3 | ingenuo (ultimo valor) | -1.971 | 0.051 | 138 |
| 3 | tendencia (crescimento medio de 12 meses) | -0.150 | 0.881 | 138 |
| 3 | tendencia (ultimo crescimento) | -4.081 | 0.000 | 138 |
| 6 | ingenuo (ultimo valor) | -0.854 | 0.395 | 135 |
| 6 | tendencia (crescimento medio de 12 meses) | 0.957 | 0.340 | 135 |
| 6 | tendencia (ultimo crescimento) | -3.955 | 0.000 | 135 |
| 12 | ingenuo (ultimo valor) | -1.248 | 0.214 | 129 |
| 12 | tendencia (crescimento medio de 12 meses) | -0.842 | 0.401 | 129 |
| 12 | tendencia (ultimo crescimento) | -3.673 | 0.000 | 129 |

### Ajuste na amostra toda (n = 224)

AIC -1877.9; BIC -1857.4; Ljung-Box (12 lags) nos residuos: p = 0.002.

| parametro | coef | erro-padrao | p |
|---|---|---|---|
| const | 8.1835 | 0.0511 | 0.0000 |
| ar.L1 | 1.9085 | 0.0295 | 0.0000 |
| ar.L2 | -0.9117 | 0.0296 | 0.0000 |
| ma.L1 | -0.1900 | 0.0864 | 0.0279 |
| ma.L2 | -0.0639 | 0.0861 | 0.4581 |
| sigma2 | 0.0000 | 0.0000 | 0.0000 |

### Previsao para os proximos 12 meses (R$/m2; IC de 95%)

| mes de referencia | previsao | limite inferior (95%) | limite superior (95%) |
|---|---|---|---|
| 2026-09-01 00:00:00 | 3604.8 | 3580.2 | 3629.5 |
| 2026-10-01 00:00:00 | 3625.0 | 3576.0 | 3674.7 |
| 2026-11-01 00:00:00 | 3643.4 | 3568.3 | 3720.1 |
| 2026-12-01 00:00:00 | 3660.1 | 3557.4 | 3765.7 |
| 2027-01-01 00:00:00 | 3675.0 | 3543.9 | 3811.1 |
| 2027-02-01 00:00:00 | 3688.5 | 3528.4 | 3855.8 |
| 2027-03-01 00:00:00 | 3700.4 | 3511.2 | 3899.7 |
| 2027-04-01 00:00:00 | 3710.9 | 3492.9 | 3942.5 |
| 2027-05-01 00:00:00 | 3720.1 | 3473.6 | 3984.0 |
| 2027-06-01 00:00:00 | 3728.0 | 3453.7 | 4024.1 |
| 2027-07-01 00:00:00 | 3734.8 | 3433.4 | 4062.6 |
| 2027-08-01 00:00:00 | 3740.4 | 3412.9 | 4099.4 |

## Figuras

- `reports/figures/arima_previsao.png`
- `reports/figures/arima_erros_por_horizonte.png`
