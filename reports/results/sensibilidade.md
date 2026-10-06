# Sensibilidade e relevancia das variaveis (meta 7)

Gerado por `python main.py sensibilidade`. Nao editar manualmente. Leitura em `docs/SENSIBILIDADE.md`.

Modelo: conjunto LightGBM + HistGradientBoosting com os parametros de `modelos_avancados.md`. Relevancia: permutacao do grupo no teste temporal (5 repeticoes). Cenarios e bairros: modelo ajustado em todo o segmento. Tempo: 148 s.

## Relevancia por grupo: apartamento (MAE do conjunto no teste: R$ 680/m2)

| grupo | colunas | aumento do MAE (R$/m2) | desvio | aumento relativo (%) |
|---|---|---|---|---|
| Localizacao fina (coordenadas e vizinhos) | 5 | 360.36 | 9.40 | 52.96 |
| Texto do anuncio | 150 | 140.91 | 6.75 | 20.71 |
| Setor e Censo 2022 | 8 | 110.43 | 3.63 | 16.23 |
| Tamanho (area util) | 1 | 108.87 | 3.97 | 16.00 |
| Comodos e vagas | 5 | 107.77 | 7.87 | 15.84 |
| Contexto (tamanho relativo, anuncios, centro) | 4 | 77.73 | 4.79 | 11.42 |
| Bairro | 1 | 72.65 | 1.41 | 10.68 |
| Terreno (casas) | 2 | 37.74 | 3.61 | 5.55 |
| Condominio (taxa e tipo) | 3 | 31.59 | 1.31 | 4.64 |

## Relevancia por grupo: casa (MAE do conjunto no teste: R$ 637/m2)

| grupo | colunas | aumento do MAE (R$/m2) | desvio | aumento relativo (%) |
|---|---|---|---|---|
| Bairro | 1 | 237.33 | 10.74 | 37.23 |
| Contexto (tamanho relativo, anuncios, centro) | 4 | 206.94 | 5.12 | 32.46 |
| Tamanho (area util) | 1 | 192.50 | 7.97 | 30.20 |
| Condominio (taxa e tipo) | 3 | 192.32 | 11.15 | 30.17 |
| Texto do anuncio | 150 | 165.80 | 5.05 | 26.01 |
| Terreno (casas) | 2 | 158.53 | 5.99 | 24.87 |
| Comodos e vagas | 5 | 150.06 | 6.70 | 23.54 |
| Setor e Censo 2022 | 8 | 85.19 | 3.67 | 13.36 |
| Localizacao fina (coordenadas e vizinhos) | 5 | 45.47 | 4.68 | 7.13 |

## Cenarios 'e se?' (efeito medio por imovel, mantendo o resto)

Efeito sobre os imoveis do proprio segmento aos quais a mudanca se aplica (as previsoes sao dentro da amostra de treino; o que importa e a diferenca).

| segmento | cenario | imoveis | variacao mediana do R$/m2 (%) | q25 (%) | q75 (%) | variacao mediana do preco total (R$) |
|---|---|---|---|---|---|---|
| apartamento | +10% de area util | 3992 | -3.14 | -5.10 | -1.55 | 24373.12 |
| apartamento | +1 suite | 3369 | 4.55 | 2.16 | 8.48 | 19998.19 |
| apartamento | +1 vaga | 3894 | 2.31 | 0.41 | 4.93 | 9388.11 |
| apartamento | +1 quarto | 3992 | 0.08 | -0.40 | 0.75 | 308.58 |
| apartamento | +1 banheiro | 3992 | 0.89 | 0.26 | 1.94 | 3413.65 |
| apartamento | +R$ 100 na taxa de condominio | 3579 | 1.08 | -0.28 | 2.92 | 4004.34 |
| casa | +10% de area util | 10254 | -3.16 | -5.28 | -1.24 | 39868.16 |
| casa | +1 suite | 8915 | 0.85 | -0.01 | 3.21 | 6709.01 |
| casa | +1 vaga | 9852 | 0.82 | 0.00 | 2.73 | 5795.11 |
| casa | +1 quarto | 10254 | 0.77 | 0.11 | 2.68 | 5888.53 |
| casa | +1 banheiro | 10254 | 0.91 | 0.35 | 1.97 | 6515.25 |
| casa | +50 m2 de terreno | 10206 | 4.23 | 0.96 | 8.41 | 26913.34 |
| casa | casa passa a ser em condominio | 7614 | 7.07 | 3.07 | 12.34 | 43530.14 |

## Imovel de referencia por bairro (R$/m2 estimado; bairros com 30+ anuncios)

### apartamento: 10 mais caros e 5 mais baratos

| bairro | R$/m2 do imovel de referencia | anuncios | R$/m2 mediano dos anuncios | diferenca para a mediana dos bairros (%) |
|---|---|---|---|---|
| Loteamento Villa Branca | 8415.8 | 402 | 8659.8 | 60.7 |
| Jardim Pereira do Amparo | 7183.8 | 149 | 6625.0 | 37.2 |
| Jardim Paraíba | 6504.8 | 91 | 7870.4 | 24.2 |
| Pagador de Andrade | 6497.5 | 316 | 7247.3 | 24.1 |
| Parque dos Príncipes | 6288.9 | 45 | 6808.5 | 20.1 |
| Jardim Califórnia | 5780.3 | 685 | 7191.0 | 10.4 |
| Centro | 5627.0 | 318 | 6111.1 | 7.5 |
| Vila Aprazível | 5556.0 | 140 | 7722.8 | 6.1 |
| Jardim Flórida | 5533.9 | 95 | 4885.2 | 5.7 |
| São João | 5414.6 | 53 | 5555.6 | 3.4 |
| Loteamento Jardim Sol Nascente | 4552.0 | 92 | 4759.3 | -13.1 |
| Vila Nova Aliança | 4480.2 | 116 | 5602.0 | -14.4 |
| Bairro do Colonia | 4461.3 | 92 | 5205.5 | -14.8 |
| Jardim Yolanda | 4258.4 | 50 | 5115.1 | -18.7 |
| Jardim Novo Amanhecer | 3885.2 | 40 | 3697.8 | -25.8 |

### casa: 10 mais caros e 5 mais baratos

| bairro | R$/m2 do imovel de referencia | anuncios | R$/m2 mediano dos anuncios | diferenca para a mediana dos bairros (%) |
|---|---|---|---|---|
| Condomínio Vem Viver Jacareí | 6096.7 | 221 | 7970.0 | 82.1 |
| Condomínio Residencial Mirante do Vale | 5754.1 | 398 | 6118.1 | 71.8 |
| Jardim Pereira do Amparo | 5448.8 | 30 | 5833.3 | 62.7 |
| Condomínio Sunset Garden | 5076.7 | 36 | 6956.3 | 51.6 |
| Condomínio Residence Club | 4937.2 | 65 | 7342.3 | 47.4 |
| Loteamento Villa Branca | 4872.2 | 1211 | 5748.0 | 45.5 |
| Jardim Residencial Golden Park | 4705.9 | 98 | 6158.2 | 40.5 |
| Condomínio Residencial Fogaça | 4658.3 | 124 | 6813.7 | 39.1 |
| Jardim Crystal Park | 4571.1 | 57 | 7555.6 | 36.5 |
| Loteamento Residencial Parque Lago Dourado | 4335.6 | 41 | 5300.0 | 29.5 |
| Jardim Paraíso | 2239.7 | 132 | 2649.1 | -33.1 |
| Conjunto São Benedito | 2190.3 | 64 | 2517.1 | -34.6 |
| Cidade Nova Jacareí | 2189.1 | 134 | 2777.8 | -34.6 |
| Jardim do Vale | 2161.1 | 50 | 2278.2 | -35.5 |
| Parque Imperial | 1929.8 | 97 | 3153.8 | -42.4 |

## Figuras

- `reports/figures/sensibilidade_grupos.png`
- `reports/figures/sensibilidade_curvas.png`
- `reports/figures/sensibilidade_bairros.png`

