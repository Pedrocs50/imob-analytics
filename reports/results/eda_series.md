# Analise exploratoria: series temporais

Gerado por `python main.py eda-series`. Nao editar manualmente. A leitura dos resultados esta em
`docs/ANALISE_EXPLORATORIA.md`. Relacoes calculadas em data de **referencia** (painel `*_referencia`).
Correlacao cruzada e Granger usam series **estacionarias** (secoes 3 e 9); a coluna `utilizavel`
indica se o lag respeita a defasagem de publicacao (lag >= L+1 para prever o mes seguinte).

## 1. Series usadas (em nivel)

| serie | coluna | n | inicio | fim | media | desvio | min | max | defasagem L |
|---|---|---|---|---|---|---|---|---|---|
| nacional (nominal) | fipezap_nacional_res_venda_preco_m2 | 224 | 2008-01 | 2026-08 | 6457.539 | 1968.736 | 2228.662 | 9953.595 | 1 |
| nacional (real) | fipezap_nacional_res_venda_preco_m2_real | 224 | 2008-01 | 2026-08 | 3630.986 | 577.537 | 2228.662 | 4626.754 | 1 |
| SJC (nominal) | fipezap_sjc_res_venda_preco_m2 | 104 | 2018-01 | 2026-08 | 6439.575 | 1666.850 | 4586.122 | 9615.214 | 1 |
| SJC (real) | fipezap_sjc_res_venda_preco_m2_real | 104 | 2018-01 | 2026-08 | 2805.711 | 339.768 | 2430.916 | 3459.462 | 1 |
| Meta Selic (% a.a.) | bcb_selic_meta | 224 | 2008-01 | 2026-08 | 10.235 | 3.485 | 2.000 | 15.000 | 0 |
| Selic real no mes (%) | selic_real_mes | 224 | 2008-01 | 2026-08 | 0.340 | 0.452 | -1.174 | 1.722 | 1 |
| IPCA variacao mensal (% a.m.) | bcb_ipca | 224 | 2008-01 | 2026-08 | 0.460 | 0.345 | -0.680 | 1.620 | 1 |
| IGP-M variacao mensal (% a.m.) | bcb_igpm | 224 | 2008-01 | 2026-08 | 0.528 | 0.902 | -1.930 | 4.340 | 0 |
| INCC-M variacao mensal (% a.m.) | bcb_incc | 224 | 2008-01 | 2026-08 | 0.569 | 0.509 | -0.250 | 2.940 | 0 |
| Dolar (venda) media mensal (R$/US$) | bcb_ptax | 224 | 2008-01 | 2026-08 | 3.561 | 1.454 | 1.564 | 6.097 | 0 |
| IBC-Br dessazonalizado (indice) | bcb_ibcbr | 223 | 2008-01 | 2026-07 | 98.458 | 6.478 | 80.532 | 118.017 | 2 |
| Saldo credito imobiliario PF (direcionado) (R$ milhoes) | bcb_credimob_saldo | 224 | 2008-01 | 2026-08 | 569799.295 | 376125.355 | 43972.000 | 1430825.000 | 1 |
| Juros financ. imobiliario - taxas de mercado (% a.m.) | bcb_credimob_juros_mercado | 186 | 2011-03 | 2026-08 | 0.978 | 0.218 | 0.600 | 1.500 | 1 |
| Juros financ. imobiliario - taxas reguladas (% a.m.) | bcb_credimob_juros_regulada | 186 | 2011-03 | 2026-08 | 0.698 | 0.099 | 0.530 | 0.890 | 1 |
| Confianca do consumidor (Fecomercio-SP) (indice) | ipea_icc | 224 | 2008-01 | 2026-08 | 125.234 | 21.374 | 84.550 | 170.180 | 1 |
| Desocupacao Brasil - mensalizada (%) | ipea_desocupacao_br_mensal | 175 | 2012-01 | 2026-07 | 9.539 | 2.874 | 5.100 | 15.200 | 2 |

## 2. Crescimento medio por ano (% ao mes)

| ano | FipeZAP nacional (nominal) | FipeZAP nacional (real) | FipeZAP SJC (nominal) | IPCA | Selic meta (media, % a.a.) |
|---|---|---|---|---|---|
| 2008 | 1.244 | 0.772 |  | 0.479 | 12.542 |
| 2009 | 1.598 | 1.246 |  | 0.352 | 9.917 |
| 2010 | 1.983 | 1.504 |  | 0.480 | 10.000 |
| 2011 | 1.947 | 1.422 |  | 0.527 | 11.792 |
| 2012 | 1.021 | 0.548 |  | 0.474 | 8.458 |
| 2013 | 1.073 | 0.594 |  | 0.480 | 8.438 |
| 2014 | 0.541 | 0.023 |  | 0.519 | 11.021 |
| 2015 | 0.110 | -0.735 |  | 0.849 | 13.583 |
| 2016 | 0.048 | -0.460 |  | 0.510 | 14.167 |
| 2017 | -0.044 | -0.286 |  | 0.243 | 9.917 |
| 2018 | -0.017 | -0.324 | 0.167 | 0.308 | 6.562 |
| 2019 | 0.000 | -0.351 | 0.261 | 0.353 | 5.958 |
| 2020 | 0.300 | -0.068 | 0.291 | 0.370 | 2.812 |
| 2021 | 0.429 | -0.370 | 0.982 | 0.802 | 4.812 |
| 2022 | 0.498 | 0.029 | 1.479 | 0.472 | 12.625 |
| 2023 | 0.417 | 0.040 | 0.758 | 0.378 | 13.250 |
| 2024 | 0.621 | 0.228 | 0.964 | 0.394 | 10.958 |
| 2025 | 0.527 | 0.179 | 0.751 | 0.349 | 14.562 |
| 2026 | 0.423 | 0.040 | 0.795 | 0.384 | 14.531 |

## 3. Estacionariedade dos alvos (ADF e KPSS)

Estacionaria = ADF rejeita a raiz unitaria (p<0,05) e KPSS nao rejeita a estacionariedade (p>0,05).

| serie | transformacao | n | ADF p | KPSS p | estacionaria |
|---|---|---|---|---|---|
| nacional (nominal) | log (nivel) | 224 | 0.156 | 0.010 | nao |
| nacional (nominal) | d1: var. mensal (dlog) | 223 | 0.399 | 0.010 | nao |
| nacional (nominal) | d2: dif. da var. mensal | 222 | 0.006 | 0.100 | sim |
| nacional (real) | log (nivel) | 224 | 0.002 | 0.062 | sim |
| nacional (real) | d1: var. mensal (dlog) | 223 | 0.587 | 0.010 | nao |
| nacional (real) | d2: dif. da var. mensal | 222 | 0.000 | 0.100 | sim |
| SJC (nominal) | log (nivel) | 104 | 0.804 | 0.010 | nao |
| SJC (nominal) | d1: var. mensal (dlog) | 103 | 0.538 | 0.047 | nao |
| SJC (nominal) | d2: dif. da var. mensal | 102 | 0.000 | 0.100 | sim |
| SJC (real) | log (nivel) | 104 | 0.991 | 0.010 | nao |
| SJC (real) | d1: var. mensal (dlog) | 103 | 0.000 | 0.036 | conflito |
| SJC (real) | d2: dif. da var. mensal | 102 | 0.000 | 0.100 | sim |

Transformacao minima que passa nos dois testes:

- **nacional (nominal)**: d2: dif. da var. mensal
- **nacional (real)**: log (nivel)
- **SJC (nominal)**: d2: dif. da var. mensal
- **SJC (real)**: d2: dif. da var. mensal

## 4. Autocorrelacao

O FipeZAP e media movel trimestral e a variacao mensal e muito persistente; a serie estacionaria e a usada nos passos seguintes.

| serie | transformacao estacionaria | autocorr. lag 1 (var. mensal) | autocorr. lag 1 (estacionaria) | autocorr. lag 2 (estacionaria) | autocorr. lag 3 (estacionaria) | Ljung-Box p12 (var. mensal) | Ljung-Box p12 (estacionaria) |
|---|---|---|---|---|---|---|---|
| nacional (nominal) | dif. da var. mensal (d2) | 0.976 | 0.068 | -0.100 | -0.224 | 0.000 | 0.010 |
| SJC (nominal) | dif. da var. mensal (d2) | 0.813 | 0.048 | -0.033 | -0.353 | 0.000 | 0.000 |

Figura: `reports/figures/eda_acf_pacf_alvo.png`

## 5. Sazonalidade

| serie | n | forca sazonal (STL, 0-1) | Kruskal-Wallis p (mes do ano) |
|---|---|---|---|
| nacional (nominal) | 223 | 0.071 | 1.000 |
| SJC (nominal) | 103 | 0.032 | 0.995 |

Nao ha indicio de sazonalidade (forca < 0,3 e Kruskal-Wallis p >= 0,05); nenhum grafico foi gerado.

## 6. Sao Jose dos Campos x indice nacional

| lag (SJC em t x nacional em t-k) | corr. var. mensal (nao estacionaria) | corr. estacionaria (d2) | n (estacionaria) |
|---|---|---|---|
| -6 | 0.461 | 0.227 | 96 |
| -5 | 0.466 | 0.024 | 97 |
| -4 | 0.466 | 0.011 | 98 |
| -3 | 0.468 | 0.018 | 99 |
| -2 | 0.465 | -0.017 | 100 |
| -1 | 0.466 | 0.046 | 101 |
| 0 | 0.451 | 0.021 | 102 |
| 1 | 0.430 | 0.127 | 101 |
| 2 | 0.376 | -0.157 | 100 |
| 3 | 0.355 | -0.070 | 99 |
| 4 | 0.348 | -0.164 | 98 |
| 5 | 0.390 | 0.087 | 97 |
| 6 | 0.409 | -0.071 | 96 |

## 7. Faixas de dormitorios (indice nacional)

| faixa | preco final / inicial | crescimento mensal medio (%) | desvio (%) | corr. com o total |
|---|---|---|---|---|
| total | 4.466 | 0.671 | 0.655 | 1.000 |
| 1d | 5.053 | 0.726 | 0.764 | 0.945 |
| 2d | 4.504 | 0.675 | 0.677 | 0.979 |
| 3d | 4.255 | 0.649 | 0.638 | 0.980 |
| 4d | 3.824 | 0.601 | 0.598 | 0.921 |

## 8. Meses atipicos (z robusto > 3,5)

| serie | mes | var. mensal (%) | z robusto |
|---|---|---|---|
| nacional (nominal) | 2011-04 | 2.650 | 3.536 |
| SJC (nominal) | 2022-01 | 2.705 | 3.688 |
| SJC (nominal) | 2022-02 | 2.808 | 3.868 |

## 9. Preditores e estacionariedade

Transformacao inicial e diferencas extras aplicadas ate ADF e KPSS concordarem.

| preditor | coluna | transformacao inicial | diferencas extras | estacionaria | n | inicio | defasagem L | ADF p (antes) | KPSS p (antes) | ADF p (final) | KPSS p (final) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Selic meta | bcb_selic_meta | 1a diferenca | 0 | sim | 223 | 2008-02 | 0 | 0.033 | 0.100 | 0.033 | 0.100 |
| Selic real no mes | selic_real_mes | nivel | 0 | sim | 224 | 2008-01 | 1 | 0.000 | 0.100 | 0.000 | 0.100 |
| IPCA mensal | bcb_ipca | nivel | 0 | sim | 224 | 2008-01 | 1 | 0.000 | 0.100 | 0.000 | 0.100 |
| IGP-M mensal | bcb_igpm | nivel | 0 | sim | 224 | 2008-01 | 0 | 0.000 | 0.100 | 0.000 | 0.100 |
| INCC mensal | bcb_incc | nivel | 0 | sim | 224 | 2008-01 | 0 | 0.010 | 0.100 | 0.010 | 0.100 |
| Dolar PTAX | bcb_ptax | var. % (dlog) | 0 | sim | 223 | 2008-02 | 0 | 0.000 | 0.100 | 0.000 | 0.100 |
| IBC-Br | bcb_ibcbr | var. % (dlog) | 0 | sim | 222 | 2008-02 | 2 | 0.001 | 0.100 | 0.001 | 0.100 |
| Saldo cred. imob. | bcb_credimob_saldo | var. % (dlog) | 1 | sim | 222 | 2008-03 | 1 | 0.629 | 0.010 | 0.000 | 0.100 |
| Juros financ. imob. (mercado) | bcb_credimob_juros_mercado | 1a diferenca | 0 | sim | 185 | 2011-04 | 1 | 0.000 | 0.100 | 0.000 | 0.100 |
| Juros financ. imob. (regulada) | bcb_credimob_juros_regulada | 1a diferenca | 0 | sim | 185 | 2011-04 | 1 | 0.029 | 0.100 | 0.029 | 0.100 |
| Confianca do consumidor | ipea_icc | 1a diferenca | 0 | sim | 223 | 2008-02 | 1 | 0.004 | 0.100 | 0.004 | 0.100 |
| Desocupacao Brasil | ipea_desocupacao_br_mensal | 1a diferenca | 1 | sim | 173 | 2012-03 | 2 | 0.098 | 0.100 | 0.000 | 0.100 |

Pares de preditores (ja estacionarios) com |correlacao| >= 0,5:

| variavel A | variavel B | correlacao (Spearman) |
|---|---|---|
| Selic real no mes | IPCA mensal | -0.757 |
| Selic real no mes | IGP-M mensal | -0.550 |
| Juros financ. imob. (mercado) | Juros financ. imob. (regulada) | 0.527 |

## 10. Correlacao cruzada com o FipeZAP nacional (dif. da var. mensal (d2))

Maiores correlacoes significativas e utilizaveis (limiar conservador com n/3):

Nenhuma correlacao significativa e utilizavel.

Comparativo: maior |r| com as series como vinham (nao estacionarias) e depois de estacionarizar:

| preditor | maior |r| bruta | lag (bruta) | maior |r| estacionaria | lag (estacionaria) |
|---|---|---|---|---|
| Saldo cred. imob. | 0.846 | 3 | 0.179 | 3 |
| Desocupacao Brasil | 0.152 | 12 | 0.109 | 3 |
| INCC mensal | 0.118 | 1 | 0.177 | 7 |
| Dolar PTAX | 0.104 | 5 | 0.052 | 9 |
| Selic meta | 0.096 | 1 | 0.105 | 5 |
| Confianca do consumidor | 0.074 | 10 | 0.172 | 9 |
| Juros financ. imob. (regulada) | 0.074 | 12 | 0.153 | 12 |
| IBC-Br | 0.063 | 4 | 0.172 | 10 |
| Juros financ. imob. (mercado) | 0.062 | 2 | 0.122 | 12 |
| IPCA mensal | 0.053 | 6 | 0.195 | 8 |
| Selic real no mes | 0.047 | 11 | 0.147 | 8 |
| IGP-M mensal | 0.030 | 12 | 0.093 | 5 |

## 10. Correlacao cruzada com o FipeZAP SJC (dif. da var. mensal (d2))

Maiores correlacoes significativas e utilizaveis (limiar conservador com n/3):

Nenhuma correlacao significativa e utilizavel.

Comparativo: maior |r| com as series como vinham (nao estacionarias) e depois de estacionarizar:

| preditor | maior |r| bruta | lag (bruta) | maior |r| estacionaria | lag (estacionaria) |
|---|---|---|---|---|
| INCC mensal | 0.545 | 10 | 0.185 | 7 |
| Saldo cred. imob. | 0.535 | 9 | 0.148 | 9 |
| IPCA mensal | 0.449 | 12 | 0.184 | 12 |
| Selic meta | 0.426 | 4 | 0.160 | 2 |
| Selic real no mes | 0.406 | 12 | 0.170 | 12 |
| IGP-M mensal | 0.344 | 11 | 0.151 | 11 |
| Juros financ. imob. (mercado) | 0.294 | 11 | 0.220 | 9 |
| Dolar PTAX | 0.227 | 8 | 0.154 | 8 |
| Desocupacao Brasil | 0.212 | 4 | 0.165 | 5 |
| Juros financ. imob. (regulada) | 0.160 | 11 | 0.186 | 7 |
| Confianca do consumidor | 0.124 | 10 | 0.183 | 11 |
| IBC-Br | 0.098 | 12 | 0.106 | 10 |

Figura: `reports/figures/eda_correlacao_cruzada.png`

## 11. Causalidade de Granger, FipeZAP nacional (series estacionarias)

Limiar de Bonferroni: p < 0.00069 (sobre 12 preditores x 6 lags).

| preditor | n | menor p | no lag | p < 0,05 | passa Bonferroni |
|---|---|---|---|---|---|
| Selic meta | 222 | 0.1409 | 6 | False | False |
| Selic real no mes | 222 | 0.3080 | 6 | False | False |
| IPCA mensal | 222 | 0.6268 | 5 | False | False |
| IGP-M mensal | 222 | 0.6448 | 5 | False | False |
| INCC mensal | 222 | 0.3717 | 3 | False | False |
| Dolar PTAX | 222 | 0.7815 | 1 | False | False |
| IBC-Br | 221 | 0.0023 | 1 | True | False |
| Saldo cred. imob. | 222 | 0.0898 | 3 | False | False |
| Juros financ. imob. (mercado) | 185 | 0.5477 | 3 | False | False |
| Juros financ. imob. (regulada) | 185 | 0.0895 | 5 | False | False |
| Confianca do consumidor | 222 | 0.0470 | 2 | True | False |
| Desocupacao Brasil | 173 | 0.3099 | 3 | False | False |

## 11. Causalidade de Granger, FipeZAP SJC (series estacionarias)

Limiar de Bonferroni: p < 0.00069 (sobre 12 preditores x 6 lags).

| preditor | n | menor p | no lag | p < 0,05 | passa Bonferroni |
|---|---|---|---|---|---|
| Selic meta | 102 | 0.0265 | 5 | True | False |
| Selic real no mes | 102 | 0.1149 | 3 | False | False |
| IPCA mensal | 102 | 0.1673 | 3 | False | False |
| IGP-M mensal | 102 | 0.2828 | 1 | False | False |
| INCC mensal | 102 | 0.6145 | 1 | False | False |
| Dolar PTAX | 102 | 0.4441 | 1 | False | False |
| IBC-Br | 101 | 0.3185 | 1 | False | False |
| Saldo cred. imob. | 102 | 0.6977 | 4 | False | False |
| Juros financ. imob. (mercado) | 102 | 0.5549 | 2 | False | False |
| Juros financ. imob. (regulada) | 102 | 0.1555 | 3 | False | False |
| Confianca do consumidor | 102 | 0.2154 | 1 | False | False |
| Desocupacao Brasil | 101 | 0.3267 | 1 | False | False |

## 11b. Canal de baixa frequencia (variacoes de 12 meses)

Analise descritiva com janelas sobrepostas (limiar com n/12). Relacoes significativas e utilizaveis, por alvo:

**nacional (nominal)**

| preditor | lag | r | n | limiar (n/12) |
|---|---|---|---|---|
| Saldo cred. imob. (var. 12 meses) | 3 | 0.934 | 209 | 0.470 |
| Saldo cred. imob. (var. 12 meses) | 6 | 0.911 | 206 | 0.473 |
| Saldo cred. imob. (var. 12 meses) | 9 | 0.879 | 203 | 0.477 |
| Saldo cred. imob. (var. 12 meses) | 12 | 0.840 | 200 | 0.480 |
| Confianca do consumidor (nivel) | 3 | 0.823 | 212 | 0.466 |
| Confianca do consumidor (nivel) | 6 | 0.822 | 212 | 0.466 |

**nacional (real)**

| preditor | lag | r | n | limiar (n/12) |
|---|---|---|---|---|
| Confianca do consumidor (nivel) | 3 | 0.867 | 212 | 0.466 |
| Saldo cred. imob. (var. 12 meses) | 3 | 0.864 | 209 | 0.470 |
| Confianca do consumidor (nivel) | 6 | 0.851 | 212 | 0.466 |
| Saldo cred. imob. (var. 12 meses) | 6 | 0.831 | 206 | 0.473 |
| Confianca do consumidor (nivel) | 9 | 0.826 | 212 | 0.466 |
| Confianca do consumidor (nivel) | 12 | 0.792 | 212 | 0.466 |

**SJC (nominal)**

| preditor | lag | r | n | limiar (n/12) |
|---|---|---|---|---|
| INCC acumulado 12 meses | 12 | 0.870 | 92 | 0.708 |
| Saldo cred. imob. (var. 12 meses) | 12 | 0.864 | 92 | 0.708 |
| Saldo cred. imob. (var. 12 meses) | 9 | 0.855 | 92 | 0.708 |
| IPCA acumulado 12 meses | 9 | 0.828 | 92 | 0.708 |
| Saldo cred. imob. (var. 12 meses) | 6 | 0.823 | 92 | 0.708 |
| INCC acumulado 12 meses | 9 | 0.818 | 92 | 0.708 |

## 11c. Estabilidade das relacoes de baixa frequencia por subperiodo

Autocorrelacao no lag 12 das variacoes de 12 meses: preco 0.87, credito 0.94 (series muito persistentes: poucas observacoes independentes).

| preditor (contra a var. 12 meses do FipeZAP nacional) | 2009-2014 | 2015-2020 | 2021-2026 | amostra toda |
|---|---|---|---|---|
| Saldo cred. imob. (var. 12 meses, lag 3) | 0.95 | 0.85 | -0.09 | 0.93 |
| Confianca do consumidor (nivel, lag 3) | 0.56 | -0.04 | 0.10 | 0.82 |
| Selic real, media de 12 meses (lag 6) | 0.36 | -0.32 | 0.24 | 0.05 |
| INCC acumulado 12 meses (lag 6) | -0.26 | 0.42 | -0.16 | 0.19 |

## 12. Correlacao cruzada trimestral (nacional, series estacionarias)

| preditor | dif. extras | lag (trimestres) | r | n | limiar 95% |
|---|---|---|---|---|---|
| Desocupacao SP | 0 | 0 | -0.119 | 57 | 0.260 |
| Desocupacao SP | 0 | 1 | 0.143 | 56 | 0.262 |
| Desocupacao SP | 0 | 2 | -0.058 | 55 | 0.264 |
| Desocupacao SP | 0 | 3 | 0.028 | 54 | 0.267 |
| Desocupacao SP | 0 | 4 | -0.125 | 53 | 0.269 |
| Renda SP | 0 | 0 | -0.082 | 48 | 0.283 |
| Renda SP | 0 | 1 | 0.007 | 47 | 0.286 |
| Renda SP | 0 | 2 | 0.155 | 46 | 0.289 |
| Renda SP | 0 | 3 | -0.214 | 45 | 0.292 |
| Renda SP | 0 | 4 | -0.007 | 44 | 0.295 |
| Selic meta | 0 | 0 | 0.047 | 72 | 0.231 |
| Selic meta | 0 | 1 | -0.079 | 72 | 0.231 |
| Selic meta | 0 | 2 | -0.226 | 71 | 0.233 |
| Selic meta | 0 | 3 | -0.120 | 70 | 0.234 |
| Selic meta | 0 | 4 | -0.144 | 69 | 0.236 |
| IPCA (composto no trimestre) | 0 | 0 | -0.193 | 72 | 0.231 |
| IPCA (composto no trimestre) | 0 | 1 | -0.050 | 72 | 0.231 |
| IPCA (composto no trimestre) | 0 | 2 | 0.071 | 72 | 0.231 |
| IPCA (composto no trimestre) | 0 | 3 | -0.140 | 71 | 0.233 |
| IPCA (composto no trimestre) | 0 | 4 | -0.201 | 70 | 0.234 |
| IBC-Br | 0 | 0 | 0.170 | 72 | 0.231 |
| IBC-Br | 0 | 1 | 0.118 | 72 | 0.231 |
| IBC-Br | 0 | 2 | -0.179 | 71 | 0.233 |
| IBC-Br | 0 | 3 | -0.027 | 70 | 0.234 |
| IBC-Br | 0 | 4 | 0.153 | 69 | 0.236 |

## 13. Suficiencia amostral (observacoes apos estacionarizar)

| cenario | observacoes | variaveis | obs. por variavel |
|---|---|---|---|
| ARIMA univariado, nacional (nominal) | 222 | 1 | 222.000 |
| ARIMAX/LSTM, nacional (nominal), 9 preditores com historico desde 2008 | 221 | 9 | 24.600 |
| ARIMAX/LSTM, nacional (nominal), todos os 12 preditores | 173 | 12 | 14.400 |
| Modelo trimestral univariado, nacional (nominal) | 72 | 1 | 72.000 |
| ARIMA univariado, SJC (nominal) | 102 | 1 | 102.000 |
| ARIMAX/LSTM, SJC (nominal), 9 preditores com historico desde 2008 | 101 | 9 | 11.200 |
| ARIMAX/LSTM, SJC (nominal), todos os 12 preditores | 101 | 12 | 8.400 |
| Modelo trimestral univariado, SJC (nominal) | 32 | 1 | 32.000 |
| Trimestral, nacional, com desocupacao e renda de SP (IBGE) | 48 | 2 | 24.000 |

## Figuras geradas

- `reports/figures/eda_acf_pacf_alvo.png`
- `reports/figures/eda_alvo_niveis.png`
- `reports/figures/eda_crescimento_selic.png`
- `reports/figures/eda_correlacao_preditores.png`
- `reports/figures/eda_correlacao_cruzada.png`
- `reports/figures/eda_disponibilidade.png`
