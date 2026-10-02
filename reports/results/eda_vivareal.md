# Analise exploratoria: datasets VivaReal (apartamento, casa, residencial)

Gerado por `python main.py eda-vivareal`. Nao editar manualmente. Fonte: `data/processed/vivareal/*.csv`
(saida de `vivareal-prep`). A leitura esta em `docs/ANALISE_EXPLORATORIA.md`.

## 1. Resumo por segmento

| segmento | n | preco_m2 mediana | preco_m2 media | desvio | p5 | p95 | assimetria | assimetria do log | preco mediano (R$) | area mediana (m2) | quartos (mediana) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| apartamento | 3992 | 6174.76 | 6386.22 | 1816.61 | 3806.85 | 9482.90 | 0.40 | -0.28 | 410000.00 | 65.00 | 2.00 |
| casa | 10254 | 4375.00 | 4646.29 | 1947.65 | 1964.29 | 8214.29 | 0.58 | -0.39 | 660000.00 | 171.00 | 3.00 |
| residencial | 14246 | 4941.52 | 5133.85 | 2065.32 | 2133.75 | 8750.00 | 0.42 | -0.56 | 550000.00 | 125.00 | 3.00 |

## 2. Valores ausentes (%)

| variavel (% ausente) | apartamento | casa | residencial |
|---|---|---|---|
| area util | 0.0 | 0.0 | 0.0 |
| quartos | 0.0 | 0.0 | 0.0 |
| banheiros | 0.0 | 0.0 | 0.0 |
| suites | 15.6 | 13.1 | 13.8 |
| vagas | 2.5 | 3.9 | 3.5 |
| IPTU anual | 35.7 | 35.2 | 35.4 |
| condominio | 6.1 | 36.4 | 27.9 |
| latitude | 52.2 | 51.5 | 51.7 |
| longitude | 52.2 | 51.5 | 51.7 |

## 3. Por tipo de imovel

| segmento | property_type | n | preco_m2 mediana | area mediana | preco mediano (R$) |
|---|---|---|---|---|---|
| casa | HOME | 7613 | 3840.0 | 156.0 | 551500.0 |
| apartamento | APARTMENT | 3948 | 6193.1 | 65.0 | 410000.0 |
| casa | CONDOMINIUM | 2640 | 6020.7 | 230.0 | 1480000.0 |
| apartamento | PENTHOUSE | 40 | 5331.8 | 111.0 | 595000.0 |
| apartamento | FLAT | 4 | 8538.0 | 40.5 | 362500.0 |
| casa | TWO_STORY_HOUSE | 1 | 2583.3 | 600.0 | 1550000.0 |

## 4. Correlacao (Spearman) das variaveis com preco_m2

| segmento | variavel | n | Spearman com preco_m2 | p |
|---|---|---|---|---|
| apartamento | latitude | 1908 | 0.456 | 0.000 |
| apartamento | suites | 3369 | 0.319 | 0.000 |
| apartamento | banheiros | 3992 | 0.255 | 0.000 |
| apartamento | vagas | 3894 | 0.253 | 0.000 |
| apartamento | n. comodidades | 3992 | 0.228 | 0.000 |
| apartamento | condominio | 3748 | 0.171 | 0.000 |
| apartamento | area util | 3992 | 0.109 | 0.000 |
| apartamento | quartos | 3992 | 0.109 | 0.000 |
| apartamento | longitude | 1908 | 0.109 | 0.000 |
| apartamento | IPTU anual | 2566 | 0.018 | 0.359 |
| casa | condominio | 6522 | 0.512 | 0.000 |
| casa | casa em condominio | 10254 | 0.436 | 0.000 |
| casa | latitude | 4974 | 0.357 | 0.000 |
| casa | n. comodidades | 10254 | 0.356 | 0.000 |
| casa | suites | 8915 | 0.299 | 0.000 |
| casa | banheiros | 10254 | 0.258 | 0.000 |
| casa | vagas | 9852 | 0.228 | 0.000 |
| casa | longitude | 4974 | 0.178 | 0.000 |
| casa | quartos | 10254 | 0.161 | 0.000 |
| casa | IPTU anual | 6640 | 0.145 | 0.000 |
| casa | area util | 10254 | -0.031 | 0.001 |

## 5. Multicolinearidade (VIF; acima de 5 merece atencao, acima de 10 e problema)

| segmento | variavel | n | VIF |
|---|---|---|---|
| apartamento | area util | 3303 | 2.55 |
| apartamento | quartos | 3303 | 2.21 |
| apartamento | banheiros | 3303 | 1.82 |
| apartamento | suites | 3303 | 2.09 |
| apartamento | vagas | 3303 | 1.68 |
| casa | area util | 8704 | 2.04 |
| casa | quartos | 8704 | 1.71 |
| casa | banheiros | 8704 | 2.20 |
| casa | suites | 8704 | 2.01 |
| casa | vagas | 8704 | 1.40 |

## 6. Bairros

| segmento | bairros | com n >= 30 | com n < 10 | top 5 concentram (%) | cobertura dos bairros com n >= 30 (%) | eta2: variancia de log(preco_m2) explicada pelo bairro |
|---|---|---|---|---|---|---|
| apartamento | 71 | 26 | 34 | 46.87 | 92.56 | 0.35 |
| casa | 121 | 69 | 27 | 29.44 | 94.41 | 0.39 |

Os 12 bairros com mais anuncios por segmento:

| segmento | neighborhood | n | preco_m2 mediana |
|---|---|---|---|
| apartamento | Jardim Califórnia | 685 | 7191.0 |
| apartamento | Loteamento Villa Branca | 402 | 8659.8 |
| apartamento | Centro | 318 | 6111.1 |
| apartamento | Pagador de Andrade | 316 | 7247.3 |
| apartamento | Vila Machado | 150 | 5568.1 |
| apartamento | Jardim Pereira do Amparo | 149 | 6625.0 |
| apartamento | Jardim Paraíso | 146 | 5045.6 |
| apartamento | Jardim das Indústrias | 141 | 5485.4 |
| apartamento | Vila Aprazível | 140 | 7722.8 |
| apartamento | Parque Santo Antônio | 124 | 5547.0 |
| apartamento | Jardim Santa Maria | 120 | 5614.0 |
| apartamento | Vila Nova Aliança | 116 | 5602.0 |
| casa | Loteamento Villa Branca | 1211 | 5748.0 |
| casa | Jardim Santa Maria | 542 | 4417.0 |
| casa | Centro | 489 | 3398.1 |
| casa | Condomínio Residencial Mirante do Vale | 398 | 6118.1 |
| casa | Jardim Jacinto | 379 | 6408.7 |
| casa | Residencial Santa Paula | 285 | 4285.7 |
| casa | Cidade Jardim | 274 | 3636.4 |
| casa | Jardim Califórnia | 272 | 4896.8 |
| casa | Residencial Parque dos Sinos | 269 | 4500.0 |
| casa | Vila Zezé | 251 | 4142.9 |
| casa | Cidade Salvador | 239 | 3473.1 |
| casa | Condomínio Vem Viver Jacareí | 221 | 7970.0 |

## 7. Condominio

| analise | valor A | valor B | n A | n B | p (Mann-Whitney) |
|---|---|---|---|---|---|
| casa fora x dentro de condominio (preco_m2 mediana) | 3840.000 | 6020.658 | 7614 | 2640.000 | 0.000 |
| casa fora de condominio: % sem valor de condominio | 47.754 |  | 7614 |  |  |
| casa em condominio: % sem valor de condominio | 3.636 |  | 2640 |  |  |
| apartamento: Spearman(condominio, preco_m2) entre os que tem taxa > 0 | 0.193 |  | 3579 |  | 0.000 |
| casa: Spearman(condominio, preco_m2) entre os que tem taxa > 0 | 0.038 |  | 3489 |  | 0.025 |

Valores implausiveis que a limpeza atual nao trata (pendencia para o `vivareal-prep`):

| segmento | variavel | n com valor | mediana | p1 | p99 | maximo | zeros (sem taxa) | positivos abaixo do limite inferior | acima do limite superior | limites (inferior; superior) |
|---|---|---|---|---|---|---|---|---|---|---|
| apartamento | condominio mensal (R$) | 3748 | 417.0 | 0.0 | 1000.0 | 1800.0 | 169 | 0 | 0 | 50; 5000 |
| apartamento | IPTU anual (R$) | 2566 | 100.0 | 0.0 | 1200.0 | 29034.0 | 512 | 0 | 0 | 50; 30000 |
| casa | condominio mensal (R$) | 6522 | 270.0 | 0.0 | 1309.5 | 2471.0 | 3033 | 0 | 0 | 50; 5000 |
| casa | IPTU anual (R$) | 6640 | 150.0 | 0.0 | 4006.1 | 20909.0 | 1725 | 0 | 0 | 50; 30000 |

## 8. Coordenadas

| segmento | n | com coordenadas (%) | fora da caixa de Jacarei | corr. lat x preco_m2 (Spearman) | corr. lon x preco_m2 (Spearman) |
|---|---|---|---|---|---|
| apartamento | 3992 | 47.796 | 1 | 0.456 | 0.109 |
| casa | 10254 | 48.508 | 1 | 0.357 | 0.178 |
| residencial | 14246 | 48.308 | 2 | 0.374 | 0.143 |

## 9. Tempo (por trimestre de criacao do anuncio)

Anuncios ativos em marco/2026 agrupados pela data de publicacao: ha vies de sobrevivencia; nao e serie de precos.

| trimestre de criacao | n (apartamento) | n (casa) | mediana preco_m2 (apartamento) | mediana preco_m2 (casa) |
|---|---|---|---|---|
| 2022Q1 | 2 | 31 | 5910.0 | 4380.2 |
| 2022Q2 | 20 | 131 | 5434.1 | 3262.5 |
| 2022Q3 | 9 | 44 | 7605.6 | 4680.5 |
| 2022Q4 | 10 | 54 | 6421.2 | 4153.4 |
| 2023Q1 | 11 | 55 | 5687.5 | 3809.5 |
| 2023Q2 | 17 | 145 | 5463.9 | 4561.4 |
| 2023Q3 | 32 | 157 | 5266.2 | 3888.9 |
| 2023Q4 | 29 | 160 | 5217.4 | 3951.3 |
| 2024Q1 | 35 | 176 | 5757.3 | 4325.0 |
| 2024Q2 | 62 | 271 | 5960.5 | 4250.0 |
| 2024Q3 | 97 | 327 | 5562.5 | 4649.1 |
| 2024Q4 | 108 | 328 | 6094.2 | 4625.4 |
| 2025Q1 | 333 | 993 | 6071.4 | 3947.4 |
| 2025Q2 | 288 | 708 | 6436.5 | 4888.7 |
| 2025Q3 | 532 | 1415 | 6418.8 | 4180.3 |
| 2025Q4 | 602 | 1587 | 6175.0 | 4470.6 |
| 2026Q1 | 1788 | 3591 | 6182.9 | 4492.2 |

## Figuras geradas

- `reports/figures/eda_vivareal_distribuicao.png`
- `reports/figures/eda_vivareal_area_preco.png`
- `reports/figures/eda_vivareal_correlacao.png`
- `reports/figures/eda_vivareal_bairros.png`
- `reports/figures/eda_vivareal_condominio.png`
- `reports/figures/eda_vivareal_mapa.png`
