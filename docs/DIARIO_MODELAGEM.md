# Diario de modelagem

Registro corrido das tecnicas usadas, dos problemas de dados contornados e da evolucao das metricas, para
servir de base ao relatorio final. **Atualizar a cada mudanca de modelagem ou de tratamento de dados.**
Ultima atualizacao: 2026-10-02.

## 1. O que estamos prevendo (e com quais dados)

| Trilha | Dados | O que se preve | Estado |
|---|---|---|---|
| **Precificacao** | **VivaReal de Jacarei** (snapshot de marco/2026; 21.191 anuncios residenciais, 19.207 sem duplicatas) | O **R$/m2 de um anuncio** a partir das caracteristicas do imovel e da localizacao. E uma previsao transversal, nao no tempo. | Modelos finais prontos (secoes 3 a 5); projecao para Jacarei na secao 7 |
| **Series temporais** | **FipeZAP** (indice nacional desde 2008 e Sao Jose dos Campos desde 2018; **nao ha Jacarei**) + variaveis macro | O indice de preco ao longo dos meses (ARIMA, ARIMAX, LSTM) | ARIMA, ARIMAX e LSTM prontos (secao 6) |

O VivaReal de Jacarei **nao permite previsao no tempo**: e uma fotografia, e as datas de criacao dos anuncios tem
vies de sobrevivencia. Uma serie temporal propria de Jacarei so existira com **snapshots periodicos** do VivaReal.

Unidade de avaliacao: R2, MAE (R$/m2) e MAPE (%) em **divisao temporal** (treino nos 75% de anuncios mais antigos
pela data de criacao, teste nos 25% mais recentes), a mais exigente. Tambem se reportam holdout aleatorio de 20% e 5-fold.

## 2. Catalogo de tecnicas para dados faltantes, ruidosos ou problematicos

| Problema | Tamanho | Tecnica | Efeito observado |
|---|---|---|---|
| Anuncios duplicados (`external_id` repetido) | 1.984 de 21.191 (9,4%) | Manter o registro com `scraped_at` mais recente | Evita o mesmo anuncio no treino e no teste |
| Precos, areas e comodos absurdos | ex.: preco de R$ 1.000 a R$ 1,4 bilhao | Limites por segmento (apartamento, casa) + outliers por IQR dentro de cada tipo | Dataset limpo por segmento (3.992 / 10.254 / 14.246) |
| Condominio e IPTU implausiveis | condominio > R$ 5.000 (17 anuncios, maximo R$ 2,5 mi); IPTU > R$ 30.000 (20); positivos < R$ 50 | Viram **ausentes** (a linha e mantida); zeros ("sem taxa") preservados | O IPTU dos apartamentos perdeu a correlacao com o preco (era puxada pelos valores absurdos) |
| Unidade do IPTU duvidosa | mediana de R$ 100-150 por ano | **Fora dos modelos** ate confirmar com o orientador | Evita usar variavel possivelmente mal definida |
| Taxa de condominio ausente | 36% nas casas | Indicador `condominio_informado` (a ausencia e informativa: 48% nas casas fora de condominio, 4% nas em condominio) | O valor da taxa so ajuda no modelo linear das casas (+0,03 de R2) |
| Suites ausentes | 13-16% | Mediana + indicador de ausencia (modelo linear); NaN nativo (arvores) | Anuncios sem suites informadas tem R$/m2 15 a 21% menor: a ausencia carrega informacao |
| **Coordenadas ausentes** | ~52% dos anuncios | **Imputacao hierarquica so com coordenadas** (nunca o preco): mediana da rua no bairro (>= 2 anuncios) e, na falta, do bairro (>= 3); indicador `coord_origem` | Cobertura de 99%. Ganho apenas em apartamentos sem coordenada real (R2 0,63 -> 0,66); nulo em casas |
| Bairros e setores raros | 20 a 34 bairros com < 10 anuncios | Agrupar em uma categoria (bairro < 30 anuncios, setor < 15) | Estabiliza o modelo |
| Localizacao fina | - | Preco dos 15 vizinhos reais mais proximos, calculado **sem vazamento** (cada anuncio fica fora do proprio calculo; no teste so o treino conta) | Linear em apartamentos: R2 0,49 -> 0,58 |
| Sem zonas oficiais | - | **Setores censitarios do IBGE (Censo 2022)**: 544 setores de Jacarei, atribuidos por juncao espacial a 98,8-99,8% dos anuncios (100% dos com coordenada real) | Mapa por setor e variavel categorica |
| Poder aquisitivo e entorno | - | **Variaveis do Censo 2022 por setor**: renda do responsavel (media e mediana), densidade, domicilios vagos, moradores por domicilio. Renda ausente em 22 dos 544 setores (sigilo): NaN | Correlacao com R$/m2 de 0,54 (renda, casas); ganho de R2 pequeno (+0 a +0,005) |
| Colinearidade (`tipo` x `em_condominio`) | colinearidade perfeita nas casas | Cada informacao entra uma unica vez | Coeficientes passam a ser interpretaveis |
| Heterocedasticidade | Breusch-Pagan p < 0,001 | Erros-padrao robustos (HC3) | Inferencia confiavel dos coeficientes |
| Vazamento de informacao | - | Divisao temporal; vizinhos leave-one-out; busca de parametros so no treino; imputacao sem usar o alvo | Metricas honestas |
| **Area do terreno** (casas) | nao entrava nos modelos | `log_terreno` e `razao_terreno_construida`; `total_area_m2` passou a ser mantida na limpeza | Casa +0,026 de R2 |
| **Texto do anuncio** | titulo e descricao ignorados | 150 palavras/bigramas binarios (`txt_*`) por CountVectorizer, **sem digitos nem "R$"** (o preco aparece em 19% dos titulos e 8% das descricoes: vazaria o alvo) | Casa +0,014 (temporal), +0,032 (holdout); apartamento ~0 no temporal |
| Idade do anuncio, comodidades, anunciante | testados | **Descartados**: a idade e colinear com a divisao temporal (piora o teste); os demais nao acrescentam | Evita variavel que "ajuda" so por artefato da divisao |
| Busca de parametros lenta | LightGBM/CatBoost com milhares de arvores | Optuna (TPE) com 3 particoes **so no treino**; CatBoost limitado (profundidade 4-7, 150-450 iteracoes, 8 tentativas, `border_count` 64) | Execucao de 65 min em vez de horas; ganho de +0,01 a +0,02 de R2 |
| Incerteza da previsao | erro de 11% a 15% por imovel | **Intervalos conformais** pelo quantil do erro relativo fora da amostra (5 particoes) | Cobertura 81-83% para 80% nominal e ~91% para 90% (teste temporal) |
| Valor "justo" de um anuncio | o modelo viu o proprio anuncio no treino | **Previsao fora da amostra** (5 particoes) para cada anuncio | Erro relativo mediano honesto: 8,1% (apt), 10,4% (casa) |
| Jacarei sem indice proprio | FipeZAP nao cobre | **Proxy**: variacao observada e prevista de Sao Jose dos Campos; cenarios nacional e tendencia de 12 meses como comparacao | Premissa explicita, nao testavel hoje |

Tratamento das series temporais (macro, FipeZAP, defasagens de publicacao, painel "as-of", teste de vazamento) esta em
`docs/SERIES_TEMPORAIS.md`.

## 3. Evolucao do R2 na precificacao (VivaReal de Jacarei)

Divisao temporal, todos os anuncios; R2 | MAE em R$/m2.

| # | Etapa | Apartamento | Casa | Residencial |
|---|---|---|---|---|
| 0 | Baseline: mediana do R$/m2 do bairro | 0,37 \| 1.085 | 0,37 \| 1.208 | 0,33 \| 1.339 |
| 1 | Regressao linear multipla (variaveis do imovel + bairro) | 0,49 \| 1.012 | 0,58 \| 972 | 0,60 \| 1.011 |
| 2 | Linear + preco dos vizinhos (kNN, coord. reais) | 0,58 \| 885 | 0,61 \| 933 | 0,63 \| 961 |
| 3 | Gradient boosting, sem coordenadas | 0,62 \| 830 | 0,72 \| 768 | 0,73 \| 808 |
| 4 | Gradient boosting + lat/lon reais | 0,67 \| 767 | 0,73 \| 762 | 0,73 \| 800 |
| 5 | Gradient boosting + lat/lon **imputadas** | 0,68 \| 760 | 0,73 \| 760 | 0,74 \| 799 |
| 6 | + setor IBGE | 0,68 \| 753 | 0,73 \| 754 | 0,74 \| 788 |
| 7 | Imputadas + vizinhos + setor | **0,70** \| 735 | 0,73 \| 759 | 0,74 \| 783 |
| 8 | + Censo 2022 (conjunto completo, parametros padrao) | 0,69 \| 735 | 0,73 \| 754 | 0,74 \| 781 |
| 9 | **Conjunto completo + parametros ajustados** | 0,68 \| 738 | **0,74** \| 728 | **0,76** \| 741 |
| - | Random Forest (baseline original) com as mesmas variaveis e divisoes | 0,66 \| 774 | 0,72 \| 768 | 0,74 \| 785 |
| 10 | Etapa 8 + **terreno e texto do anuncio** (parametros padrao) | 0,69 \| 739 | 0,77 \| 687 | 0,77 \| 740 |
| 11 | LightGBM ajustado (Optuna, 40 tentativas) | 0,70 \| 713 | 0,79 \| 650 | **0,80** \| 676 |
| 12 | Conjunto (media de HGB + LightGBM + CatBoost ajustados) | 0,709 \| 711 | 0,791 \| 649 | 0,797 \| 680 |
| 13 | Etapa 12 + **valor do condominio e contexto** (area relativa ao bairro, no de anuncios na rua e no bairro, distancia ao centro), busca refeita | **0,730** \| 684 | **0,800** \| 638 | **0,807** \| 665 |

Ganho acumulado do baseline simples (etapa 0) ao conjunto final (etapa 13): apartamento 0,37 -> 0,73; casa 0,37 -> 0,80; residencial 0,33 -> 0,81.
MAE de 1.085 -> 684 (apt), 1.208 -> 638 (casa), 1.339 -> 665 (residencial). MAPE do conjunto: 11,1% / 15,0% / 14,0%.

Observacoes das etapas 10 a 13 (`docs/MODELOS_AVANCADOS.md`):

- **Informacao nova rendeu mais que ajuste**: terreno e texto deram +0,044 de R2 nas casas; o ajuste Bayesiano deu +0,014 a +0,021;
  o Censo, +0,00. Antes de tunar mais, vale buscar variaveis (qualidade, andar, idade do predio) que o VivaReal nao traz.
- **CatBoost ajustado nao melhorou** (apt 0,690 -> 0,683) com apenas 8 tentativas; o LightGBM ajustado foi o melhor modelo unico.
- **O conjunto so ganha de forma clara em apartamento** (+0,005 sobre o LightGBM na etapa 13); em casa e residencial o LightGBM sozinho empata (0,803 e 0,809).
- **Etapa 13 (2026-10-05):** a informacao que nao usa preco (taxa de condominio e contexto do anuncio) deu +0,021 em apartamento e +0,009 a +0,010
  nas casas e no residencial. Testados e **descartados**: IPTU, alvo em log, vizinhos em varias escalas, preco da rua (mais variaveis de
  vizinhanca com preco pioram o teste). Aluguel/yield nas series temporais tambem piorou o ARIMA (`docs/MODELOS_TEMPORAIS.md`).
- Etapa 10 dos apartamentos: R2 praticamente igual (0,693) porque terreno nao se aplica e o texto pouco agrega no teste temporal.

Observacoes:

- **O ganho mais importante nao veio de dados novos, e sim de trocar o modelo linear por arvores** (etapa 3: +0,14 em
  apartamento e casa), que capturam interacoes (ex.: area x bairro).
- **A geografia ajuda sobretudo em apartamentos** (etapas 2, 4 e 7). Em casas o bairro e `em_condominio` ja capturam
  a localizacao.
- **A imputacao de coordenadas e o Censo agregam pouco** (+0,00 a +0,03): a informacao geografica esta saturando perto
  de R2 0,69-0,76. O erro percentual medio (MAPE) do melhor modelo e de ~12% (apartamento) e ~16-17% (casa e residencial).
- **O ajuste de parametros** ajuda em casas e no residencial (+0,014 e +0,018 de R2 temporal; MAE de 754 para 728 e de
  781 para 741), mas **nao em apartamentos** (0,691 -> 0,682, dentro do ruido; no holdout aleatorio ha pequeno ganho:
  0,683 -> 0,695). Busca aleatoria de 20 combinacoes com validacao cruzada de 3 particoes **so no treino**. Os parametros
  escolhidos coincidiram nas tres divisoes (taxa de aprendizado ~0,023, 63 folhas maximas, minimo de 20 anuncios por folha,
  sem L2, 50% das variaveis por divisao), porque a busca usou a mesma semente: uma busca maior pode achar mais.
- O **R2 de 0,78 do Random Forest antigo nao e comparavel** (limpeza diferente, sem remocao de duplicatas); refeito nas
  mesmas condicoes, o Random Forest fica abaixo do gradient boosting nos tres segmentos.
- A linha "gradient boosting sem coordenadas" mudou de 0,63 para 0,62 em apartamento entre duas execucoes porque as categorias
  raras passaram a ser agrupadas; as comparacoes dentro de cada tabela usam a mesma versao.

## 4. O que mais importa para o preco (importancia por permutacao, gradient boosting ajustado, teste temporal)

Aumento do erro medio (R$/m2) ao embaralhar cada variavel:

| Posicao | Apartamento | Casa | Residencial |
|---|---|---|---|
| 1 | area (log): 293 | area (log): 768 | area (log): 838 |
| 2 | latitude (vizinhos): 153 | bairro: 289 | bairro: 261 |
| 3 | longitude (vizinhos): 140 | casa em condominio: 145 | tipo do imovel: 201 |
| 4 | suites: 136 | setor IBGE: 86 | setor IBGE: 130 |
| 5 | latitude: 116 | suites: 81 | suites: 82 |

Localizacao (coordenadas, vizinhos, bairro, setor) domina nos apartamentos; area e bairro nas casas. **A renda media do setor
(Censo) fica entre a 10a e a 14a posicao** (6 a 29 R$/m2): util, mas redundante com a localizacao.

## 5. Como usar o Censo 2022 (renda, densidade e domicilios)

Variaveis agregadas por setor, disponiveis para Jacarei (544 setores): pessoas, domicilios, media de moradores,
domicilios vagos e de uso ocasional, e renda do responsavel (media e mediana). Ja em uso: renda, densidade
(habitantes e domicilios por km2), moradores por domicilio e % de domicilios vagos.

- **Renda media do setor:** correlaciona 0,54 com o R$/m2 das casas e 0,33 dos apartamentos; e um indicador de poder aquisitivo
  do entorno. Interpretavel (a variavel "setor" so memoriza o codigo).
- **Densidade:** correlaciona -0,37 com o R$/m2 das casas (areas mais adensadas, mais baratas).
- **% de domicilios vagos:** proxy de liquidez e de mercado de investimento; efeito fraco.
- **Proximos usos possiveis:** arquivos adicionais do mesmo Censo por setor (caracteristicas dos domicilios, como tipo e posse; e
  entorno urbanistico, como pavimentacao e arborizacao); suavizar a renda entre setores vizinhos; comparar areas no mapa
  (`reports/figures/mapa_setores_interativo.html`).
- **Limite:** o Censo e de 2022 e o snapshot e de 2026; os setores mudam devagar, mas a renda esta em valores nominais de 2022.

## 6. Series temporais (FipeZAP): resumo

- Alvo em log; `d = 2` nos nominais; ARIMA(0,2,3) (a media movel trimestral do indice aparece como MA(3)).
- MAPE do ARIMA nacional: 0,07% (1 mes) a 1,18% (12 meses), contra 0,30% a 3,24% do ingenuo.
- **Tecnicas testadas sem ganho significativo no nacional:** suavizacao exponencial, tendencia local, combinacao com tendencia,
  ARIMAX (credito, juros, confianca, IBC-Br) e cidades vizinhas defasadas. Em Sao Jose dos Campos a combinacao com tendencia
  reduz o erro aos 12 meses (MAPE 5,5% -> 3,8%), mas sem significancia estatistica.
- Detalhes: `docs/MODELOS_TEMPORAIS.md`.

### LSTM e painel de 50 cidades (2026-10-02)

Pergunta: como o VivaReal nao tem serie temporal e o FipeZAP nao tem Jacarei, o painel com as 50 cidades ajuda o LSTM? E dar mais
peso as cidades parecidas ajuda? Tecnicas: modelar **crescimento padronizado** (elimina diferenca de nivel entre cidades), painel
com todas as cidades, so com as 10 mais parecidas e ponderado pela correlacao com o alvo (calculada so com dados ate a origem), contra
um LSTM de controle so com a serie do alvo, mais gradient boosting global. Avaliacao: walk-forward, MAPE e RMSE relativo ao ARIMA.

| Alvo | ARIMA (MAPE 1 / 12 meses) | Melhor rede ou GB (12 meses) | Veredito |
|---|---|---|---|
| Nacional | 0,07% / 1,18% | GB global 1,69%; LSTM painel 1,71% | **ARIMA ganha** (diferenca significativa em 1 e 3 meses) |
| SJC | 0,32% / 5,46% | LSTM controle 2,13%; GB global 2,50% | **Redes menores nos 6 e 12 meses, mas sem significancia** (p 0,06 a 0,16; 44 origens) |

- O painel ajuda o LSTM no nacional (mais dados), nao em SJC (o controle foi o melhor).
- **A semelhanca entre cidades nao trouxe ganho consistente** (top 10 e ponderado ~ painel simples). As cidades mais parecidas
  com SJC nao sao as vizinhas (Praia Grande, Vila Velha, Blumenau...).
- Detalhes e ressalvas: `docs/MODELOS_LSTM.md`.

## 7. Projecao de preco de Jacarei (2026-10-02; refeita em 2026-10-05 com o modelo da etapa 13)

Combina o valor estimado de cada anuncio (conjunto LightGBM + HGB, previsao fora da amostra) com a tendencia do FipeZAP de SJC.
Detalhes e premissas em `docs/PROJECAO_JACAREI.md`.

| Segmento | Estimado hoje (R$/m2, mediana) | Em 12 meses (ARIMA SJC) | Erro relativo mediano | Intervalo 80% do imovel |
|---|---|---|---|---|
| Apartamento | 6.458 | 6.989 (+8,2%) | 8,1% | +-17% |
| Casa | 4.597 | 4.974 (+8,2%) | 10,4% | +-23% |

Cenarios em 12 meses: ARIMA SJC +8,2% (IC95 -4,5% a +22,6%); tendencia de 12 meses de SJC +9,8%; ARIMA nacional +6,2% (+0,3% a +12,4%).
Do snapshot (mar/2026) ate o ultimo indice (ago/2026) o indice de SJC subiu 4,4% (nacional 2,4%).

## 8. Tempo de execucao e custo computacional

Maquina local, so CPU (sem GPU). Os tempos orientam a reproducao e justificam as escolhas de projeto.

| Comando | Tempo | O que consome o tempo | Decisao tomada |
|---|---|---|---|
| `vivareal-prep` | curto (nao medido) | leitura do banco e limpeza; o texto acrescenta a vetorizacao | - |
| `arima` | ~45 s | walk-forward (reajuste a cada mes) | - |
| `arima-plus` | ~2 min | ARIMAX e cidades vizinhas | - |
| `reg-geo` | minutos (nao medido) | kNN espacial e gradient boosting por segmento | - |
| `ajuste-gb` | ~7 min | busca aleatoria de 20 combinacoes x 3 particoes x 3 segmentos | busca pequena de proposito |
| `lstm` | 6,8 min | 3 sementes x reajuste anual x 50 cidades (PyTorch, CPU) | rede de 1 camada com 32 unidades; reajuste anual (nao mensal) |
| `modelos-avancados` | **65,5 min** (70,2 min na rodada final) | Optuna: 40 tentativas HGB + 40 LightGBM + 8 CatBoost, cada uma com 3 particoes, em 3 segmentos | CatBoost reduzido (era o mais lento); busca so no treino |
| `verificar` | segundos | so le o disco: ambiente, dados de entrada, resultados e comandos disponiveis | - |
| `relatorio` | segundos | le resultados e monta Markdown/HTML (numeros calculados, texto conferido) | nada recalculado |
| `painel` | segundos | so le resultados salvos e monta o HTML (plotly.js embutido) | tudo em um arquivo, sem servidor |
| `sensibilidade` | ~2,5 min | refit do conjunto + 5 permutacoes por grupo + cenarios | - |
| `prever` | ~40 s | treino do conjunto em todo o segmento | - |
| `projecao` | ~4 min | 5 particoes x 2 modelos x 2 segmentos | parametros lidos do relatorio anterior para nao refazer a busca |

Maior gargalo: a busca de parametros. Se for preciso repetir, reduzir as tentativas do Optuna ou rodar so um segmento.

## 9. Problemas encontrados e como foram contornados

| Problema | Como apareceu | Solucao |
|---|---|---|
| Correlacao cruzada espuria (credito x FipeZAP, 0,85) | series nao estacionarias | Refeita com series estacionarias e comparacao bruta x estacionaria |
| Vazamento temporal nos paineis antigos | defasagem so nas series trimestrais; ffill de 27 meses; base do preco real usava o fim da amostra | Paineis **as-of** com defasagens confirmadas em fontes + teste automatico de vazamento (perturbacao do futuro) |
| Colinearidade `tipo` x `em_condominio` (erro-padrao 47) | casas | Cada informacao entra uma unica vez |
| Duplicatas entre treino e teste | `external_id` repetido | Deduplicacao antes da divisao |
| Valores absurdos de condominio e IPTU | maximo de R$ 2,5 mi | Viram ausentes + indicador de informado |
| Texto com preco (vazamento do alvo) | preco em 19% dos titulos | Remocao de "R$" e de todos os digitos; vocabulario com minimo de 150 documentos |
| Vocabulario vazio no texto | `\b` do regex virou caractere de controle (`\x08`) ao gerar o codigo | Corrigido o padrao do token; teste com contagem de colunas `txt_*` |
| `total_area_m2` ausente do dataset | nao estava em `OUTPUT_COLUMNS` | Incluida na limpeza e regenerados os 3 CSVs |
| Idade do anuncio "ajuda" no holdout, piora no temporal | colinear com a divisao | Descartada |
| CatBoost muito lento | milhares de arvores x validacao cruzada | Profundidade e iteracoes limitadas; 8 tentativas |
| Parametros do Optuna nao salvos em JSON na execucao longa | patch aplicado depois da corrida | `projecao.py` le o JSON se existir e, senao, extrai do `modelos_avancados.md` por expressao regular; proximas execucoes ja gravam o JSON |
| Shapefile do IBGE (centenas de MB) quase entrou no git | pasta em `data/raw/` | `.gitignore` bloqueia `*.shp`, `*.dbf`, `*.shx`, `data/raw/SP_setores_CD2022/` e os originais do Censo; so o CSV de Jacarei (39 KB) e versionado |
| Banco do orientador tem telefone, nome e CRECI de anunciantes | repositorio publico | `*.db` e `*.pkl` ignorados; nunca versionar |
| Mapa de SP inteiro em vez de Jacarei | pedido do usuario | Recorte por juncao espacial: so os 544 setores de Jacarei |
| Corrida longa interrompida (computador suspendeu, 5 h sem processo) | `modelos-avancados` perdeu o relatorio (so grava no fim) | Reiniciada com a suspensao do computador bloqueada durante a sessao; as sementes fixas reproduziram os mesmos numeros |
| Tarefa em segundo plano que nunca terminava | laço de espera procurava "concluido", mas a projecao termina com "relatorio em" | Tarefa encerrada; em proximas esperas usar a mensagem final real do comando |

## 10. Ressalvas para o relatorio

- Os dados sao **precos pedidos** em anuncios (nao de venda); a coleta e de um unico dia.
- So ~48% dos anuncios tem coordenada real; a imputacao usa a posicao do bairro ou da rua.
- Anuncios do mesmo predio ou loteamento sao parecidos; a divisao temporal reduz, mas nao elimina, o efeito.
- A busca de parametros do modelo final e maior (Optuna), mas o CatBoost teve so 8 tentativas.
- IPTU fora dos modelos ate confirmar a unidade; coordenadas e Censo tem resolucao de setor.
- A projecao supoe que Jacarei acompanha SJC e que todos os imoveis variam igual (`docs/PROJECAO_JACAREI.md`).
- Os resultados temporais de SJC tem so 44 origens de teste: indicativos, nao conclusivos.

## 11. Pendencias

1. (feito, 2026-10-05) Comando `prever`: treina o conjunto LightGBM + HGB em todo o segmento, avalia um imovel novo e devolve
   valor, intervalos conformais (do teste temporal) e projecao de SJC. Detalhes em `docs/PROJECAO_JACAREI.md`.
2. Variaveis de qualidade e conservacao do imovel (apartamentos estao em R2 ~0,70); mais arquivos do Censo (domicilios e entorno).
3. Ideias de series nao testadas: razao preco/aluguel (yield do FipeZAP), expectativas do Focus, concessoes de credito, Google Trends;
   ajuste de hiperparametros e conjuntos do LSTM.
4. Snapshots periodicos do VivaReal, para medir crescimento de preco por area e criar uma serie propria de Jacarei.
5. Confirmar com o orientador: unidade do IPTU; se FipeZAP (sem Jacarei) atende a proposta.
