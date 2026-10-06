# Projecao de preco de Jacarei (precificacao x tendencia do FipeZAP)

Gerado por `python main.py projecao`. Nao editar manualmente. Leitura em `docs/PROJECAO_JACAREI.md`.

**Metodo.** (1) Valor estimado de cada anuncio do VivaReal de Jacarei (apartamento e casa) com um conjunto de LightGBM e HistGradientBoosting ajustados (Optuna), por **previsoes fora da amostra** (5 particoes). (2) Esse valor e de **mar/2026** (coleta do VivaReal); leva-se ate Aug/2026 com a variacao **observada** do indice de Sao Jose dos Campos (+4.4%; nacional +2.4%). (3) A partir dai aplica-se a **previsao** do indice (cenario central: ARIMA de SJC) ao R$/m2 de cada anuncio.

**Premissa central:** Jacarei acompanha a tendencia do indice de SJC (o FipeZAP nao tem Jacarei) e todos os imoveis variam igual. A incerteza do valor de **cada imovel** (erro de avaliacao, abaixo) e muito maior que a da tendencia.

## Resumo por segmento (R$/m2, medianas)

| segmento | anuncios | R$/m2 pedido (mediana) | R$/m2 estimado, mar/2026 | R$/m2 estimado, hoje | R$/m2 projetado em 3 meses | R$/m2 projetado em 6 meses | R$/m2 projetado em 12 meses | intervalo 80% (+-) | intervalo 90% (+-) |
|---|---|---|---|---|---|---|---|---|---|
| apartamento | 3992 | 6174.757 | 6184.971 | 6457.880 | 6569.677 | 6706.421 | 6988.507 | 0.170 | 0.228 |
| casa | 10254 | 4375.000 | 4402.429 | 4596.684 | 4676.261 | 4773.594 | 4974.381 | 0.225 | 0.313 |

## Cenarios de tendencia (variacao do R$/m2 apos o ultimo indice publicado)

| cenario | h | variacao (%) | IC95 inf (%) | IC95 sup (%) |
|---|---|---|---|---|
| ARIMA SJC | 3 | 1.73 | -0.88 | 4.41 |
| ARIMA SJC | 6 | 3.85 | -1.78 | 9.80 |
| ARIMA SJC | 12 | 8.22 | -4.48 | 22.61 |
| Tendencia de 12 meses SJC | 3 | 2.37 |  |  |
| Tendencia de 12 meses SJC | 6 | 4.80 |  |  |
| Tendencia de 12 meses SJC | 12 | 9.83 |  |  |
| ARIMA Nacional | 3 | 1.54 | 0.51 | 2.57 |
| ARIMA Nacional | 6 | 3.06 | 0.68 | 5.50 |
| ARIMA Nacional | 12 | 6.18 | 0.31 | 12.39 |

## Incerteza do valor de cada imovel

Intervalo conformal pelo erro relativo fora da amostra: apartamento: +-17% (80%), +-23% (90%); casa: +-23% (80%), +-31% (90%).

## Arquivos

- `data/processed/vivareal/projecao_anuncios.csv`: valor estimado e projecoes por anuncio (nao versionado)
- `reports/results/eda/projecao_por_setor.csv`: pedido x estimado por setor
- `reports/results/eda/projecao_cenarios_tendencia.csv`

- `reports/figures/projecao_cenarios.png`
- `reports/figures/projecao_premio_por_setor.png`
