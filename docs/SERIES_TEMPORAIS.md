# Series temporais: FipeZAP e variaveis macroeconomicas

Base de dados da trilha temporal (ARIMA/ARIMAX e LSTM). Fica separada do
`imoveis.db` do scraper. Data do estudo e da migracao: 2026-09-30.

## Como reproduzir

```bash
python main.py series-coletar   # 14 series macro pelas APIs publicas (BCB, IPEA, IBGE)
python main.py series-fipezap   # le o Excel do FipeZAP em data/raw/
python main.py series-painel    # valida, testa vazamento temporal e gera os paineis
```

`series-painel` termina com erro (codigo 1) se o teste de vazamento reprovar.

| Saida | Local |
|---|---|
| Banco (series, observacoes, log de coletas) | `data/database/series_temporais.db` |
| Resposta original das APIs (uma por coleta) | `data/raw/macro/<fonte>/<serie>_<data>.json` |
| **Painel mensal as-of** (preditores e series defasadas) | `data/processed/series/painel_mensal.csv` |
| Painel mensal de referencia (so para o alvo) | `data/processed/series/painel_mensal_referencia.csv` |
| **Painel trimestral as-of** | `data/processed/series/painel_trimestral.csv` |
| Painel trimestral de referencia (so para o alvo) | `data/processed/series/painel_trimestral_referencia.csv` |
| Relatorio de qualidade das series | `reports/results/series_qualidade.md` |
| Relatorio do teste de vazamento e defasagens aplicadas | `reports/results/series_vazamento.md` |

Codigo: `src/timeseries/` (`catalogo.py`, `clients.py`, `collect.py`,
`fipezap.py`, `storage.py`, `quality.py`, `panel.py`, `vazamento.py`).

## Tempo de publicacao e vazamento (convencao dos paineis)

Uma serie tem **data de referencia** (o mes ou trimestre a que o valor se
refere) e **data de divulgacao** (quando alguem pode ve-lo). Usar o valor de
julho numa previsao feita em julho e vazamento se ele so foi publicado em
agosto.

- **Painel as-of** (`painel_mensal.csv`, `painel_trimestral.csv`): a linha do
  mes `t` contem so o que estava publicado ate o ultimo dia de `t`. Uma serie
  com defasagem `L` (meses entre o ultimo mes do periodo e a divulgacao) tem o
  valor do mes de referencia `r` na linha `r + L`. **Use este painel para as
  variaveis explicativas** (inclusive o FipeZAP defasado).
- **Painel de referencia** (`*_referencia.csv`): cada valor esta na sua data de
  referencia, sem deslocamento. Serve para definir o **alvo** (o FipeZAP do mes
  `t` que se quer prever) e para descrever a serie. Nao use como preditor.
- **Trimestral:** o trimestre so e conhecido depois de terminar mais `L`
  meses; por isso as colunas sao deslocadas `k = ceil(L/3)` trimestres.
- **Series trimestrais no painel mensal** (`*_ffill`): o valor do trimestre `q`
  aparece no mes `q + 2 + L` e vale ate a proxima divulgacao esperada (3 meses).
  Depois disso fica **ausente**: nao ha repeticao por anos. Isso mantem os
  trimestres sem publicacao da fonte (renda de SP em 2020-2022) como lacuna.
- **Colunas derivadas** herdam a maior defasagem das entradas. O preco real
  do FipeZAP deflaciona pelo IPCA acumulado desde o inicio do painel (base
  constante e causal); o painel antigo usava o IPCA do fim da amostra.

### Defasagens e fontes consultadas (2026-09-30)

| Serie | L | Situacao | Evidencia |
|---|---|---|---|
| IPCA (`bcb_ipca`) | 1 | confirmada | [Calendario oficial de divulgacoes do IBGE (API)](https://servicodados.ibge.gov.br/api/v3/calendario/): divulgacoes de 2026 (ex.: 10/02, 12/03, 10/04, 12/05, 12/06, 10/07, 11/08, 11/09) ocorrem 9 a 12 dias apos o fim do mes de referencia |
| PNAD trimestral (`ibge_desocupacao_sp`, `ibge_renda_sp`) | 2 | confirmada | Mesmo calendario do IBGE, produto "PNAD Continua trimestral": 44 a 51 dias apos o fim do trimestre (ex.: 1o tri/2026 divulgado em 14/05/2026) |
| ICC (`ipea_icc`, Fecomercio-SP) | 1 | confirmada | Jun/2025 divulgado em 14/07/2025 ([Times Brasil](https://timesbrasil.com.br/brasil/fecomerciosp-confianca-do-consumidor-na-capital-cai-111-em-junho-ante-igual-mes-de-2024/)); fev/2026 divulgado em 16/03/2026 ([Panrotas](https://www.panrotas.com.br/mercado/economia-e-politica/2026/03/familias-paulistanas-iniciaram-fevereiro-mais-dispostas-a-consumir-aponta-fecomerciosp_226751.html)) |
| FipeZAP (`fipezap_*`) | 1 | confirmada por evidencia indireta | Relatorios mensais de referencia `t` publicados no mes `t+1` (arquivos [fipezap-202605-residencial-venda.pdf](https://static.poder360.com.br/2026/06/fipezap-202605-residencial-venda.pdf), em pasta de 2026/06, e `fipezap-202604` em 2026/05); o resultado de junho/2026 e comparado com o IPCA-15 de junho (divulgado em 25/06), ou seja, antes do IPCA de junho (10/07). **O calendario oficial de divulgacao do site da Fipe nao estava legivel** ([pagina do indice](https://www.fipe.org.br/pt-br/indices/fipezap/)); tratar como confirmacao parcial |
| IBC-Br, credito imobiliario, IGP-M, INCC, Selic, PTAX, desocupacao mensalizada (IPEA) | 0 a 2 | **estimada** | Mantidas como estavam; nao foram confirmadas em calendario oficial nesta etapa (a lista completa esta em `reports/results/series_vazamento.md`) |

Limitacoes que o teste de vazamento **nao** cobre:

- **Revisao de dados:** os valores foram coletados em 2026-09; a versao de hoje
  pode diferir da que existia na epoca. O IBC-Br dessazonalizado teve todos os
  218 meses revisados entre abril e setembro (ate 0,26%). IPCA, PTAX e FipeZAP
  nao mudaram. Um backtest em tempo real exigiria versoes historicas.
- As defasagens marcadas como estimadas podem estar erradas em 1 mes.

### Teste de vazamento (`src/timeseries/vazamento.py`)

Roda em toda execucao de `series-painel` e escreve
`reports/results/series_vazamento.md`:

1. **T1, declarada x aplicada:** cada serie do painel as-of deve ser a serie
   original deslocada exatamente pela defasagem do catalogo.
2. **T2, perturbacao do futuro:** reconstroi os paineis depois de adulterar todos
   os dados posteriores a datas de corte (2013-06, 2018-09, 2022-03, 2025-01) e
   exige que nenhuma linha anterior ao corte (mais a defasagem da coluna)
   mude. Vale para colunas base, derivadas, ffill e para o painel trimestral.
3. **T3, validade trimestral:** recalcula de forma independente qual trimestre
   deveria estar visivel em cada mes e exige valor ausente quando ele passou de
   3 meses.
4. **Auto-teste:** o validador precisa reprovar dois vazamentos plantados de
   proposito (IPCA sem defasagem e deflator com base no fim da amostra).

## FipeZAP

Fonte: `data/raw/fipezap-serieshistoricas (2).xlsx` (59 abas; usamos duas).

- Aba **Indice FipeZAP** (composto nacional): 224 meses, 2008-01 a 2026-08,
  residencial com detalhamento de 1 a 4 dormitorios, e comercial desde 2012.
- Aba **Sao Jose dos Campos**: 104 meses, 2018-01 a 2026-08. Jacarei nao consta
  na planilha.
- Guardamos numero-indice, preco medio (R$/m2) e rentabilidade do aluguel.
  Variacao mensal e em 12 meses sao derivaveis e sao recalculadas no painel.
- **Os precos sao medias moveis trimestrais** (nota da planilha; fonte ZAP e
  IBGE). A serie e suavizada e autocorrelacionada; considerar na metodologia.
- Conferencia com o CSV anterior: 99 meses em comum, diferenca maxima de R$ 0,48
  (arredondamento do CSV). Nao houve revisao de valores.
- No Excel o yield vem como fracao (0,004); foi convertido para % a.m. (0,4).

## Series macro coletadas

| Id | Fonte | Codigo | O que e | Freq | Defasagem de divulgacao |
|---|---|---|---|---|---|
| `bcb_selic_meta` | BCB | 432 | Meta Selic (% a.a.), ultimo valor do mes | M | 0 |
| `bcb_selic_mes` | BCB | 4390 | Selic acumulada no mes | M | 0 |
| `bcb_ipca` | BCB | 433 | IPCA, variacao mensal | M | 1 |
| `bcb_igpm` | BCB | 189 | IGP-M, variacao mensal | M | 0 |
| `bcb_incc` | BCB | 192 | INCC-M, variacao mensal | M | 0 |
| `bcb_ptax` | BCB | 3698 | Dolar venda, media mensal | M | 0 |
| `bcb_ibcbr` | BCB | 24363 | IBC-Br dessazonalizado | M | 2 meses |
| `bcb_credimob_saldo` | BCB | 20612 | Saldo do credito imobiliario PF (direcionado), R$ milhoes | M | 1 |
| `bcb_credimob_juros_mercado` | BCB | 25497 | Juros do financiamento imobiliario, taxas de mercado | M | 1 |
| `bcb_credimob_juros_regulada` | BCB | 25498 | Juros do financiamento imobiliario, taxas reguladas | M | 1 |
| `ipea_icc` | IPEA | FCESP12_IIC12 | Confianca do consumidor (Fecomercio-SP) | M | 1 |
| `ipea_desocupacao_br_mensal` | IPEA | PNADC12_TDESOCM12 | Desocupacao Brasil, mensalizada | M | 2 |
| `ibge_desocupacao_sp` | SIDRA | 4099 / var. 4099 | Taxa de desocupacao, SP | **Q** | 2 |
| `ibge_renda_sp` | SIDRA | 5436 / var. 5933 | Rendimento medio real habitual, todos os trabalhos, SP | **Q** | 2 |

Os codigos de credito imobiliario foram localizados no catalogo de dados
abertos do BCB e validados na API. A defasagem `L` e o numero de meses entre o
ultimo mes do periodo de referencia e a divulgacao; IPCA, PNAD e ICC estao
confirmados em fontes (tabela em "Defasagens e fontes consultadas"), as demais
sao estimativas.

## Problemas do fluxo antigo (`src/macro/`, tabela `indicadores_macro`) e correcoes

O fluxo antigo continua no repositorio para o comando legado, mas **nao deve
ser usado para modelagem**. Erros encontrados e como foram resolvidos:

| Problema no fluxo antigo | Correcao |
|---|---|
| IGP-M e INCC gravados como "variacao mensal (%)", mas eram **indices** (base ago/1994 = 100); o codigo `IGP12_INCCDI12` nao existe e caiu num fallback | Uso das series SGS 189 e 192, que sao a variacao mensal, com unidade e tipo no catalogo |
| Periodos trimestrais do IBGE (`AAAAQQ`) lidos como `AAAAMM`: cada trimestre virou "jan a abr" | O periodo e lido como trimestre, e a data e o primeiro dia do trimestre |
| Colunas `4099`, `5933`, `5941` (codigos de **variavel**) tomadas por periodo, gerando datas nos anos 4099, 5933 e 5941; linhas ruins nunca foram apagadas | Coluna do periodo identificada pelo cabecalho do SIDRA, variavel escolhida pelo codigo, nao por texto |
| Renda media do banco era quase toda o coeficiente de variacao (2,1 a 3,4), nao o rendimento em R$ | Variavel explicita 5933 (R$) |
| ICC configurado com codigo inexistente; a coleta falhou so com um aviso | Codigo correto `FCESP12_IIC12`; falha de coleta agora fica registrada e aparece no relatorio |
| Selic de abril/2026 era um mes incompleto (coleta em 17/04) | Series calculadas sobre o mes descartam o mes corrente |
| Series desde 1944/1980 (hiperinflacao, outras moedas) | Banco guarda apenas de 2005 em diante; a resposta bruta completa fica em `data/raw/macro` |
| Sem validacao, sem log, sem defasagem, banco desatualizado | Validacao de faixa, lacunas e datas em `series_qualidade.md`; log em `coletas`; defasagem no catalogo |

Achados sobre as APIs:

- O SGS do BCB responde **HTTP 200 com uma pagina HTML** quando recusa a
  requisicao, e recusa de forma intermitente janelas de ~3.000 dias ou mais em
  series diarias. O cliente usa janelas de 1.800 dias e repete a chamada.
- A renda do SIDRA (tabela 5436) tem lacunas na propria fonte: so o 1o trimestre
  de 2020 e nenhum de 2021. E registrada como aviso, nao falha.

## Agregacao e derivadas

(O alinhamento no tempo esta descrito em "Tempo de publicacao e vazamento".)

- **Painel mensal:** degraus nas colunas `_ffill` sao esperados; para modelos
  sensiveis a isso, use o painel trimestral.
- **Painel trimestral:** taxas viram variacao composta no trimestre, saldos
  e indices acumulados usam o ultimo valor, niveis usam a media (so quando os
  tres meses existem). Series PNAD entram como publicadas. O trimestre em curso
  e excluido. A variacao mensal nao e agregada.
- **Derivadas:** IPCA acumulado (indice e 12 meses), preco de venda do FipeZAP
  em reais constantes do inicio do painel (deflacionado pelo IPCA), variacao
  mensal e em 12 meses dos indices, IGP-M e INCC acumulados em 12 meses e
  Selic real. Ao deflacionar por uma base fixa, o nivel do preco real fica em
  "reais de 2008"; a base nao usa dados posteriores.
- Valores ausentes ficam ausentes (sem imputacao). Cada modelo decide o recorte.

## Limitacoes

- FipeZAP SJC tem 104 meses (34 trimestres); o nacional tem 224 meses.
- Ainda nao ha serie especifica de Jacarei. Series municipais (populacao, PIB,
  emprego formal) ficam como candidatas futuras.
- A serie do IBC-Br termina dois meses antes do FipeZAP; nos meses finais do
  painel algumas colunas macro estao vazias por atraso de divulgacao.
- **Renda de SP (`ibge_renda_sp`):** a tabela 5436 do SIDRA (variavel 5933,
  rendimento medio mensal real, habitualmente recebido em todos os trabalhos)
  nao traz o 2o ao 4o trimestre de 2020 nem os quatro de 2021 nem o 1o de 2022.
  Esses periodos ficam **ausentes** nos paineis. A serie nao foi substituida por
  outra tabela: isso exigiria comparar antes a definicao da variavel (populacao,
  habitual x efetivo, deflator), o que nao foi feito.
- Atualizar o FipeZAP exige baixar o Excel novo manualmente; nao ha API.
