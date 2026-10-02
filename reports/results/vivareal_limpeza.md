# Limpeza do dataset VivaReal Jacarei

Gerado por `python main.py vivareal-prep`. Nao editar manualmente.
Banco de origem (somente leitura): `data/raw/vivareal_jacarei/vivareal_jacarei_20260324.db`

## Etapas comuns

| Etapa | Linhas |
|---|---|
| registros na tabela `listings` | 23128 |
| usage_type = RESIDENTIAL | 21191 |
| apos remover duplicatas por `external_id` (mantido o `scraped_at` mais recente; 1984 removidas) | 19207 |

## Segmento: apartamento

| Etapa (cumulativa) | Linhas restantes |
|---|---|
| tipos APARTMENT, PENTHOUSE, FLAT (-15110) | 4097 |
| preco e area validos (>0) (-0) | 4097 |
| preco de venda entre 100,000 e 3,000,000 (-10) | 4087 |
| area util entre 20 e 300 m2 (-19) | 4068 |
| preco_m2 entre 1,500 e 20,000 (-0) | 4068 |
| quartos <= 5, banheiros <= 6, vagas <= 5 (-13) | 4055 |
| outliers de preco_m2 por IQR (fator 1.5) por property_type (-63) | 3992 |

Ajustes de valores no segmento apartamento (nenhuma linha removida):

| variavel | faixa plausivel | zeros mantidos (sem taxa) | positivos abaixo do minimo -> ausente | acima do maximo -> ausente | informados ao final |
|---|---|---|---|---|---|
| condominio mensal (R$) | 50 a 5000 | 169 | 6 | 9 | 3748 |
| IPTU anual (R$) | 50 a 30000 | 512 | 265 | 1 | 2566 |

## Segmento: casa

| Etapa (cumulativa) | Linhas restantes |
|---|---|
| tipos HOME, CONDOMINIUM, TWO_STORY_HOUSE (-8538) | 10669 |
| preco e area validos (>0) (-0) | 10669 |
| preco de venda entre 100,000 e 6,000,000 (-21) | 10648 |
| area util entre 30 e 1500 m2 (-80) | 10568 |
| preco_m2 entre 500 e 20,000 (-7) | 10561 |
| quartos <= 8, banheiros <= 8, vagas <= 10 (-92) | 10469 |
| outliers de preco_m2 por IQR (fator 1.5) por property_type (-215) | 10254 |

Ajustes de valores no segmento casa (nenhuma linha removida):

| variavel | faixa plausivel | zeros mantidos (sem taxa) | positivos abaixo do minimo -> ausente | acima do maximo -> ausente | informados ao final |
|---|---|---|---|---|---|
| condominio mensal (R$) | 50 a 5000 | 3033 | 23 | 8 | 6522 |
| IPTU anual (R$) | 50 a 30000 | 1725 | 313 | 19 | 6640 |

## Arquivos gerados

| Arquivo | Linhas |
|---|---|
| `data/processed/vivareal/apartamento.csv` | 3992 |
| `data/processed/vivareal/casa.csv` | 10254 |
| `data/processed/vivareal/residencial.csv` | 14246 |

Valores ausentes foram mantidos (sem imputacao). `em_condominio` so existe
para casas; fica vazio em apartamentos. Coordenadas lat/lon = 0 viraram vazias.
Taxas de condominio e IPTU positivas fora da faixa plausivel viraram ausentes (zero = sem taxa,
mantido). `condominio_informado` e `iptu_informado` indicam se a taxa existe apos o ajuste.
