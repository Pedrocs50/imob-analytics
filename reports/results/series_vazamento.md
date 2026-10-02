# Validacao de vazamento temporal

Gerado por `python main.py series-painel`. Nao editar manualmente.

Convencao: a linha do mes `t` dos paineis `painel_mensal.csv` e `painel_trimestral.csv`
contem so o que estava publicado ate o ultimo dia do mes `t`. Os arquivos `*_referencia.csv`
usam a data de referencia e servem so para o alvo, nunca para as variaveis explicativas.

**Resultado: APROVADO** (0 falha(s))

## Testes

| Teste | Verificacoes | Falhas |
|---|---|---|
| T1 defasagem declarada x aplicada | 47 | 0 |
| T2 perturbacao do futuro (mensal e trimestral) | 528 | 0 |
| T3 validade do valor trimestral | 448 | 0 |

O validador tambem e testado contra vazamentos plantados de proposito:

- detectado: IPCA aplicado sem defasagem (T1 deve reprovar)
- detectado: deflator com base no fim da amostra (T2 deve reprovar)

## Defasagens aplicadas

`L` = meses entre o ultimo mes do periodo de referencia e a divulgacao (catalogo). No painel trimestral, o deslocamento e de `k = ceil(L/3)` trimestres.

| Serie | L | k (trimestres) | Situacao | Fonte |
|---|---|---|---|---|
| `bcb_selic_meta` | 0 | 0 | estimada (nao confirmada) | decisao do Copom e conhecida no ato |
| `bcb_selic_mes` | 0 | 0 | estimada (nao confirmada) | acumulada no mes, conhecida no ultimo dia do mes |
| `bcb_ipca` | 1 | 1 | confirmada | calendario oficial do IBGE: divulgado 9 a 12 dias apos o fim do mes |
| `bcb_igpm` | 0 | 0 | estimada (nao confirmada) | FGV divulga no fim do proprio mes |
| `bcb_incc` | 0 | 0 | estimada (nao confirmada) | FGV divulga no fim do proprio mes |
| `bcb_ptax` | 0 | 0 | estimada (nao confirmada) | media mensal conhecida no ultimo dia do mes |
| `bcb_ibcbr` | 2 | 1 | estimada (nao confirmada) | publicacao do BCB cerca de 45 dias apos o mes |
| `bcb_credimob_saldo` | 1 | 1 | estimada (nao confirmada) | estatisticas de credito do BCB no mes seguinte |
| `bcb_credimob_juros_mercado` | 1 | 1 | estimada (nao confirmada) | estatisticas de credito do BCB no mes seguinte |
| `bcb_credimob_juros_regulada` | 1 | 1 | estimada (nao confirmada) | estatisticas de credito do BCB no mes seguinte |
| `ipea_icc` | 1 | 1 | confirmada | Fecomercio-SP: jun/2025 divulgado em 14/07/2025 e fev/2026 em 16/03/2026 |
| `ipea_desocupacao_br_mensal` | 2 | 1 | estimada (nao confirmada) | PNAD mensal sai 26-33 dias apos o mes (IBGE); a mensalizacao do IPEA e posterior; 2 e conservador |
| `ibge_desocupacao_sp` | 2 | 1 | confirmada | calendario oficial do IBGE (PNAD Continua trimestral): 44 a 51 dias apos o fim do trimestre |
| `ibge_renda_sp` | 2 | 1 | confirmada | calendario oficial do IBGE (PNAD Continua trimestral): 44 a 51 dias apos o fim do trimestre |
| `fipezap_*` (35 series) | 1 | 1 | confirmada | evidencia indireta: relatorios de referencia t publicados no mes t+1; sem calendario oficial legivel |

Colunas derivadas herdam a maior defasagem das series de entrada.
