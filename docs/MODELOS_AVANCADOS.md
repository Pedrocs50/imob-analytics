# Modelos avancados de precificacao: novas informacoes, ajuste bayesiano, conjunto e intervalos

Data: 2026-10-02. Numeros completos em `reports/results/modelos_avancados.md` (CSVs em `reports/results/eda/modelos_avancados_*.csv`;
figura `reports/figures/modelos_avancados_real_previsto.png`). Complementa `docs/DIARIO_MODELAGEM.md`.

```bash
python main.py modelos-avancados    # ~66 minutos, quase todo na busca de parametros (CPU)
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

## Resultados finais (divisao temporal, teste nos 25% mais recentes)

| Segmento | Melhor modelo unico | R2 | MAE (R$/m2) | **Conjunto**: R2 | MAE | MAPE |
|---|---|---|---|---|---|---|
| Apartamento | LightGBM ajustado | 0,702 | 713 | **0,709** | 711 | 11,5% |
| Casa | LightGBM ajustado | 0,789 | 650 | **0,791** | 649 | 15,1% |
| Residencial | LightGBM ajustado | 0,799 | 676 | **0,797** | 680 | 14,3% |

Modelos com parametros padrao, para referencia: apartamento 0,685 a 0,692; casa 0,767 a 0,772; residencial 0,772 a 0,773.

No residencial o LightGBM sozinho (0,799) e ligeiramente melhor que o conjunto (0,797): a diferenca esta dentro do ruido.

Intervalos de previsao (R$/m2, teste temporal):

| Segmento | Nominal | Cobertura observada | Erro relativo do intervalo |
|---|---|---|---|
| Apartamento | 80% / 90% | 82,7% / 91,1% | +-18,8% / +-24,8% |
| Casa | 80% / 90% | 81,1% / 90,6% | +-23,8% / +-32,7% |
| Residencial | 80% / 90% | 82,1% / 91,1% | +-23,1% / +-31,4% |

A cobertura observada fica 1 a 3 pontos acima da nominal: os intervalos sao bem calibrados e levemente conservadores.

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
