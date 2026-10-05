# LSTM e modelos globais em painel (FipeZAP)

Gerado por `python main.py lstm`. Nao editar manualmente. Leitura em `docs/MODELOS_LSTM.md`.

Experimento: as 50 cidades do Excel do FipeZAP (preco medio de venda residencial). Modelos de **crescimento mensal** (em log), padronizado pelo desvio-padrao de cada cidade **calculado so no treino**: o nivel do preco de cada cidade e eliminado. Entrada: ultimos 12 meses; saida direta de 12 meses. Alvos: SJC (proxy de Jacarei) e indice nacional.

- **Controle:** LSTM so com a serie do alvo.
- **Painel (todas):** todas as cidades juntas.
- **Mais parecidas:** so as 10 cidades com maior correlacao do crescimento de 12 meses com o alvo.
- **Ponderado:** todas, com peso = correlacao (negativas valem 0).
- **GB global:** gradient boosting em painel (comparador).
A semelhanca usa **so dados ate a origem de cada reajuste** (sem olhar o futuro). Os modelos sao reajustados a cada 12 meses (o ARIMA, todo mes) e os LSTM sao a media de 3 sementes. Walk-forward com janela expansiva, mesmos horizontes e metricas do ARIMA.

Tempo total: 6.8 min.

## SJC (nominal) (44 origens)

### Erro por horizonte

| h (meses) | modelo | n origens | MAPE (%) | RMSE | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 44 | 0.316 | 33.810 | 1.000 |
| 1 | Tendencia (12 meses) | 44 | 0.458 | 48.496 | 1.434 |
| 1 | LSTM controle (so o alvo) | 44 | 0.407 | 43.687 | 1.292 |
| 1 | LSTM painel (todas as cidades) | 44 | 0.334 | 35.123 | 1.039 |
| 1 | LSTM painel (10 mais parecidas) | 44 | 0.391 | 41.767 | 1.235 |
| 1 | LSTM painel ponderado por semelhanca | 44 | 0.363 | 38.848 | 1.149 |
| 1 | GB global (todas as cidades) | 44 | 0.335 | 33.853 | 1.001 |
| 1 | GB global (10 mais parecidas) | 44 | 0.352 | 35.402 | 1.047 |
| 3 | ARIMA(0,2,3) | 42 | 1.193 | 130.576 | 1.000 |
| 3 | Tendencia (12 meses) | 42 | 1.264 | 132.438 | 1.014 |
| 3 | LSTM controle (so o alvo) | 42 | 1.126 | 116.077 | 0.889 |
| 3 | LSTM painel (todas as cidades) | 42 | 1.128 | 125.451 | 0.961 |
| 3 | LSTM painel (10 mais parecidas) | 42 | 1.148 | 124.284 | 0.952 |
| 3 | LSTM painel ponderado por semelhanca | 42 | 1.162 | 125.659 | 0.962 |
| 3 | GB global (todas as cidades) | 42 | 1.135 | 114.679 | 0.878 |
| 3 | GB global (10 mais parecidas) | 42 | 1.186 | 118.141 | 0.905 |
| 6 | ARIMA(0,2,3) | 39 | 2.776 | 283.313 | 1.000 |
| 6 | Tendencia (12 meses) | 39 | 2.191 | 217.991 | 0.769 |
| 6 | LSTM controle (so o alvo) | 39 | 1.890 | 183.548 | 0.648 |
| 6 | LSTM painel (todas as cidades) | 39 | 2.212 | 235.210 | 0.830 |
| 6 | LSTM painel (10 mais parecidas) | 39 | 2.037 | 212.654 | 0.751 |
| 6 | LSTM painel ponderado por semelhanca | 39 | 2.262 | 231.485 | 0.817 |
| 6 | GB global (todas as cidades) | 39 | 1.947 | 204.014 | 0.720 |
| 6 | GB global (10 mais parecidas) | 39 | 2.078 | 219.448 | 0.775 |
| 12 | ARIMA(0,2,3) | 33 | 5.455 | 533.101 | 1.000 |
| 12 | Tendencia (12 meses) | 33 | 3.446 | 322.779 | 0.605 |
| 12 | LSTM controle (so o alvo) | 33 | 2.134 | 238.277 | 0.447 |
| 12 | LSTM painel (todas as cidades) | 33 | 3.267 | 307.310 | 0.576 |
| 12 | LSTM painel (10 mais parecidas) | 33 | 2.471 | 301.458 | 0.565 |
| 12 | LSTM painel ponderado por semelhanca | 33 | 3.248 | 314.550 | 0.590 |
| 12 | GB global (todas as cidades) | 33 | 2.503 | 248.066 | 0.465 |
| 12 | GB global (10 mais parecidas) | 33 | 2.863 | 287.336 | 0.539 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| Tendencia (12 meses) | ARIMA(0,2,3) | 1 | 2.000 | 0.052 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 3 | 0.048 | 0.962 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 6 | -1.375 | 0.177 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 12 | -1.214 | 0.234 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 1 | 1.421 | 0.163 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 3 | -0.700 | 0.488 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 6 | -1.729 | 0.092 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 12 | -1.665 | 0.106 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 1 | 0.402 | 0.689 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 3 | -0.442 | 0.661 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 6 | -1.838 | 0.074 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 12 | -1.624 | 0.114 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 1 | 1.346 | 0.185 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 3 | -0.482 | 0.633 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 6 | -1.753 | 0.088 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 12 | -1.723 | 0.095 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 1 | 0.989 | 0.328 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 3 | -0.527 | 0.601 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 6 | -1.946 | 0.059 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 12 | -1.687 | 0.101 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 1 | 0.017 | 0.987 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 3 | -0.749 | 0.458 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 6 | -1.862 | 0.070 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 12 | -1.628 | 0.113 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 1 | 0.197 | 0.845 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 3 | -0.521 | 0.605 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 6 | -1.248 | 0.220 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 12 | -1.456 | 0.155 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 1 | -1.779 | 0.082 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 3 | 0.579 | 0.566 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 6 | 1.127 | 0.267 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 12 | 0.813 | 0.422 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 1 | -0.749 | 0.458 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 3 | 0.724 | 0.473 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 6 | 1.248 | 0.220 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 12 | 0.949 | 0.350 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 1 | -1.389 | 0.172 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 3 | 0.612 | 0.544 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 6 | 1.412 | 0.166 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 12 | 1.287 | 0.207 |

### Cidades escolhidas como mais parecidas em cada reajuste (cidade: correlacao)

- 2022-12: Vila Velha (0.967), Santo André (0.955), Praia Grande (0.955), São Caetano do Sul (0.951), Blumenau (0.949), Balneário Camboriú (0.94) ...
- 2023-12: Praia Grande (0.949), Balneário Camboriú (0.946), Santo André (0.942), Blumenau (0.941), Goiânia (0.93), São Caetano do Sul (0.927) ...
- 2024-12: Santo André (0.941), Praia Grande (0.935), Blumenau (0.934), Goiânia (0.925), Vila Velha (0.913), São Caetano do Sul (0.904) ...
- 2025-12: Praia Grande (0.921), Vila Velha (0.909), Blumenau (0.906), Goiânia (0.903), Santo André (0.902), São José (0.865) ...

## nacional (nominal) (140 origens)

### Erro por horizonte

| h (meses) | modelo | n origens | MAPE (%) | RMSE | RMSE relativo ao ARIMA |
|---|---|---|---|---|---|
| 1 | ARIMA(0,2,3) | 140 | 0.071 | 7.136 | 1.000 |
| 1 | Tendencia (12 meses) | 140 | 0.111 | 10.909 | 1.529 |
| 1 | LSTM controle (so o alvo) | 140 | 0.184 | 18.375 | 2.575 |
| 1 | LSTM painel (todas as cidades) | 140 | 0.127 | 11.913 | 1.669 |
| 1 | LSTM painel (10 mais parecidas) | 140 | 0.151 | 14.460 | 2.026 |
| 1 | LSTM painel ponderado por semelhanca | 140 | 0.126 | 11.753 | 1.647 |
| 1 | GB global (todas as cidades) | 140 | 0.095 | 9.126 | 1.279 |
| 1 | GB global (10 mais parecidas) | 140 | 0.098 | 9.826 | 1.377 |
| 3 | ARIMA(0,2,3) | 138 | 0.238 | 24.409 | 1.000 |
| 3 | Tendencia (12 meses) | 138 | 0.323 | 32.596 | 1.335 |
| 3 | LSTM controle (so o alvo) | 138 | 0.560 | 56.548 | 2.317 |
| 3 | LSTM painel (todas as cidades) | 138 | 0.391 | 36.718 | 1.504 |
| 3 | LSTM painel (10 mais parecidas) | 138 | 0.443 | 43.279 | 1.773 |
| 3 | LSTM painel ponderado por semelhanca | 138 | 0.382 | 36.120 | 1.480 |
| 3 | GB global (todas as cidades) | 138 | 0.358 | 33.590 | 1.376 |
| 3 | GB global (10 mais parecidas) | 138 | 0.349 | 34.669 | 1.420 |
| 6 | ARIMA(0,2,3) | 135 | 0.532 | 52.616 | 1.000 |
| 6 | Tendencia (12 meses) | 135 | 0.674 | 67.426 | 1.281 |
| 6 | LSTM controle (so o alvo) | 135 | 1.163 | 114.256 | 2.171 |
| 6 | LSTM painel (todas as cidades) | 135 | 0.812 | 75.634 | 1.437 |
| 6 | LSTM painel (10 mais parecidas) | 135 | 0.913 | 86.988 | 1.653 |
| 6 | LSTM painel ponderado por semelhanca | 135 | 0.784 | 73.842 | 1.403 |
| 6 | GB global (todas as cidades) | 135 | 0.752 | 73.953 | 1.406 |
| 6 | GB global (10 mais parecidas) | 135 | 0.796 | 79.154 | 1.504 |
| 12 | ARIMA(0,2,3) | 129 | 1.182 | 117.690 | 1.000 |
| 12 | Tendencia (12 meses) | 129 | 1.465 | 148.575 | 1.262 |
| 12 | LSTM controle (so o alvo) | 129 | 2.275 | 232.128 | 1.972 |
| 12 | LSTM painel (todas as cidades) | 129 | 1.758 | 161.440 | 1.372 |
| 12 | LSTM painel (10 mais parecidas) | 129 | 1.865 | 176.597 | 1.501 |
| 12 | LSTM painel ponderado por semelhanca | 129 | 1.706 | 157.638 | 1.339 |
| 12 | GB global (todas as cidades) | 129 | 1.689 | 175.303 | 1.490 |
| 12 | GB global (10 mais parecidas) | 129 | 1.755 | 185.460 | 1.576 |

### Diebold-Mariano (estatistica negativa: o primeiro modelo e melhor que o segundo)

| modelo | contra | h (meses) | estatistica DM | p (bilateral) |
|---|---|---|---|---|
| Tendencia (12 meses) | ARIMA(0,2,3) | 1 | 4.864 | 0.000 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 3 | 2.793 | 0.006 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 6 | 1.843 | 0.068 |
| Tendencia (12 meses) | ARIMA(0,2,3) | 12 | 1.428 | 0.156 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 1 | 5.637 | 0.000 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 3 | 3.362 | 0.001 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 6 | 2.383 | 0.019 |
| LSTM controle (so o alvo) | ARIMA(0,2,3) | 12 | 1.879 | 0.063 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 1 | 4.852 | 0.000 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 3 | 2.750 | 0.007 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 6 | 1.974 | 0.050 |
| LSTM painel (todas as cidades) | ARIMA(0,2,3) | 12 | 1.931 | 0.056 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 1 | 5.805 | 0.000 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 3 | 3.288 | 0.001 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 6 | 2.320 | 0.022 |
| LSTM painel (10 mais parecidas) | ARIMA(0,2,3) | 12 | 1.957 | 0.053 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 1 | 4.859 | 0.000 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 3 | 2.726 | 0.007 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 6 | 1.906 | 0.059 |
| LSTM painel ponderado por semelhanca | ARIMA(0,2,3) | 12 | 1.828 | 0.070 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 1 | 2.893 | 0.004 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 3 | 3.346 | 0.001 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 6 | 1.933 | 0.055 |
| GB global (todas as cidades) | ARIMA(0,2,3) | 12 | 1.486 | 0.140 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 1 | 4.168 | 0.000 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 3 | 2.825 | 0.005 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 6 | 1.936 | 0.055 |
| GB global (10 mais parecidas) | ARIMA(0,2,3) | 12 | 1.222 | 0.224 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 1 | -5.584 | 0.000 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 3 | -3.497 | 0.001 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 6 | -2.497 | 0.014 |
| LSTM painel (todas as cidades) | LSTM controle (so o alvo) | 12 | -1.811 | 0.073 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 1 | -4.715 | 0.000 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 3 | -3.077 | 0.003 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 6 | -2.246 | 0.026 |
| LSTM painel (10 mais parecidas) | LSTM controle (so o alvo) | 12 | -1.755 | 0.082 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 1 | -5.560 | 0.000 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 3 | -3.491 | 0.001 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 6 | -2.522 | 0.013 |
| LSTM painel ponderado por semelhanca | LSTM controle (so o alvo) | 12 | -1.853 | 0.066 |

### Cidades escolhidas como mais parecidas em cada reajuste (cidade: correlacao)

- 2014-12: Brasília (0.971), São Paulo (0.967), Rio de Janeiro (0.956), Recife (0.871), Belo Horizonte (0.87), Santo André (0.826) ...
- 2015-12: São Paulo (0.98), Rio de Janeiro (0.972), Campinas (0.967), Guarujá (0.963), Guarulhos (0.961), São Caetano do Sul (0.954) ...
- 2016-12: São Paulo (0.986), Rio de Janeiro (0.982), Campinas (0.977), Guarujá (0.974), São Caetano do Sul (0.96), Osasco (0.952) ...
- 2017-12: São Paulo (0.988), Rio de Janeiro (0.985), Campinas (0.969), Guarujá (0.965), São Caetano do Sul (0.959), Niterói (0.958) ...
- 2018-12: São Paulo (0.99), Rio de Janeiro (0.988), Campinas (0.974), Niterói (0.963), São Bernardo do Campo (0.962), Osasco (0.962) ...
- 2019-12: São Paulo (0.991), Rio de Janeiro (0.989), Campinas (0.972), Niterói (0.965), São Bernardo do Campo (0.965), Recife (0.96) ...
- 2020-12: São Paulo (0.991), Rio de Janeiro (0.989), Campinas (0.965), São Bernardo do Campo (0.965), Niterói (0.963), Recife (0.956) ...
- 2021-12: São Paulo (0.99), Rio de Janeiro (0.989), São José dos Pinhais (0.967), São Bernardo do Campo (0.959), João Pessoa (0.955), Recife (0.954) ...
- 2022-12: Rio de Janeiro (0.988), São Paulo (0.987), São José dos Pinhais (0.979), João Pessoa (0.971), São Bernardo do Campo (0.96), São José (0.954) ...
- 2023-12: Rio de Janeiro (0.987), São Paulo (0.986), João Pessoa (0.971), São Bernardo do Campo (0.955), São José (0.949), São José dos Pinhais (0.948) ...
- 2024-12: Rio de Janeiro (0.985), São Paulo (0.985), João Pessoa (0.97), São Bernardo do Campo (0.948), Recife (0.943), São José dos Pinhais (0.941) ...
- 2025-12: Rio de Janeiro (0.984), São Paulo (0.983), João Pessoa (0.972), São Bernardo do Campo (0.946), São José dos Pinhais (0.945), Recife (0.937) ...

## Figura

- `reports/figures/lstm_comparacao.png`

