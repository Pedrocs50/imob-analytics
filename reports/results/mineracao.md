# Mineracao de dados dos anuncios (VivaReal, Jacarei)
Gerado por `python main.py mineracao`. Leituras descritivas: sao **associacoes, nao efeitos causais**. Anuncios com R$/m2 fora do intervalo 1%-99% foram retirados.

## Apartamento (3914 anuncios)

### 1. Associacao com o R$/m2 (Spearman)

| caracteristica | n | spearman com R$/m2 |
|---|---|---|
| suites | 3299 | 0.32 |
| banheiros | 3914 | 0.26 |
| vagas | 3817 | 0.25 |
| no de comodidades | 3914 | 0.22 |
| condominio (R$) | 3675 | 0.18 |
| area util | 3914 | 0.12 |
| quartos | 3914 | 0.12 |
| area total | 3826 | 0.09 |

### 2. Grupos de imoveis (K-means, k=4, por area, quartos, suites e vagas)

| grupo | anuncios | area_mediana | quartos | suites | vagas | preco_m2_mediano | preco_mediano |
|---|---|---|---|---|---|---|---|
| 0 | 902 | 50.0 | 2.0 | 0.0 | 1.0 | 5512.8 | 280000.0 |
| 1 | 958 | 64.0 | 2.0 | 1.0 | 1.0 | 7076.1 | 440000.0 |
| 2 | 343 | 84.0 | 3.0 | 1.0 | 1.0 | 5185.2 | 460000.0 |
| 3 | 1031 | 86.0 | 3.0 | 1.0 | 2.0 | 7258.8 | 620000.0 |

### 3. Termos do anuncio: maior e menor efeito sobre o preco relativo ao bairro (termos em 150+ anuncios)

**Associados a preco acima do bairro**

| termo | anuncios com o termo | efeito vs bairro (%) |
|---|---|---|
| gourmet | 1317 | 7.9 |
| vagas garagem | 882 | 7.2 |
| lavabo | 172 | 6.9 |
| varanda | 1190 | 6.6 |
| vagas | 1174 | 6.5 |
| academia | 1360 | 5.6 |
| completa | 571 | 5.1 |
| lazer | 1810 | 4.9 |
| piscina | 1657 | 4.5 |
| vista | 749 | 4.5 |
| suíte | 1949 | 4.4 |
| planejados | 1132 | 4.4 |

**Associados a preco abaixo do bairro**

| termo | anuncios com o termo | efeito vs bairro (%) |
|---|---|---|
| vaga | 2027 | -2.9 |
| vaga garagem | 1724 | -2.2 |
| banheiro | 1932 | -2.2 |
| valores | 566 | -2.0 |
| aviso prévio | 579 | -1.8 |
| para venda | 615 | -1.5 |
| quartos | 1047 | -1.5 |
| prévio | 673 | -1.0 |
| sala estar | 648 | -0.9 |
| bairro | 815 | -0.7 |
| ótima | 593 | -0.6 |
| aviso | 682 | -0.6 |

## Casa (10051 anuncios)

### 1. Associacao com o R$/m2 (Spearman)

| caracteristica | n | spearman com R$/m2 |
|---|---|---|
| condominio (R$) | 6385 | 0.50 |
| no de comodidades | 10051 | 0.34 |
| suites | 8749 | 0.29 |
| banheiros | 10051 | 0.25 |
| vagas | 9659 | 0.22 |
| quartos | 10051 | 0.15 |
| area total | 10004 | 0.14 |
| area util | 10051 | -0.02 |

### 2. Grupos de imoveis (K-means, k=4, por area, quartos, suites e vagas)

| grupo | anuncios | area_mediana | quartos | suites | vagas | preco_m2_mediano | preco_mediano |
|---|---|---|---|---|---|---|---|
| 0 | 2029 | 90.0 | 2.0 | 1.0 | 2.0 | 4301.1 | 375000.0 |
| 1 | 3528 | 170.0 | 3.0 | 1.0 | 2.0 | 4263.6 | 700000.0 |
| 2 | 1891 | 250.0 | 3.0 | 1.0 | 4.0 | 5357.1 | 1378000.0 |
| 3 | 1091 | 388.0 | 4.0 | 4.0 | 4.0 | 5277.8 | 2014000.0 |

### 3. Termos do anuncio: maior e menor efeito sobre o preco relativo ao bairro (termos em 150+ anuncios)

**Associados a preco acima do bairro**

| termo | anuncios com o termo | efeito vs bairro (%) |
|---|---|---|
| condomínio | 3390 | 15.7 |
| salão festas | 1064 | 11.5 |
| festas | 1183 | 11.3 |
| quadra | 1093 | 11.1 |
| portaria | 815 | 11.0 |
| playground | 865 | 9.9 |
| piscina | 2765 | 9.3 |
| segurança | 1907 | 9.1 |
| completa | 1017 | 8.6 |
| planejados | 1989 | 8.6 |
| área gourmet | 2463 | 8.6 |
| gourmet | 3444 | 8.6 |

**Associados a preco abaixo do bairro**

| termo | anuncios com o termo | efeito vs bairro (%) |
|---|---|---|
| sobrado | 2802 | -4.6 |
| venda jardim | 1567 | -4.0 |
| bairro | 2970 | -2.7 |
| agora | 1567 | -2.3 |
| ótima | 1387 | -1.4 |
| agende visita | 5123 | -1.1 |
| comércios | 1497 | -0.9 |
| sala cozinha | 1581 | -0.8 |
| agende | 5448 | -0.6 |
| localizada | 1987 | -0.5 |
| coberta | 2221 | -0.3 |
| para venda | 1623 | -0.3 |
