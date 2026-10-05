# Modelos com latitude, longitude e setores do IBGE (VivaReal)

Gerado por `python main.py reg-geo`. Nao editar manualmente.

Mesmas variaveis do modelo linear (`docs/MODELOS_PRECIFICACAO.md`, variante `+ condominio informado`) mais informacao geografica. **So ~48% dos anuncios tem coordenadas reais.** Para os demais as coordenadas sao **imputadas** usando so coordenadas (sem usar o preco): mediana da rua dentro do bairro (>= 2 anuncios com coordenada real) e, na falta, a mediana do bairro (>= 3). O indicador `coord_origem` (0 real, 1 rua, 2 bairro) entra nos modelos.

- **Vizinhos (kNN):** mediana do R$/m2 dos 15 anuncios **reais** mais proximos e distancia media, sem vazamento (cada anuncio fica fora do proprio calculo; no teste so o treino conta).
- **Setor IBGE:** setor censitario 2022 (544 em Jacarei) de cada anuncio, por juncao espacial, como categoria (setores com menos de 15 anuncios viram uma so).
- **Gradient boosting:** arvores usam as coordenadas e categorias nativamente.

Validacoes: holdout aleatorio de 20%, 5-fold e divisao temporal (teste nos 25% mais recentes). Cada modelo e avaliado em **todos os anuncios**, **so nos com coordenadas reais** e **so nos sem coordenadas reais** (onde a imputacao importa).

## apartamento (3992 anuncios; 1907 com coordenadas reais)

### R2 e MAE, todos os anuncios (n teste temporal = 998)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.439 | 0.476 | 0.488 | 1012.374 |
| OLS + vizinhos (kNN, so coord. reais) | 0.540 | 0.560 | 0.580 | 884.884 |
| OLS + vizinhos (coord. imputadas) | 0.520 | 0.553 | 0.573 | 897.150 |
| Gradient boosting sem coordenadas | 0.627 | 0.653 | 0.620 | 829.901 |
| Gradient boosting com lat/lon reais | 0.661 | 0.679 | 0.673 | 766.517 |
| Gradient boosting com lat/lon imputadas | 0.670 | 0.692 | 0.680 | 759.672 |
| Gradient boosting + setor IBGE | 0.678 | 0.693 | 0.681 | 753.243 |
| Gradient boosting imputadas + vizinhos | 0.683 | 0.690 | 0.686 | 745.819 |
| Gradient boosting imputadas + vizinhos + setor | 0.684 | 0.693 | 0.695 | 734.632 |
| OLS + vizinhos + Censo | 0.519 | 0.555 | 0.575 | 894.520 |
| Gradient boosting + Censo | 0.668 | 0.696 | 0.685 | 750.415 |
| Gradient boosting imputadas + vizinhos + Censo | 0.678 | 0.692 | 0.686 | 747.975 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.683 | 0.695 | 0.691 | 735.359 |
| GB completo + terreno e texto (sem vizinhos) | 0.696 | 0.698 | 0.679 | 762.848 |
| GB completo + terreno e texto | 0.693 | 0.701 | 0.693 | 738.638 |

### R2 e MAE, so com coordenadas reais (n teste temporal = 632)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.488 | 0.502 | 0.485 | 1056.532 |
| OLS + vizinhos (kNN, so coord. reais) | 0.669 | 0.660 | 0.615 | 868.061 |
| OLS + vizinhos (coord. imputadas) | 0.657 | 0.647 | 0.597 | 890.785 |
| Gradient boosting sem coordenadas | 0.661 | 0.663 | 0.615 | 858.253 |
| Gradient boosting com lat/lon reais | 0.718 | 0.726 | 0.696 | 749.609 |
| Gradient boosting com lat/lon imputadas | 0.724 | 0.728 | 0.691 | 761.834 |
| Gradient boosting + setor IBGE | 0.728 | 0.731 | 0.693 | 748.493 |
| Gradient boosting imputadas + vizinhos | 0.750 | 0.739 | 0.697 | 741.230 |
| Gradient boosting imputadas + vizinhos + setor | 0.747 | 0.735 | 0.706 | 730.819 |
| OLS + vizinhos + Censo | 0.653 | 0.648 | 0.596 | 892.056 |
| Gradient boosting + Censo | 0.718 | 0.741 | 0.696 | 748.264 |
| Gradient boosting imputadas + vizinhos + Censo | 0.742 | 0.739 | 0.694 | 747.361 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.747 | 0.738 | 0.699 | 734.273 |
| GB completo + terreno e texto (sem vizinhos) | 0.763 | 0.738 | 0.682 | 780.640 |
| GB completo + terreno e texto | 0.772 | 0.750 | 0.702 | 741.358 |

### R2 e MAE, so sem coordenadas reais (n teste temporal = 366)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.381 | 0.449 | 0.493 | 936.123 |
| OLS + vizinhos (kNN, so coord. reais) | 0.390 | 0.458 | 0.505 | 913.933 |
| OLS + vizinhos (coord. imputadas) | 0.361 | 0.458 | 0.521 | 908.141 |
| Gradient boosting sem coordenadas | 0.588 | 0.642 | 0.630 | 780.943 |
| Gradient boosting com lat/lon reais | 0.595 | 0.632 | 0.623 | 795.713 |
| Gradient boosting com lat/lon imputadas | 0.607 | 0.655 | 0.657 | 755.939 |
| Gradient boosting + setor IBGE | 0.620 | 0.654 | 0.656 | 761.446 |
| Gradient boosting imputadas + vizinhos | 0.605 | 0.641 | 0.662 | 753.742 |
| Gradient boosting imputadas + vizinhos + setor | 0.610 | 0.651 | 0.671 | 741.217 |
| OLS + vizinhos + Censo | 0.361 | 0.460 | 0.530 | 898.775 |
| Gradient boosting + Censo | 0.609 | 0.651 | 0.662 | 754.129 |
| Gradient boosting imputadas + vizinhos + Censo | 0.603 | 0.644 | 0.669 | 749.037 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.608 | 0.652 | 0.672 | 737.232 |
| GB completo + terreno e texto (sem vizinhos) | 0.618 | 0.658 | 0.673 | 732.124 |
| GB completo + terreno e texto | 0.600 | 0.651 | 0.673 | 733.939 |

## casa (10254 anuncios; 4973 com coordenadas reais)

### R2 e MAE, todos os anuncios (n teste temporal = 2564)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.611 | 0.597 | 0.583 | 971.686 |
| OLS + vizinhos (kNN, so coord. reais) | 0.632 | 0.622 | 0.611 | 933.026 |
| OLS + vizinhos (coord. imputadas) | 0.628 | 0.619 | 0.608 | 937.954 |
| Gradient boosting sem coordenadas | 0.724 | 0.729 | 0.721 | 768.334 |
| Gradient boosting com lat/lon reais | 0.732 | 0.733 | 0.726 | 762.349 |
| Gradient boosting com lat/lon imputadas | 0.729 | 0.735 | 0.729 | 759.930 |
| Gradient boosting + setor IBGE | 0.727 | 0.734 | 0.731 | 754.326 |
| Gradient boosting imputadas + vizinhos | 0.724 | 0.736 | 0.729 | 757.762 |
| Gradient boosting imputadas + vizinhos + setor | 0.725 | 0.737 | 0.727 | 758.761 |
| OLS + vizinhos + Censo | 0.634 | 0.625 | 0.617 | 927.139 |
| Gradient boosting + Censo | 0.731 | 0.737 | 0.735 | 748.481 |
| Gradient boosting imputadas + vizinhos + Censo | 0.727 | 0.738 | 0.733 | 747.682 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.726 | 0.735 | 0.729 | 754.082 |
| GB completo + terreno e texto (sem vizinhos) | 0.772 | 0.774 | 0.773 | 690.314 |
| GB completo + terreno e texto | 0.771 | 0.774 | 0.773 | 687.457 |

### R2 e MAE, so com coordenadas reais (n teste temporal = 1675)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.604 | 0.604 | 0.569 | 963.720 |
| OLS + vizinhos (kNN, so coord. reais) | 0.643 | 0.643 | 0.606 | 913.874 |
| OLS + vizinhos (coord. imputadas) | 0.638 | 0.638 | 0.599 | 925.718 |
| Gradient boosting sem coordenadas | 0.721 | 0.735 | 0.706 | 781.394 |
| Gradient boosting com lat/lon reais | 0.734 | 0.746 | 0.717 | 769.310 |
| Gradient boosting com lat/lon imputadas | 0.730 | 0.744 | 0.717 | 770.865 |
| Gradient boosting + setor IBGE | 0.731 | 0.749 | 0.720 | 763.057 |
| Gradient boosting imputadas + vizinhos | 0.727 | 0.748 | 0.718 | 764.374 |
| Gradient boosting imputadas + vizinhos + setor | 0.728 | 0.751 | 0.715 | 765.081 |
| OLS + vizinhos + Censo | 0.648 | 0.648 | 0.613 | 912.746 |
| Gradient boosting + Censo | 0.734 | 0.751 | 0.727 | 751.944 |
| Gradient boosting imputadas + vizinhos + Censo | 0.729 | 0.752 | 0.724 | 749.219 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.730 | 0.751 | 0.719 | 757.838 |
| GB completo + terreno e texto (sem vizinhos) | 0.777 | 0.787 | 0.770 | 689.303 |
| GB completo + terreno e texto | 0.776 | 0.787 | 0.770 | 682.635 |

### R2 e MAE, so sem coordenadas reais (n teste temporal = 889)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.617 | 0.590 | 0.595 | 986.693 |
| OLS + vizinhos (kNN, so coord. reais) | 0.623 | 0.602 | 0.607 | 969.112 |
| OLS + vizinhos (coord. imputadas) | 0.618 | 0.600 | 0.613 | 961.009 |
| Gradient boosting sem coordenadas | 0.727 | 0.724 | 0.739 | 743.727 |
| Gradient boosting com lat/lon reais | 0.729 | 0.721 | 0.734 | 749.233 |
| Gradient boosting com lat/lon imputadas | 0.727 | 0.726 | 0.744 | 739.328 |
| Gradient boosting + setor IBGE | 0.723 | 0.721 | 0.742 | 737.876 |
| Gradient boosting imputadas + vizinhos | 0.721 | 0.725 | 0.740 | 745.303 |
| Gradient boosting imputadas + vizinhos + setor | 0.722 | 0.723 | 0.739 | 746.855 |
| OLS + vizinhos + Censo | 0.622 | 0.604 | 0.614 | 954.260 |
| Gradient boosting + Censo | 0.728 | 0.724 | 0.743 | 741.958 |
| Gradient boosting imputadas + vizinhos + Censo | 0.725 | 0.726 | 0.741 | 744.786 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.722 | 0.721 | 0.739 | 747.006 |
| GB completo + terreno e texto (sem vizinhos) | 0.767 | 0.761 | 0.772 | 692.220 |
| GB completo + terreno e texto | 0.766 | 0.761 | 0.771 | 696.543 |

## residencial (14246 anuncios; 6880 com coordenadas reais)

### R2 e MAE, todos os anuncios (n teste temporal = 3562)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.621 | 0.614 | 0.596 | 1011.038 |
| OLS + vizinhos (kNN, so coord. reais) | 0.642 | 0.641 | 0.632 | 960.690 |
| OLS + vizinhos (coord. imputadas) | 0.636 | 0.635 | 0.626 | 967.909 |
| Gradient boosting sem coordenadas | 0.736 | 0.739 | 0.726 | 807.712 |
| Gradient boosting com lat/lon reais | 0.740 | 0.742 | 0.733 | 799.613 |
| Gradient boosting com lat/lon imputadas | 0.741 | 0.744 | 0.735 | 799.318 |
| Gradient boosting + setor IBGE | 0.746 | 0.747 | 0.739 | 787.881 |
| Gradient boosting imputadas + vizinhos | 0.743 | 0.748 | 0.737 | 792.018 |
| Gradient boosting imputadas + vizinhos + setor | 0.746 | 0.750 | 0.740 | 782.558 |
| OLS + vizinhos + Censo | 0.642 | 0.641 | 0.634 | 957.467 |
| Gradient boosting + Censo | 0.745 | 0.748 | 0.741 | 787.340 |
| Gradient boosting imputadas + vizinhos + Censo | 0.747 | 0.749 | 0.741 | 783.961 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.747 | 0.750 | 0.741 | 780.985 |
| GB completo + terreno e texto (sem vizinhos) | 0.772 | 0.774 | 0.768 | 738.916 |
| GB completo + terreno e texto | 0.771 | 0.775 | 0.767 | 739.999 |

### R2 e MAE, so com coordenadas reais (n teste temporal = 2374)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.639 | 0.624 | 0.592 | 1023.248 |
| OLS + vizinhos (kNN, so coord. reais) | 0.687 | 0.675 | 0.641 | 949.041 |
| OLS + vizinhos (coord. imputadas) | 0.675 | 0.665 | 0.629 | 968.370 |
| Gradient boosting sem coordenadas | 0.760 | 0.744 | 0.724 | 819.476 |
| Gradient boosting com lat/lon reais | 0.772 | 0.757 | 0.736 | 802.851 |
| Gradient boosting com lat/lon imputadas | 0.771 | 0.756 | 0.734 | 809.121 |
| Gradient boosting + setor IBGE | 0.781 | 0.767 | 0.740 | 791.290 |
| Gradient boosting imputadas + vizinhos | 0.778 | 0.768 | 0.740 | 793.796 |
| Gradient boosting imputadas + vizinhos + setor | 0.784 | 0.772 | 0.743 | 783.193 |
| OLS + vizinhos + Censo | 0.684 | 0.673 | 0.638 | 956.396 |
| Gradient boosting + Censo | 0.783 | 0.766 | 0.744 | 789.021 |
| Gradient boosting imputadas + vizinhos + Censo | 0.786 | 0.770 | 0.744 | 785.624 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.786 | 0.774 | 0.743 | 781.068 |
| GB completo + terreno e texto (sem vizinhos) | 0.806 | 0.794 | 0.772 | 740.624 |
| GB completo + terreno e texto | 0.806 | 0.797 | 0.770 | 740.575 |

### R2 e MAE, so sem coordenadas reais (n teste temporal = 1188)

| modelo | holdout | 5-fold | temporal | MAE temporal (R$/m2) |
|---|---|---|---|---|
| OLS base (sem coordenadas) | 0.604 | 0.606 | 0.596 | 986.639 |
| OLS + vizinhos (kNN, so coord. reais) | 0.599 | 0.608 | 0.602 | 983.969 |
| OLS + vizinhos (coord. imputadas) | 0.599 | 0.607 | 0.610 | 966.988 |
| Gradient boosting sem coordenadas | 0.714 | 0.733 | 0.725 | 784.203 |
| Gradient boosting com lat/lon reais | 0.709 | 0.729 | 0.722 | 793.144 |
| Gradient boosting com lat/lon imputadas | 0.712 | 0.733 | 0.730 | 779.728 |
| Gradient boosting + setor IBGE | 0.712 | 0.729 | 0.729 | 781.069 |
| Gradient boosting imputadas + vizinhos | 0.709 | 0.728 | 0.723 | 788.465 |
| Gradient boosting imputadas + vizinhos + setor | 0.709 | 0.729 | 0.728 | 781.289 |
| OLS + vizinhos + Censo | 0.602 | 0.610 | 0.614 | 959.609 |
| Gradient boosting + Censo | 0.710 | 0.731 | 0.728 | 783.981 |
| Gradient boosting imputadas + vizinhos + Censo | 0.710 | 0.729 | 0.728 | 780.639 |
| Gradient boosting imputadas + vizinhos + setor + Censo | 0.711 | 0.727 | 0.730 | 780.818 |
| GB completo + terreno e texto (sem vizinhos) | 0.740 | 0.756 | 0.754 | 735.503 |
| GB completo + terreno e texto | 0.739 | 0.754 | 0.755 | 738.849 |

## Figuras

- `reports/figures/geo_mapa_preco_m2.png`
- `reports/figures/geo_mapa_residuos.png`
