# Ajuste de parametros do gradient boosting e importancia das variaveis

Gerado por `python main.py ajuste-gb`. Nao editar manualmente.

Conjunto de informacao fixado a priori: variaveis do imovel, coordenadas (imputadas), preco dos vizinhos, setor IBGE e Censo 2022 (renda, densidade, domicilios). Busca aleatoria (20 combinacoes, validacao cruzada de 3 particoes) **apenas dentro do treino** de cada divisao, otimizando o erro medio; o teste so e usado para a avaliacao final. O numero de arvores e escolhido por parada antecipada.

O Random Forest e o do baseline original do projeto, agora com as mesmas variaveis e divisoes (o R2 de 0,78 dos artefatos antigos nao e comparavel).

Tempo total: 6.5 min.

## apartamento

| validacao | modelo | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|
| holdout aleatorio (20%) | Gradient boosting, parametros padrao | 3193 | 799 | 1016.852 | 750.851 | 12.594 | 0.683 |
| holdout aleatorio (20%) | Gradient boosting, parametros ajustados | 3193 | 799 | 996.152 | 739.774 | 12.420 | 0.695 |
| temporal (teste apos 2026-03-01) | Gradient boosting, parametros padrao | 2994 | 998 | 1018.372 | 735.359 | 11.851 | 0.691 |
| temporal (teste apos 2026-03-01) | Gradient boosting, parametros ajustados | 2994 | 998 | 1032.808 | 738.324 | 11.840 | 0.682 |
| holdout aleatorio (20%) | Random Forest (baseline original, mesmas variaveis) | 3193 | 799 | 1046.920 | 776.820 | 13.186 | 0.664 |
| temporal (teste apos 2026-03-01) | Random Forest (baseline original, mesmas variaveis) | 2994 | 998 | 1073.223 | 774.401 | 12.666 | 0.657 |

Melhores parametros (por divisao):

- holdout aleatorio (20%): {'l2_regularization': 0.0, 'learning_rate': 0.0228, 'max_features': 0.5, 'max_leaf_nodes': 63, 'min_samples_leaf': 20, 'MAE interno (CV, treino)': np.float64(756.2), 'segundos': 31}
- temporal (teste apos 2026-03-01): {'l2_regularization': 5.0, 'learning_rate': 0.0571, 'max_features': 0.75, 'max_leaf_nodes': 63, 'min_samples_leaf': 10, 'MAE interno (CV, treino)': np.float64(768.9), 'segundos': 31}

Importancia das variaveis (permutacao no teste temporal; as 12 maiores):

| variavel | aumento do MAE ao embaralhar (R$/m2) | desvio |
|---|---|---|
| area (log) | 292.91 | 6.86 |
| latitude real (vizinhos) | 152.73 | 7.23 |
| longitude real (vizinhos) | 140.44 | 13.51 |
| suites | 136.07 | 2.71 |
| latitude | 115.99 | 5.47 |
| bairro | 100.38 | 7.00 |
| longitude | 89.84 | 5.85 |
| setor IBGE | 60.80 | 4.97 |
| vagas | 29.19 | 5.18 |
| renda media do setor | 29.17 | 4.08 |
| banheiros | 15.43 | 2.69 |
| comodidades | 11.32 | 3.24 |

## casa

| validacao | modelo | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|
| holdout aleatorio (20%) | Gradient boosting, parametros padrao | 8203 | 2051 | 1016.043 | 748.214 | 18.640 | 0.726 |
| holdout aleatorio (20%) | Gradient boosting, parametros ajustados | 8203 | 2051 | 1000.622 | 732.640 | 18.372 | 0.734 |
| temporal (teste apos 2026-02-26) | Gradient boosting, parametros padrao | 7690 | 2564 | 1051.327 | 754.082 | 17.337 | 0.729 |
| temporal (teste apos 2026-02-26) | Gradient boosting, parametros ajustados | 7690 | 2564 | 1025.498 | 728.375 | 16.863 | 0.743 |
| holdout aleatorio (20%) | Random Forest (baseline original, mesmas variaveis) | 8203 | 2051 | 1029.104 | 750.587 | 19.432 | 0.719 |
| temporal (teste apos 2026-02-26) | Random Forest (baseline original, mesmas variaveis) | 7690 | 2564 | 1070.078 | 768.466 | 18.381 | 0.720 |

Melhores parametros (por divisao):

- holdout aleatorio (20%): {'l2_regularization': 0.0, 'learning_rate': 0.0228, 'max_features': 0.5, 'max_leaf_nodes': 63, 'min_samples_leaf': 20, 'MAE interno (CV, treino)': np.float64(745.0), 'segundos': 53}
- temporal (teste apos 2026-02-26): {'l2_regularization': 0.0, 'learning_rate': 0.0228, 'max_features': 0.5, 'max_leaf_nodes': 63, 'min_samples_leaf': 20, 'MAE interno (CV, treino)': np.float64(743.6), 'segundos': 52}

Importancia das variaveis (permutacao no teste temporal; as 12 maiores):

| variavel | aumento do MAE ao embaralhar (R$/m2) | desvio |
|---|---|---|
| area (log) | 767.88 | 23.03 |
| bairro | 288.75 | 9.08 |
| casa em condominio | 145.37 | 6.84 |
| setor IBGE | 85.48 | 4.93 |
| suites | 81.04 | 1.01 |
| quartos | 71.08 | 4.02 |
| vagas | 48.88 | 2.21 |
| latitude real (vizinhos) | 26.18 | 1.86 |
| banheiros | 25.04 | 1.62 |
| longitude real (vizinhos) | 24.45 | 0.51 |
| latitude | 24.26 | 2.33 |
| longitude | 23.61 | 1.91 |

## residencial

| validacao | modelo | n treino | n teste | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|---|---|---|
| holdout aleatorio (20%) | Gradient boosting, parametros padrao | 11396 | 2850 | 1026.131 | 761.311 | 16.671 | 0.747 |
| holdout aleatorio (20%) | Gradient boosting, parametros ajustados | 11396 | 2850 | 994.416 | 724.294 | 15.772 | 0.763 |
| temporal (teste apos 2026-02-27) | Gradient boosting, parametros padrao | 10684 | 3562 | 1071.117 | 780.985 | 16.437 | 0.741 |
| temporal (teste apos 2026-02-27) | Gradient boosting, parametros ajustados | 10684 | 3562 | 1033.650 | 740.764 | 15.481 | 0.759 |
| holdout aleatorio (20%) | Random Forest (baseline original, mesmas variaveis) | 11396 | 2850 | 1033.908 | 752.255 | 16.724 | 0.744 |
| temporal (teste apos 2026-02-27) | Random Forest (baseline original, mesmas variaveis) | 10684 | 3562 | 1082.479 | 785.392 | 17.027 | 0.736 |

Melhores parametros (por divisao):

- holdout aleatorio (20%): {'l2_regularization': 0.0, 'learning_rate': 0.0228, 'max_features': 0.5, 'max_leaf_nodes': 63, 'min_samples_leaf': 20, 'MAE interno (CV, treino)': np.float64(752.1), 'segundos': 102}
- temporal (teste apos 2026-02-27): {'l2_regularization': 0.0, 'learning_rate': 0.0228, 'max_features': 0.5, 'max_leaf_nodes': 63, 'min_samples_leaf': 20, 'MAE interno (CV, treino)': np.float64(753.7), 'segundos': 87}

Importancia das variaveis (permutacao no teste temporal; as 12 maiores):

| variavel | aumento do MAE ao embaralhar (R$/m2) | desvio |
|---|---|---|
| area (log) | 838.23 | 12.25 |
| bairro | 261.06 | 8.51 |
| tipo do imovel | 200.81 | 4.69 |
| setor IBGE | 130.02 | 5.28 |
| suites | 81.87 | 5.34 |
| vagas | 59.50 | 3.90 |
| quartos | 44.41 | 3.38 |
| latitude real (vizinhos) | 42.38 | 4.51 |
| longitude real (vizinhos) | 38.57 | 1.84 |
| latitude | 27.83 | 0.98 |
| banheiros | 24.30 | 2.77 |
| longitude | 23.21 | 2.22 |

## Figura

- `reports/figures/importancia_variaveis.png`

