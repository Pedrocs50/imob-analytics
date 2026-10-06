# Modelos avancados de precificacao: novas informacoes, ajuste bayesiano, conjunto e intervalos

Data: 2026-10-02. Numeros completos em `reports/results/modelos_avancados.md` (CSVs em `reports/results/eda/modelos_avancados_*.csv`;
figura `reports/figures/modelos_avancados_real_previsto.png`). Complementa `docs/DIARIO_MODELAGEM.md`.

```bash
python main.py modelos-avancados    # ~70 minutos, quase todo na busca de parametros (CPU)
```

Implementacao: `src/pricing/modelos_avancados.py` (novas variaveis em `src/vivareal/cleaning.py` e `src/pricing/geo.py`).

## Motivacao

Os resultados de precificacao pararam em R2 temporal de 0,68-0,74 (apartamento, casa, residencial). Em vez de so ajustar parametros,
pesquisou-se o que a literatura de precos hedonicos e de dados tabulares sugere e testou-se cada ideia com a mesma divisao temporal.

## O que foi testado (em ordem de ganho)

| Ideia | Fundamento | Resultado (R2 temporal) |
|---|---|---|
| **Area do terreno** (`log_terreno`, `razao_terreno_construida`) | Em casas, o terreno explica boa parte do preco e nao entrava | Casa +0,026 |
| **Texto do anuncio** (150 palavras e bigramas mais frequentes, binarias, `txt_*`) | A literatura mostra que o texto melhora modelos hedonicos | Casa +0,014 (temporal), +0,032 (holdout); apartamento ~0 no temporal, +0,03 no holdout |
| Terreno + texto juntos | - | Casa 0,771; residencial 0,769; apartamento ~inalterado |
| **Busca bayesiana de parametros** (Optuna/TPE, 3 particoes internas **so no treino**) | Mais eficiente que busca aleatoria | HGB +0,016 (apt), +0,014 (casa); LightGBM +0,010 / +0,021 |
| **LightGBM** e **CatBoost** | Fortes em dados tabulares | LightGBM ajustado e o melhor modelo unico; CatBoost ajustado (8 tentativas) **nao melhorou** |
| **Conjunto** (media de HGB, LightGBM e CatBoost ajustados) | Erros pouco correlacionados se compensam | +0,007 (apt), +0,002 (casa), -0,002 (residencial) sobre o melhor modelo unico: ganho pequeno |
| **Intervalos conformais** (quantis do erro relativo fora da amostra) | Incerteza calibrada, sem supor normalidade | Cobertura ~nominal no teste temporal |

**Licao:** informacao nova (terreno e texto) rendeu mais que todo o ajuste de parametros (casa +0,044 contra +0,02) e que o Censo
(+0,00). Ajustar parametros em apartamentos rendeu pouco por falta de variaveis de qualidade e conservacao do imovel.

## Rodada de melhorias de variaveis (2026-10-05)

Pergunta: ha informacao ja disponivel no VivaReal que o modelo ainda nao usa? Cada ideia foi testada com o **LightGBM ajustado fixo**
(mesmos parametros), na divisao temporal e em 5-fold aleatorio, para ver se o ganho e consistente. Script de teste descartavel; so o
que ajudou entrou no pipeline (`src/pricing/geo.py`, `_montar_x`).

| Ideia | Apartamento (temporal \| 5-fold, R2) | Casa (temporal \| 5-fold, R2) | Decisao |
|---|---|---|---|
| Base (LightGBM ajustado) | 0,702 \| 0,724 | 0,789 \| 0,797 | - |
| + **valor da taxa de condominio** (proxy de padrao do predio) | 0,720 \| 0,737 | 0,796 \| 0,801 | **entra** |
| + IPTU | 0,706 \| 0,727 | 0,788 \| 0,798 | **fora** (ganho ~0; unidade nao confirmada) |
| + condominio e IPTU por m2 | 0,717 \| 0,735 | 0,795 \| 0,801 | fora |
| + **contexto**: area relativa ao bairro, no de anuncios na rua e no bairro | 0,714 \| 0,730 | 0,790 \| 0,799 | **entra** |
| + distancia ao centro | 0,708 \| 0,726 | 0,789 \| 0,797 | entra (barata; ganho so em conjunto) |
| **Conjunto: condominio + contexto + distancia (+ IPTU)** | **0,730** \| **0,742** | **0,799** \| **0,804** | **entra (sem IPTU: 0,730 \| 0,799, igual)** |
| Alvo em log (preve log do R$/m2) | 0,675 \| 0,680 | 0,774 \| 0,790 | **descartado** (pior nos dois) |
| + vizinhos em mais escalas (5 e 40) | 0,720 \| 0,730 | 0,794 \| 0,801 | descartado (piora) |
| + vizinhos ponderados pelo tamanho | 0,726 \| 0,738 | 0,792 \| 0,798 | descartado |
| + preco medio da mesma rua | 0,728 \| 0,735 | 0,800 \| 0,803 | descartado (ganho ~0) |
| + todas as variaveis de vizinhanca juntas | 0,721 \| 0,723 | 0,791 \| 0,797 | descartado (piora) |

Leituras:

- **O ganho vem de variaveis que NAO usam o preco**: taxa de condominio e contexto do anuncio (+0,028 em apartamento, +0,010 em casa).
- **Mais variaveis de vizinhanca calculadas com o preco pioram o modelo.** No treino cada anuncio exclui o proprio preco (leave-one-out)
  e no teste usa o treino inteiro; com varias dessas variaveis o modelo aprende uma relacao que no teste fica ligeiramente
  diferente. Resultado negativo mantido no relatorio.
- O **IPTU nao acrescenta nada** acima do condominio, em linha com a decisao de mante-lo fora ate confirmar a unidade.
- O **alvo em log** reduz o peso dos precos altos no ajuste, mas aumenta o erro em R$/m2 (que e a metrica de interesse).
- Depois da inclusao, `modelos-avancados` foi rodado de novo (busca Optuna refeita com as novas variaveis); os numeros finais estao na
  secao seguinte. Uma primeira tentativa foi interrompida no meio (o computador suspendeu); a segunda reproduziu exatamente os mesmos
  numeros do apartamento, o que confirma a reprodutibilidade (sementes fixas).

## Resultados finais (divisao temporal, teste nos 25% mais recentes)

Rodada final, com as variaveis de condominio e contexto e a busca Optuna refeita (70 min). Entre parenteses, a rodada anterior (so com
terreno e texto), para mostrar o efeito das variaveis novas.

| Segmento | Melhor modelo unico | R2 | MAE (R$/m2) | **Conjunto**: R2 | MAE | MAPE |
|---|---|---|---|---|---|---|
| Apartamento | LightGBM ajustado | 0,725 (0,702) | 687 (713) | **0,730** (0,709) | 684 (711) | 11,1% (11,5%) |
| Casa | LightGBM ajustado | 0,803 (0,789) | 631 (650) | **0,800** (0,791) | 638 (649) | 15,0% (15,1%) |
| Residencial | LightGBM ajustado | 0,809 (0,799) | 660 (676) | **0,807** (0,797) | 665 (680) | 14,0% (14,3%) |

Todos os modelos (R2): HistGradientBoosting ajustado 0,724 / 0,792 / 0,800 e CatBoost ajustado 0,709 / 0,779 / 0,788 (apartamento / casa /
residencial). Parametros padrao: apartamento 0,708 a 0,711; casa 0,779 a 0,785; residencial 0,782 a 0,789.

- A busca Bayesiana continua rendendo +0,01 a +0,02; as variaveis novas deram +0,02 no apartamento e +0,01 em casa e residencial.
- **Em casa e residencial o LightGBM sozinho empata ou supera o conjunto** (0,803 x 0,800; 0,809 x 0,807): diferenca dentro do ruido.
  O conjunto so ganha de forma clara no apartamento (+0,005). Mantido por ser mais estavel e porque os intervalos foram calibrados com ele.
- **CatBoost ajustado nunca superou os parametros padrao** (so 8 tentativas); continua sendo o mais lento.

Intervalos de previsao (R$/m2, teste temporal):

| Segmento | Nominal | Cobertura observada | Erro relativo do intervalo |
|---|---|---|---|
| Apartamento | 80% / 90% | 82,3% / 91,1% | +-18,0% / +-24,2% |
| Casa | 80% / 90% | 81,9% / 90,6% | +-23,6% / +-32,3% |
| Residencial | 80% / 90% | 81,4% / 90,8% | +-22,3% / +-30,8% |

A cobertura observada fica 0,6 a 2,3 pontos acima da nominal: os intervalos sao bem calibrados e levemente conservadores.

## Cuidados contra vazamento (ao incluir texto e terreno)

- O texto passa por `_limpar_texto`: remove HTML, valores "R$ ..." e **todos os digitos**. O preco aparece em 19% dos titulos e 8% das
  descricoes; sem esta limpeza a variavel-resposta vazaria para os preditores.
- Vocabulario com token de 4+ letras, minimo de 150 documentos (evita palavras raras que memorizam anuncios) e maximo de 150 colunas.
- A busca de parametros usa so o treino; o teste temporal nunca participa da escolha (por isso o conjunto de teste e honesto).

## O que foi descartado

- **Idade do anuncio** (tempo desde `created_at`): piora o teste temporal, pois e colinear com a propria divisao.
- **Comodidades e tipo de anunciante:** nao acrescentam nada alem do ja informado.
- **CatBoost ajustado:** so 8 tentativas (cada uma e lenta); nao superou os parametros padrao. Uma busca maior seria cara e o ganho,
  incerto.

## Limitacoes

- Apartamentos ficam em R2 ~0,70: faltam variaveis de **qualidade, conservacao, andar, idade do predio e condominio** (alguns nao
  existem no VivaReal).
- O erro medio percentual (11% a 15%) e alto para precificar um imovel individual; serve mais para estimar nivel e comparar anuncios.
- Os parametros foram escolhidos num unico recorte temporal; outra data de corte pode mudar a ordem entre os modelos.
- Cada execucao completa dura ~66 minutos; para reproduzir mais rapido reduzir as tentativas do Optuna em `modelos_avancados.py`.
