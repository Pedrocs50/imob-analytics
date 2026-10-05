# Mapa de R$/m2 por setor censitario do IBGE (Jacarei)

Gerado por `python main.py mapa-setores`. Nao editar manualmente.

Malha: setores censitarios do Censo 2022 (IBGE), 544 em Jacarei (`data\raw\ibge\jacarei_setores_2022.gpkg`). Cada anuncio **com coordenada real** e associado ao setor que o contem; setores com menos de 5 anuncios ficam em branco. Os valores sao o **nivel** de preco (snapshot de marco/2026), nao crescimento: o crescimento por area exige varios snapshots.

| Segmento | Anuncios com coordenadas reais | Setores com algum anuncio | Setores com 5+ anuncios | Mediana dos setores (R$/m2) | Min - max das medianas |
|---|---|---|---|---|---|
| apartamento | 1907 | 198 | 105 | 5682 | 3000 - 9692 |
| casa | 4973 | 404 | 280 | 3704 | 1912 - 8411 |

## apartamento: 8 setores mais caros e 8 mais baratos (5+ anuncios)

| CD_SETOR | anuncios | R$/m2 mediano | area (km2) |
|---|---|---|---|
| 352440205000598 | 45 | 9692.31 | 0.11 |
| 352440205000493 | 5 | 9384.62 | 0.34 |
| 352440205000595 | 10 | 9258.45 | 0.10 |
| 352440205000693 | 5 | 8983.05 | 0.00 |
| 352440205000586 | 13 | 8888.89 | 0.01 |
| 352440205000378 | 10 | 8881.18 | 0.07 |
| 352440205000136 | 6 | 8863.64 | 0.08 |
| 352440205000498 | 29 | 8860.76 | 0.13 |
| 352440205000545 | 5 | 3837.21 | 0.07 |
| 352440205000147 | 6 | 3834.90 | 0.06 |
| 352440205000504 | 8 | 3809.87 | 0.04 |
| 352440205000561 | 10 | 3704.45 | 0.01 |
| 352440205000483 | 14 | 3700.00 | 0.12 |
| 352440205000631 | 5 | 3500.00 | 0.02 |
| 352440205000010 | 7 | 3409.09 | 0.22 |
| 352440205000023 | 10 | 3000.00 | 0.04 |

## casa: 8 setores mais caros e 8 mais baratos (5+ anuncios)

| CD_SETOR | anuncios | R$/m2 mediano | area (km2) |
|---|---|---|---|
| 352440205000246 | 9 | 8411.21 | 0.01 |
| 352440205000620 | 35 | 7970.00 | 0.39 |
| 352440205000602 | 20 | 7896.57 | 0.06 |
| 352440205000596 | 9 | 7888.89 | 0.06 |
| 352440205000601 | 27 | 7843.14 | 0.03 |
| 352440205000162 | 12 | 7596.15 | 0.37 |
| 352440205000364 | 58 | 7437.75 | 0.14 |
| 352440205000166 | 45 | 7361.11 | 0.09 |
| 352440205000195 | 10 | 2166.13 | 0.10 |
| 352440205000704 | 10 | 2139.52 | 0.04 |
| 352440205000173 | 15 | 2097.20 | 0.07 |
| 352440205000199 | 8 | 2053.03 | 0.16 |
| 352440205000095 | 6 | 2026.27 | 0.05 |
| 352440205000025 | 20 | 2024.73 | 0.03 |
| 352440205000544 | 6 | 1943.89 | 0.06 |
| 352440205000446 | 12 | 1911.90 | 0.07 |

## Arquivos

- `reports/figures/geo_mapa_setores.png`
- `reports/figures/mapa_setores_interativo.html` (interativo: abra no navegador; alterna apartamento e casa; passe o mouse sobre um setor)
- `reports/results/eda/setores_preco.csv` (todos os setores, com contagens e quantis)

