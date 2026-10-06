# Modelos avancados de precificacao: busca bayesiana, conjunto e intervalos

Gerado por `python main.py modelos-avancados`. Nao editar manualmente.

Conjunto de informacao completo: imovel, terreno e palavras do anuncio, coordenadas (imputadas), preco dos vizinhos, setor IBGE e Censo 2022. Divisao **temporal** (teste nos 25% mais recentes). Busca de parametros bayesiana (Optuna/TPE) minimizando o erro medio na validacao cruzada de 3 particoes **so no treino**; tentativas: HistGradientBoosting 40, LightGBM 40, CatBoost 8. O conjunto e a media dos tres modelos ajustados. Os intervalos sao conformais pelo erro relativo fora da amostra no treino.

Tempo total: 70.2 min.

## apartamento

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 984.880 | 708.874 | 11.502 | 0.711 |
| HistGradientBoosting, ajustado (Optuna) | 962.002 | 690.637 | 11.207 | 0.724 |
| LightGBM, parametros padrao | 989.961 | 718.632 | 11.714 | 0.708 |
| LightGBM, ajustado (Optuna) | 960.165 | 686.757 | 11.091 | 0.725 |
| CatBoost, parametros padrao | 989.000 | 722.963 | 11.771 | 0.709 |
| CatBoost, ajustado (Optuna) | 987.779 | 730.488 | 11.810 | 0.709 |
| Conjunto (media dos 3 ajustados) | 950.989 | 684.227 | 11.053 | 0.730 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.0264891626801987, 'max_leaf_nodes': 52, 'min_samples_leaf': 7, 'l2_regularization': 11.779794101330705, 'max_features': 0.48114598712001183} (MAE na validacao interna 738)
- LightGBM: {'learning_rate': 0.02798822409768565, 'num_leaves': 99, 'min_child_samples': 21, 'subsample': 0.8827596870565048, 'colsample_bytree': 0.4280696320370853, 'reg_lambda': 0.002281550832662955, 'reg_alpha': 0.005129643551239731, 'n_estimators': 655, 'objective': 'regression'} (MAE na validacao interna 713)
- CatBoost: {'depth': 5, 'learning_rate': 0.1769230629762758, 'l2_leaf_reg': 1.9721610970573997, 'iterations': 304} (MAE na validacao interna 750)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.823 | 2290.099 | 0.180 |
| 0.900 | 0.911 | 3084.034 | 0.242 |

## casa

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 946.163 | 676.292 | 15.884 | 0.781 |
| HistGradientBoosting, ajustado (Optuna) | 921.291 | 651.401 | 15.303 | 0.792 |
| LightGBM, parametros padrao | 937.384 | 671.902 | 15.829 | 0.785 |
| LightGBM, ajustado (Optuna) | 897.199 | 631.387 | 14.860 | 0.803 |
| CatBoost, parametros padrao | 949.674 | 676.491 | 15.895 | 0.779 |
| CatBoost, ajustado (Optuna) | 951.160 | 678.870 | 15.999 | 0.779 |
| Conjunto (media dos 3 ajustados) | 904.811 | 637.873 | 15.005 | 0.800 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.02526478746922359, 'max_leaf_nodes': 85, 'min_samples_leaf': 11, 'l2_regularization': 0.14783152649378856, 'max_features': 0.44803581182389945} (MAE na validacao interna 660)
- LightGBM: {'learning_rate': 0.015563299833733236, 'num_leaves': 107, 'min_child_samples': 11, 'subsample': 0.8999572812486466, 'colsample_bytree': 0.626423633316612, 'reg_lambda': 0.0018893216468666132, 'reg_alpha': 0.0013987587776078411, 'n_estimators': 1163, 'objective': 'regression'} (MAE na validacao interna 644)
- CatBoost: {'depth': 6, 'learning_rate': 0.15627571590838057, 'l2_leaf_reg': 1.0725209743171995, 'iterations': 441} (MAE na validacao interna 686)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.819 | 2195.521 | 0.236 |
| 0.900 | 0.906 | 3002.797 | 0.323 |

## residencial

| modelo | RMSE | MAE | MAPE (%) | R2 |
|---|---|---|---|---|
| HistGradientBoosting, parametros padrao | 968.043 | 701.652 | 14.821 | 0.789 |
| HistGradientBoosting, ajustado (Optuna) | 941.965 | 675.688 | 14.307 | 0.800 |
| LightGBM, parametros padrao | 979.666 | 715.576 | 15.468 | 0.784 |
| LightGBM, ajustado (Optuna) | 919.301 | 659.704 | 14.018 | 0.809 |
| CatBoost, parametros padrao | 982.463 | 714.581 | 15.192 | 0.782 |
| CatBoost, ajustado (Optuna) | 969.769 | 703.918 | 14.824 | 0.788 |
| Conjunto (media dos 3 ajustados) | 925.641 | 664.786 | 14.041 | 0.807 |

Melhores parametros encontrados:

- HistGradientBoosting: {'learning_rate': 0.029072875755800923, 'max_leaf_nodes': 96, 'min_samples_leaf': 9, 'l2_regularization': 1.727311644148852, 'max_features': 0.35904948602092734} (MAE na validacao interna 689)
- LightGBM: {'learning_rate': 0.012152776973750262, 'num_leaves': 122, 'min_child_samples': 16, 'subsample': 0.8647294835448722, 'colsample_bytree': 0.7146538304742496, 'reg_lambda': 0.008957145718728719, 'reg_alpha': 0.0013332875680414006, 'n_estimators': 1181, 'objective': 'regression'} (MAE na validacao interna 672)
- CatBoost: {'depth': 6, 'learning_rate': 0.15627571590838057, 'l2_leaf_reg': 1.0725209743171995, 'iterations': 441} (MAE na validacao interna 719)

Intervalos de previsao (R$/m2):

| nivel nominal | cobertura no teste temporal | largura media (R$/m2) | erro relativo no quantil |
|---|---|---|---|
| 0.800 | 0.814 | 2299.989 | 0.223 |
| 0.900 | 0.908 | 3184.042 | 0.308 |

## Figura

- `reports/figures/modelos_avancados_real_previsto.png`

