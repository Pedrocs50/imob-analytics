# Auditoria da base VivaReal Jacarei

Fonte: `data/raw/vivareal_jacarei/vivareal_jacarei_20260324.db`, tabela `listings`
(aberta somente para leitura; nenhum dado foi alterado).
Data da auditoria: 2026-09-29.

Este documento descreve o que a base contem e quais problemas ela tem. As
decisoes de limpeza ficam para a etapa seguinte (pipeline do dataset limpo).

## Resumo

- 23.128 linhas, 37 colunas. Todos os anuncios sao `status = ACTIVE`, cidade
  Jacarei (2 linhas de outras cidades) e coletados em 20-21/03/2026.
- Todos os anuncios tem `sale_price`. Apenas 586 (2,5%) tem `rental_price`,
  e todos esses tambem tem preco de venda.
- Ha problemas que afetam a qualidade da modelagem: duplicatas por
  `external_id`, precos e areas absurdos, e mistura de tipos de imovel com
  precos por m2 muito diferentes.

## 1. Composicao

| Campo | Valores |
|---|---|
| `usage_type` | RESIDENTIAL 21.191, COMMERCIAL 1.937 |
| `listing_type` | USED 23.127, DEVELOPMENT 1 (coluna sem variacao util) |
| `status` | ACTIVE em 100% (sem variacao) |

`property_type` (principais): HOME 8.634, APARTMENT 4.446, CONDOMINIUM 3.135,
RESIDENTIAL_ALLOTMENT_LAND 2.819, ALLOTMENT_LAND 1.236, FARM 798,
COMMERCIAL_PROPERTY 544, COMMERCIAL_ALLOTMENT_LAND 480, OFFICE 473,
SHED_DEPOSIT_WAREHOUSE 236, entre outros.

Mediana de preco por m2 (venda) por tipo, para mostrar que misturar tipos nao
faz sentido em um unico modelo sem tratamento:

| Tipo | Mediana R$/m2 |
|---|---|
| OFFICE | ~6.714 |
| APARTMENT | ~6.310 |
| CONDOMINIUM | ~6.086 |
| SHED_DEPOSIT_WAREHOUSE | ~4.000 |
| HOME | ~3.935 |
| FARM | ~3.234 |
| COMMERCIAL_PROPERTY | ~3.193 |
| COMMERCIAL_ALLOTMENT_LAND | ~1.090 |
| RESIDENTIAL_ALLOTMENT_LAND | ~975 |
| ALLOTMENT_LAND | ~133 |

## 2. Valores ausentes

| Coluna | % nula |
|---|---|
| `rental_price` | 97,5 |
| `lat`, `lon` | 49,4 (11.419 linhas), mais 2 linhas com lat/lon = 0 |
| `street_number` | 49,0 |
| `street` | 34,8 |
| `yearly_iptu` | 32,0 |
| `monthly_condo` | 27,6 |
| `suites` | 20,3 |
| `parking_spaces` | 12,8 |
| `total_area_m2` | 0,9 |
| `bedrooms`, `bathrooms` | 0,1 |

Observacoes:

- Metade da base nao tem coordenadas. Usar geolocalizacao reduz a amostra pela
  metade, a menos que se use o bairro como alternativa.
- `yearly_iptu` e `monthly_condo` ausentes podem significar "nao informado" ou
  "nao se aplica" (por exemplo, terrenos). Isso ainda nao foi verificado.

## 3. Duplicatas

- `hash` e `url` sao unicos (0 duplicatas), mas `external_id` nao: 20.960
  valores distintos em 23.128 linhas.
- 3.714 linhas pertencem a um `external_id` repetido (1.546 ids, em media 2,4
  linhas por id, maximo 11).
- Em 769 desses ids o preco varia entre as linhas, ou seja, ha registros do
  mesmo anuncio com precos diferentes.
- 6.621 linhas compartilham tipo, preco, area, quartos, banheiros e bairro com
  outra linha. Pode ser o mesmo imovel anunciado por varias imobiliarias ou
  os mesmos anuncios repetidos. Falta investigar qual caso predomina.

## 4. Precos e areas

- `sale_price`: minimo R$ 1.000, mediana ~R$ 535 mil, p99 ~R$ 12,1 milhoes,
  maximo R$ 1,4 bilhao. Ha precos claramente invalidos nas duas pontas.
- `usable_area_m2`: minimo 0 (19 linhas nulas ou <= 0), mediana 167 m2, p99
  ~36.300 m2, maximo ~659 milhoes de m2. Contem erros de digitacao e areas de
  terrenos e chacaras misturadas com imoveis construidos.
- Preco por m2 (venda): mediana ~R$ 4.310, p1 ~R$ 73, p99 ~R$ 34.960, maximo
  R$ 52 milhoes. 1.884 linhas estao abaixo de R$ 500/m2 e 328 acima de
  R$ 20.000/m2.
- `rental_price`: 586 valores, mediana ~R$ 4.700, maximo R$ 700.000. Amostra
  pequena e com valores suspeitos; nao serve como alvo de modelagem no estado
  atual.
- Comodos: `bedrooms` chega a 39, `bathrooms` a 56, `parking_spaces` a 550.
  Ha valores implausiveis.

## 5. Dimensao temporal

- `scraped_at`: 2026-03-20 22:06 a 2026-03-21 01:36 (uma unica coleta).
- `updated_at`: 21.475 dos 23.128 registros foram atualizados em marco/2026.
  Ou seja, o campo reflete a atualizacao recente, nao a data em que o preco
  foi fixado.
- `created_at`: de 2017 a 2026. Contagem por ano: 2017-2021 = 183;
  2022 = 496; 2023 = 1.007; 2024 = 2.291; 2025 = 9.751; 2026 (ate marco) =
  9.400. Em marco/2026 sao 6.119 anuncios criados, mais que qualquer mes
  anterior; isso pode refletir a dinamica real ou um efeito da coleta e
  precisa ser interpretado com cuidado.
- Conclusao: e um snapshot com viés de sobrevivencia. Nao ha preco historico.
  Uma serie por `created_at` seria uma serie de anuncios ativos hoje,
  agrupados pela data de publicacao, e nao um indice de precos.

## 6. Localizacao

- 137 bairros distintos; 20 tem menos de 10 anuncios.
- Concentracao alta: Loteamento Villa Branca (2.367), Centro (1.998), Jardim
  California (1.348), Jardim Santa Maria (955) e Condominio Residencial Mirante
  do Vale (827). Loteamentos e condominios grandes aparecem como "bairro".

## 7. Anunciantes

Poucos anunciantes concentram muitos anuncios (Amagai Consultoria 2.844,
Imobiliaria Franca 2.051, Ademir Imoveis 1.127, Geo Brokers 886, Grupo
Intervale 876). Um mesmo empreendimento repetido em varios anuncios pode
distorcer o modelo.

## 8. Relacao com o baseline atual (Random Forest)

O treino atual (`src/pricing/random_forest.py`, `src/pricing/config.py`) filtra a
base por limites fixos (preco entre R$ 100 mil e R$ 2 milhoes, area entre 20
e 300 m2, R$/m2 entre 2.000 e 16.000) e por outliers via IQR dentro de cada
`property_type`. Restam 18.453 das 23.128 linhas.

Pontos para revisar antes de comparar o baseline com outros modelos:

1. **Duplicatas.** O codigo nao remove `external_id` repetidos. Se linhas do
   mesmo anuncio caem no treino e no teste, o R2 de 0,78 pode estar
   otimista. Isto e uma hipotese: ainda nao foi testado.
2. **Coluna `dataset_limpo.csv`.** Nao guarda `external_id`, entao nao da para
   rastrear quais linhas do banco entraram no treino.
3. **Faixa de preco.** Os limites de `config.py` (com trechos comentados para
   casas) sugerem que o modelo foi ajustado mais para apartamentos. Os
   limites nao estao documentados na metodologia.
4. **Escopo.** O recorte final descarta terrenos, fazendas, comerciais e
   imoveis acima de R$ 2 milhoes. Isso deve constar nas conclusoes.

## 9. Pendencias para o pipeline de limpeza

Decisoes a tomar na proxima etapa (nao tomadas aqui):

- Como tratar `external_id` duplicado (manter o registro mais recente? o de
  menor `scraped_at`?).
- Definir o escopo: apenas residencial? quais `property_type`?
- Regras para precos e areas invalidos (limites fixos ou por tipo).
- Se coordenadas ausentes sao imputadas por bairro ou se a analise
  geografica usa so as linhas com lat/lon.
- Verificar o significado de `amenities` (o exemplo lido estava vazio) antes
  de confiar em `amenities_count`.
- Confirmar se `rental_price` vale como variavel de demanda (meta 4 fala em
  "preco e demanda") ou se fica de fora.
