# Modelos avancados de precificacao: busca bayesiana, conjunto e intervalos

Gerado por `python main.py modelos-avancados`. Nao editar manualmente.

Conjunto de informacao completo: imovel, terreno e palavras do anuncio, coordenadas (imputadas), preco dos vizinhos, setor IBGE e Censo 2022. Divisao **temporal** (teste nos 25% mais recentes). Busca de parametros bayesiana (Optuna/TPE) minimizando o erro medio na validacao cruzada de 3 particoes **so no treino**; tentativas: HistGradientBoosting 40, LightGBM 40, CatBoost 8. O conjunto e a media dos tres modelos ajustados. Os intervalos sao conformais pelo erro relativo fora da amostra no treino.

Tempo total: 65.5 min.

## apartamento

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 1027.450 | 743.192 | 11.957 | 0.685 |
| HistGradientBoosting, ajustado (Optuna) | 1001.011 | 722.719 | 11.677 | 0.701 |
| LightGBM, parametros padrao | 1017.251 | 739.329 | 11.966 | 0.692 |
| LightGBM, ajustado (Optuna) | 999.479 | 713.419 | 11.467 | 0.702 |
| CatBoost, parametros padrao | 1019.487 | 744.931 | 12.186 | 0.690 |
| CatBoost, ajustado (Optuna) | 1031.604 | 762.468 | 12.471 | 0.683 |
| Conjunto (media dos 3 ajustados) | 988.575 | 710.778 | 11.499 | 0.709 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.020777760750325572, 'max_leaf_nodes': 52, 'min_samples_leaf': 6, 'l2_regularization': 0.4076798661111209, 'max_features': 0.6329703120569584} (MAE na validacao interna 758)
- LightGBM: {'learning_rate': 0.010072451352696996, 'num_leaves': 112, 'min_child_samples': 15, 'subsample': 0.8452404885159948, 'colsample_bytree': 0.6742771278043024, 'reg_lambda': 0.0026139609595683803, 'reg_alpha': 4.675795244814138, 'n_estimators': 1101, 'objective': 'regression'} (MAE na validacao interna 738)
- CatBoost: {'depth': 6, 'learning_rate': 0.15627571590838057, 'l2_leaf_reg': 1.0725209743171995, 'iterations': 441} (MAE na validacao interna 784)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.827 | 2403.338 | 0.188 |
| 0.900 | 0.911 | 3168.338 | 0.248 |

## casa

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 975.684 | 693.401 | 16.135 | 0.767 |
| HistGradientBoosting, ajustado (Optuna) | 945.550 | 662.946 | 15.438 | 0.781 |
| LightGBM, parametros padrao | 972.711 | 690.925 | 16.077 | 0.768 |
| LightGBM, ajustado (Optuna) | 927.698 | 650.277 | 15.098 | 0.789 |
| CatBoost, parametros padrao | 964.176 | 683.348 | 15.922 | 0.772 |
| CatBoost, ajustado (Optuna) | 959.896 | 688.144 | 16.073 | 0.774 |
| Conjunto (media dos 3 ajustados) | 924.611 | 649.480 | 15.088 | 0.791 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.021418136071124437, 'max_leaf_nodes': 70, 'min_samples_leaf': 12, 'l2_regularization': 0.8538769722750749, 'max_features': 0.6423857721006483} (MAE na validacao interna 678)
- LightGBM: {'learning_rate': 0.017500713474250612, 'num_leaves': 70, 'min_child_samples': 17, 'subsample': 0.8553298651410736, 'colsample_bytree': 0.7923581113148196, 'reg_lambda': 0.0019375912493993007, 'reg_alpha': 0.0026821905215968825, 'n_estimators': 1145, 'objective': 'regression'} (MAE na validacao interna 661)
- CatBoost: {'depth': 6, 'learning_rate': 0.15627571590838057, 'l2_leaf_reg': 1.0725209743171995, 'iterations': 441} (MAE na validacao interna 703)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.811 | 2207.637 | 0.238 |
| 0.900 | 0.906 | 3024.961 | 0.327 |

## residencial

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 1005.525 | 726.510 | 15.096 | 0.772 |
| HistGradientBoosting, ajustado (Optuna) | 972.798 | 699.181 | 14.746 | 0.787 |
| LightGBM, parametros padrao | 1003.512 | 728.910 | 15.520 | 0.773 |
| LightGBM, ajustado (Optuna) | 942.979 | 675.956 | 14.347 | 0.799 |
| CatBoost, parametros padrao | 1005.993 | 730.281 | 15.359 | 0.772 |
| CatBoost, ajustado (Optuna) | 982.356 | 712.879 | 14.956 | 0.782 |
| Conjunto (media dos 3 ajustados) | 947.651 | 679.526 | 14.297 | 0.797 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.021103020847069942, 'max_leaf_nodes': 77, 'min_samples_leaf': 6, 'l2_regularization': 1.2143614773581008, 'max_features': 0.5057798961506867} (MAE na validacao interna 707)
- LightGBM: {'learning_rate': 0.02122857173130132, 'num_leaves': 94, 'min_child_samples': 7, 'subsample': 0.8096193217225021, 'colsample_bytree': 0.48092437429255125, 'reg_lambda': 0.02836091724352868, 'reg_alpha': 0.035506741378642875, 'n_estimators': 896, 'objective': 'regression'} (MAE na validacao interna 693)
- CatBoost: {'depth': 6, 'learning_rate': 0.15627571590838057, 'l2_leaf_reg': 1.0725209743171995, 'iterations': 441} (MAE na validacao interna 742)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.821 | 2389.817 | 0.231 |
| 0.900 | 0.911 | 3247.976 | 0.314 |

## Figura

- `reports/figures/modelos_avancados_real_previsto.png`

