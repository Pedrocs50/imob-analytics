# Mineracao avancada dos anuncios (VivaReal, Jacarei)
Gerado por `python main.py mineracao-avancada`. Complementa `mineracao.md`. A pergunta: **o que faz um imovel custar mais que os vizinhos do mesmo bairro?** O preco/m2 de cada anuncio e dividido pela mediana do proprio bairro (bairros com 15+ anuncios); a classe "alto" e o terco mais caro nessa comparacao. Sao **associacoes, nao efeitos causais**.

## Apartamento (3759 anuncios; "alto" = R$/m2 pelo menos 8% acima do bairro)

### 1. Regras de associacao: o que acompanha preco alto para o bairro

Probabilidade base de "alto": 33%. **Confianca** = % dos anuncios com a combinacao que sao "alto"; **lift** = confianca / base (lift 1,5 = 50% mais chance que a media). Combinacoes de ate 3 itens em 112+ anuncios; so entra regra maior que melhora a menor em 3 pontos.

| se o anuncio tem | anuncios | suporte (%) | confianca (%) | lift |
|---|---|---|---|---|
| area gourmet + varanda + 3+ quartos | 365 | 9.7 | 56.2 | 1.7 |
| area gourmet + seguranca + area acima da mediana | 286 | 7.6 | 55.6 | 1.7 |
| area gourmet + seguranca + 3+ quartos | 215 | 5.7 | 55.3 | 1.7 |
| varanda + academia + 2+ vagas | 208 | 5.5 | 55.3 | 1.7 |
| quadra + seguranca + area acima da mediana | 181 | 4.8 | 55.2 | 1.7 |
| area gourmet + 2+ vagas | 542 | 14.4 | 55.2 | 1.7 |
| area gourmet + quadra + area acima da mediana | 324 | 8.6 | 54.9 | 1.6 |
| area gourmet + varanda + seguranca | 257 | 6.8 | 54.5 | 1.6 |
| quadra + playground + 2+ vagas | 230 | 6.1 | 54.3 | 1.6 |
| area gourmet + varanda + area acima da mediana | 510 | 13.6 | 54.3 | 1.6 |

**Teste em dados nao vistos:** as 10 melhores regras escolhidas numa metade dos anuncios e medidas na outra. Lift medio 1.73 (onde foram escolhidas) -> 1.52 (nao vistos). Se continua bem acima de 1, a regra nao e acaso de selecao.

| regra (escolhida na metade A) | lift na metade A | anuncios na metade B | lift na metade B (nao vista) |
|---|---|---|---|
| area gourmet + varanda + 2+ vagas | 1.87 | 179 | 1.60 |
| area gourmet + varanda + 3+ quartos | 1.80 | 183 | 1.58 |
| area gourmet + seguranca + area acima da mediana | 1.79 | 155 | 1.56 |
| area gourmet + 2+ vagas | 1.76 | 279 | 1.56 |
| varanda + quadra + academia | 1.72 | 135 | 1.45 |
| varanda + portaria + armarios planejados | 1.69 | 111 | 1.52 |
| varanda + 2+ vagas | 1.68 | 230 | 1.42 |
| area gourmet + quadra + area acima da mediana | 1.67 | 169 | 1.62 |
| area gourmet + armarios planejados + area acima da mediana | 1.67 | 211 | 1.52 |
| seguranca + 2+ vagas + 3+ quartos | 1.67 | 175 | 1.33 |

### 2. Arvore de decisao (profundidade 3, 70% treino / 30% teste)

| medida | valor (%) |
|---|---|
| acuracia no teste | 66.3 |
| acuracia de quem sempre chuta a classe mais comum | 66.7 |
| AUC no teste | 58.9 |
| acuracia (validacao cruzada, 5 partes) | 63.0 |

Figura: `reports/figures/mineracao_arvore_apartamento.png`. Regras:

```
|--- vagas <= 1.50
|   |--- area util <= 74.50
|   |   |--- banheiros <= 1.50
|   |   |   |--- class: False
|   |   |--- banheiros >  1.50
|   |   |   |--- class: False
|   |--- area util >  74.50
|   |   |--- class: False
|--- vagas >  1.50
|   |--- condominio <= 578.50
|   |   |--- comodidades <= 10.50
|   |   |   |--- class: False
|   |   |--- comodidades >  10.50
|   |   |   |--- class: False
|   |--- condominio >  578.50
|   |   |--- class: True
```

### 3. Grupos de imoveis (K-means, k=4)

Silhueta por k (maior = grupos mais separados): k=2: 0.52, k=3: 0.55, k=4: 0.59, k=5: 0.61, k=6: 0.63, k=7: 0.59, k=8: 0.53. Maior silhueta em k=6; usamos k=4 porque os grupos ficam interpretaveis (ver perfil). Estabilidade com 5 sementes (ARI): 1.00 (1 = mesmos grupos).

| grupo | anuncios | area_mediana | quartos | suites | vagas | preco_m2_mediano |
|---|---|---|---|---|---|---|
| 1 | 858 | 52.0 | 2.0 | 0.0 | 1.0 | 5476.2 |
| 2 | 927 | 64.0 | 2.0 | 1.0 | 1.0 | 7109.4 |
| 3 | 332 | 84.0 | 3.0 | 1.0 | 1.0 | 5227.3 |
| 4 | 997 | 86.0 | 3.0 | 1.0 | 2.0 | 7285.7 |

Figura: `reports/figures/mineracao_grupos_apartamento.png`.

### 4. Validacao da correlacao (bootstrap e metades)

IC95% por 200 reamostragens; "metade A/B" = o mesmo calculo em duas metades aleatorias dos dados (se parecidas, o resultado nao e acaso de amostra).

| caracteristica | n | spearman | IC95 inf | IC95 sup | metade A | metade B |
|---|---|---|---|---|---|---|
| suites | 3177 | 0.33 | 0.30 | 0.36 | 0.30 | 0.36 |
| vagas | 3665 | 0.26 | 0.23 | 0.29 | 0.26 | 0.26 |
| banheiros | 3759 | 0.26 | 0.23 | 0.29 | 0.25 | 0.27 |
| no de comodidades | 3759 | 0.21 | 0.18 | 0.24 | 0.20 | 0.23 |
| condominio (R$) | 3535 | 0.19 | 0.16 | 0.22 | 0.18 | 0.19 |
| area util | 3759 | 0.14 | 0.10 | 0.17 | 0.12 | 0.16 |
| quartos | 3759 | 0.13 | 0.09 | 0.16 | 0.13 | 0.13 |
| area total | 3673 | 0.11 | 0.07 | 0.14 | 0.10 | 0.12 |

Figura: `reports/figures/mineracao_correlacao_apartamento.png`.

### 5. Imoveis fora da curva (preco pedido x esperado)

O preco esperado vem de um modelo (LightGBM) que ve so caracteristicas, bairro e coordenadas, com previsao fora da amostra (cada anuncio e previsto por um modelo que nao o viu). Anuncios muito fora do esperado sao **candidatos a revisar**: erro de cadastro, sobrepreco ou oportunidade. Nao e prova de que o imovel esta caro ou barato: o modelo nao ve estado de conservacao, acabamento nem fotos.

| medida | valor |
|---|---|
| R2 do log(R$/m2) fora da amostra | 0.73 |
| erro percentual mediano | 8.08 |
| % dos anuncios a ate 20% do esperado | 85.93 |
| % mais de 30% ACIMA do esperado | 3.38 |
| % mais de 30% ABAIXO do esperado | 1.01 |

**Mais abaixo do esperado**

| bairro | area (m2) | quartos | vagas | preco pedido (R$) | R$/m2 pedido | R$/m2 esperado | diferenca (%) |
|---|---|---|---|---|---|---|---|
| Jardim Califórnia | 98.0 | 3.0 | 2.0 | 320000.0 | 3265.3 | 7066.2 | -53.8 |
| Centro | 96.0 | 3.0 | 2.0 | 298000.0 | 3104.2 | 6598.6 | -53.0 |
| Jardim Califórnia | 97.0 | 2.0 | 1.0 | 298000.0 | 3072.2 | 6145.7 | -50.0 |
| Jardim Califórnia | 68.0 | 2.0 | 1.0 | 260000.0 | 3823.5 | 7322.0 | -47.8 |
| Jardim Califórnia | 100.0 | 3.0 | 2.0 | 403000.0 | 4030.0 | 7623.3 | -47.1 |
| Jardim Califórnia | 97.0 | 3.0 | 2.0 | 375000.0 | 3866.0 | 7264.3 | -46.8 |
| Jardim Califórnia | 126.0 | 3.0 | 1.0 | 383000.0 | 3039.7 | 5573.2 | -45.5 |
| Jardim Califórnia | 94.0 | 3.0 | 2.0 | 320000.0 | 3404.3 | 6141.3 | -44.6 |

**Mais acima do esperado**

| bairro | area (m2) | quartos | vagas | preco pedido (R$) | R$/m2 pedido | R$/m2 esperado | diferenca (%) |
|---|---|---|---|---|---|---|---|
| Jardim Califórnia | 56.0 | 2.0 | 1.0 | 610000.0 | 10892.9 | 5519.6 | 97.3 |
| Jardim Califórnia | 88.0 | 3.0 | 2.0 | 850000.0 | 9659.1 | 5061.7 | 90.8 |
| Vila Aprazível | 124.0 | 3.0 | 2.0 | 1272000.0 | 10258.1 | 5703.7 | 79.8 |
| Jardim Califórnia | 65.0 | 2.0 | 1.0 | 640000.0 | 9846.2 | 5564.9 | 76.9 |
| Jardim Flórida | 55.0 | 2.0 | 1.0 | 480000.0 | 8727.3 | 4933.6 | 76.9 |
| Jardim Califórnia | 56.0 | 2.0 | 1.0 | 620000.0 | 11071.4 | 6351.1 | 74.3 |
| Jardim Marister | 178.0 | 2.0 | 4.0 | 1272000.0 | 7146.1 | 4265.9 | 67.5 |
| Jardim Yolanda | 102.0 | 2.0 | 3.0 | 890000.0 | 8725.5 | 5230.2 | 66.8 |

Figura: `reports/figures/mineracao_fora_da_curva_apartamento.png`.

### 6. Tempo de anuncio no ar x preco relativo ao bairro

Correlacao de Spearman entre dias no ar e preco relativo ao bairro: **-0.03** (fraca). Tempo no ar = data da coleta menos a data de criacao do anuncio; anuncios antigos podem estar desatualizados.

| faixa | anuncios | preco_m2_mediano | vs bairro (%) |
|---|---|---|---|
| ate 30 dias | 1364 | 6098.8 | 0.0 |
| 31-90 dias | 352 | 6666.7 | 2.3 |
| 91-180 dias | 661 | 6231.9 | -0.1 |
| 181-365 dias | 715 | 6521.2 | 1.5 |
| 1 a 2 anos | 508 | 6000.0 | -1.6 |
| mais de 2 anos | 159 | 5729.2 | -5.2 |

## Casa (9865 anuncios; "alto" = R$/m2 pelo menos 14% acima do bairro)

### 1. Regras de associacao: o que acompanha preco alto para o bairro

Probabilidade base de "alto": 33%. **Confianca** = % dos anuncios com a combinacao que sao "alto"; **lift** = confianca / base (lift 1,5 = 50% mais chance que a media). Combinacoes de ate 3 itens em 295+ anuncios; so entra regra maior que melhora a menor em 3 pontos.

| se o anuncio tem | anuncios | suporte (%) | confianca (%) | lift |
|---|---|---|---|---|
| piscina + seguranca + armarios planejados | 483 | 4.9 | 55.7 | 1.7 |
| seguranca + armarios planejados + em condominio fechado | 503 | 5.1 | 54.9 | 1.6 |
| quadra + armarios planejados | 547 | 5.5 | 52.5 | 1.6 |
| playground + armarios planejados | 464 | 4.7 | 51.5 | 1.5 |
| armarios planejados + em condominio fechado | 1092 | 11.1 | 51.3 | 1.5 |
| seguranca + salao de festas | 479 | 4.9 | 50.5 | 1.5 |
| academia + armarios planejados | 483 | 4.9 | 50.5 | 1.5 |
| portaria + armarios planejados | 429 | 4.3 | 50.3 | 1.5 |
| portaria + seguranca | 449 | 4.6 | 49.7 | 1.5 |
| area gourmet + seguranca | 986 | 10.0 | 49.4 | 1.5 |

**Teste em dados nao vistos:** as 10 melhores regras escolhidas numa metade dos anuncios e medidas na outra. Lift medio 1.67 (onde foram escolhidas) -> 1.50 (nao vistos). Se continua bem acima de 1, a regra nao e acaso de selecao.

| regra (escolhida na metade A) | lift na metade A | anuncios na metade B | lift na metade B (nao vista) |
|---|---|---|---|
| seguranca + armarios planejados + em condominio fechado | 1.79 | 275 | 1.53 |
| piscina + seguranca + armarios planejados | 1.73 | 267 | 1.62 |
| area gourmet + portaria + seguranca | 1.70 | 184 | 1.48 |
| churrasqueira + seguranca + salao de festas | 1.68 | 191 | 1.53 |
| quadra + armarios planejados | 1.67 | 302 | 1.50 |
| area gourmet + armarios planejados + em condominio fechado | 1.65 | 389 | 1.51 |
| churrasqueira + playground + armarios planejados | 1.65 | 220 | 1.53 |
| area gourmet + seguranca + em condominio fechado | 1.63 | 335 | 1.52 |
| portaria + armarios planejados | 1.62 | 237 | 1.42 |
| portaria + seguranca | 1.59 | 238 | 1.40 |

### 2. Arvore de decisao (profundidade 3, 70% treino / 30% teste)

| medida | valor (%) |
|---|---|
| acuracia no teste | 71.6 |
| acuracia de quem sempre chuta a classe mais comum | 66.7 |
| AUC no teste | 73.4 |
| acuracia (validacao cruzada, 5 partes) | 68.3 |

Figura: `reports/figures/mineracao_arvore_casa.png`. Regras:

```
|--- area util <= 110.50
|   |--- quartos <= 2.50
|   |   |--- area util <= 84.50
|   |   |   |--- class: True
|   |   |--- area util >  84.50
|   |   |   |--- class: False
|   |--- quartos >  2.50
|   |   |--- area util <= 89.50
|   |   |   |--- class: True
|   |   |--- area util >  89.50
|   |   |   |--- class: True
|--- area util >  110.50
|   |--- condominio <= 301.00
|   |   |--- quartos <= 2.50
|   |   |   |--- class: False
|   |   |--- quartos >  2.50
|   |   |   |--- class: False
|   |--- condominio >  301.00
|   |   |--- area util <= 426.00
|   |   |   |--- class: False
|   |   |--- area util >  426.00
|   |   |   |--- class: False
```

### 3. Grupos de imoveis (K-means, k=4)

Silhueta por k (maior = grupos mais separados): k=2: 0.40, k=3: 0.27, k=4: 0.25, k=5: 0.28, k=6: 0.30, k=7: 0.29, k=8: 0.27. Maior silhueta em k=2; usamos k=4 porque os grupos ficam interpretaveis (ver perfil). **Silhueta baixa em k=4: os perfis se sobrepoem; ler como descricao de perfis, nao como segmentos distintos**. Estabilidade com 5 sementes (ARI): 0.98 (1 = mesmos grupos).

| grupo | anuncios | area_mediana | quartos | suites | vagas | preco_m2_mediano |
|---|---|---|---|---|---|---|
| 1 | 1873 | 90.0 | 2.0 | 1.0 | 2.0 | 4254.4 |
| 2 | 3536 | 165.0 | 3.0 | 1.0 | 2.0 | 4345.7 |
| 3 | 1957 | 252.0 | 3.0 | 2.0 | 4.0 | 5333.3 |
| 4 | 1040 | 384.0 | 4.0 | 4.0 | 4.0 | 5298.3 |

Figura: `reports/figures/mineracao_grupos_casa.png`.

### 4. Validacao da correlacao (bootstrap e metades)

IC95% por 200 reamostragens; "metade A/B" = o mesmo calculo em duas metades aleatorias dos dados (se parecidas, o resultado nao e acaso de amostra).

| caracteristica | n | spearman | IC95 inf | IC95 sup | metade A | metade B |
|---|---|---|---|---|---|---|
| condominio (R$) | 6288 | 0.50 | 0.48 | 0.52 | 0.52 | 0.47 |
| no de comodidades | 9865 | 0.34 | 0.33 | 0.36 | 0.34 | 0.35 |
| suites | 8611 | 0.28 | 0.26 | 0.30 | 0.29 | 0.28 |
| banheiros | 9865 | 0.24 | 0.22 | 0.26 | 0.23 | 0.25 |
| vagas | 9480 | 0.22 | 0.21 | 0.24 | 0.21 | 0.24 |
| quartos | 9865 | 0.15 | 0.13 | 0.16 | 0.12 | 0.17 |
| area total | 9818 | 0.13 | 0.12 | 0.15 | 0.12 | 0.15 |
| area util | 9865 | -0.03 | -0.05 | -0.01 | -0.04 | -0.01 |

Figura: `reports/figures/mineracao_correlacao_casa.png`.

### 5. Imoveis fora da curva (preco pedido x esperado)

O preco esperado vem de um modelo (LightGBM) que ve so caracteristicas, bairro e coordenadas, com previsao fora da amostra (cada anuncio e previsto por um modelo que nao o viu). Anuncios muito fora do esperado sao **candidatos a revisar**: erro de cadastro, sobrepreco ou oportunidade. Nao e prova de que o imovel esta caro ou barato: o modelo nao ve estado de conservacao, acabamento nem fotos.

| medida | valor |
|---|---|
| R2 do log(R$/m2) fora da amostra | 0.76 |
| erro percentual mediano | 11.63 |
| % dos anuncios a ate 20% do esperado | 73.18 |
| % mais de 30% ACIMA do esperado | 8.12 |
| % mais de 30% ABAIXO do esperado | 4.16 |

**Mais abaixo do esperado**

| bairro | area (m2) | quartos | vagas | preco pedido (R$) | R$/m2 pedido | R$/m2 esperado | diferenca (%) |
|---|---|---|---|---|---|---|---|
| Jardim Jacinto | 256.0 | 3.0 | 3.0 | 400000.0 | 1562.5 | 6086.6 | -74.3 |
| Jardim Pereira do Amparo | 300.0 | 5.0 | nan | 620000.0 | 2066.7 | 5774.7 | -64.2 |
| Parque Califórnia | 247.0 | 3.0 | 3.0 | 530000.0 | 2145.7 | 5441.2 | -60.6 |
| Loteamento Villa Branca | 224.0 | 3.0 | 1.0 | 385000.0 | 1718.8 | 4330.0 | -60.3 |
| Jardim Alvorada | 55.0 | 2.0 | 2.0 | 120000.0 | 2181.8 | 5349.0 | -59.2 |
| Loteamento Villa Branca | 235.0 | 3.0 | 4.0 | 480000.0 | 2042.6 | 4822.7 | -57.6 |
| Centro | 200.0 | 4.0 | nan | 280000.0 | 1400.0 | 3163.0 | -55.7 |
| Centro | 550.0 | 5.0 | 3.0 | 800000.0 | 1454.5 | 3254.8 | -55.3 |

**Mais acima do esperado**

| bairro | area (m2) | quartos | vagas | preco pedido (R$) | R$/m2 pedido | R$/m2 esperado | diferenca (%) |
|---|---|---|---|---|---|---|---|
| Vila Zezé | 165.0 | 5.0 | 3.0 | 1400000.0 | 8484.8 | 2522.4 | 236.4 |
| Centro | 220.0 | 2.0 | 2.0 | 1600000.0 | 7272.7 | 2712.2 | 168.1 |
| Jardim das Indústrias | 174.0 | 2.0 | 4.0 | 1070000.0 | 6149.4 | 2299.6 | 167.4 |
| Cidade Nova Jacareí | 244.0 | 2.0 | 2.0 | 1000000.0 | 4098.4 | 1538.5 | 166.4 |
| Jardim Esperança | 250.0 | 3.0 | 2.0 | 1378000.0 | 5512.0 | 2106.8 | 161.6 |
| Vila Aprazível | 215.0 | 3.0 | 2.0 | 1400000.0 | 6511.6 | 2575.4 | 152.8 |
| Cidade Jardim | 1000.0 | 6.0 | 4.0 | 5800000.0 | 5800.0 | 2356.9 | 146.1 |
| Centro | 401.0 | 4.0 | 2.0 | 2500000.0 | 6234.4 | 2573.2 | 142.3 |

Figura: `reports/figures/mineracao_fora_da_curva_casa.png`.

### 6. Tempo de anuncio no ar x preco relativo ao bairro

Correlacao de Spearman entre dias no ar e preco relativo ao bairro: **-0.06** (fraca). Tempo no ar = data da coleta menos a data de criacao do anuncio; anuncios antigos podem estar desatualizados.

| faixa | anuncios | preco_m2_mediano | vs bairro (%) |
|---|---|---|---|
| ate 30 dias | 2832 | 4412.8 | 1.2 |
| 31-90 dias | 660 | 4850.7 | 2.3 |
| 91-180 dias | 1764 | 4420.7 | 0.7 |
| 181-365 dias | 1928 | 4462.5 | 0.6 |
| 1 a 2 anos | 1723 | 4324.3 | -1.5 |
| mais de 2 anos | 958 | 3992.5 | -5.8 |
