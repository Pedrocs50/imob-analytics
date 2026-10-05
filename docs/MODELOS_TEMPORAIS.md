# Modelos temporais: ARIMA do FipeZAP (meta 4, parte 2)

Data: 2026-10-02. Numeros completos em `reports/results/arima.md` (tabelas em CSV em
`reports/results/arima/`; figuras `reports/figures/arima_*.png`).

```bash
python main.py arima     # ~45 segundos
```

Implementacao: `src/timeseries/arima.py`. O treino e rapido: sao ~180 reajustes
mensais de modelos pequenos (o LSTM, mais adiante, sera bem mais lento).

## Metodo

- **Alvos (em log):** FipeZAP nacional nominal (224 meses, principal), Sao Jose dos
  Campos nominal (104 meses, secundario) e FipeZAP nacional **real** (alternativa,
  deflacionado pelo IPCA).
- **Diferenciacao** (da analise exploratoria): `d = 2` nos nominais, sem constante;
  `d = 0` com constante no preco real.
- **Ordem `(p, q)`:** grade de 0 a 3 por AIC, escolhida **so na janela inicial de
  treino** (84 meses no nacional, 60 em SJC). Sem usar o futuro.
- **Walk-forward:** janela expansiva; em cada mes de origem o modelo e reajustado com
  o passado (ordem fixa) e preve 1, 3, 6 e 12 meses a frente da ultima observacao.
  140 origens no nacional, 44 em SJC. O FipeZAP do mes `t` so e publicado em `t+1`, entao
  o primeiro mes que se consegue prever a partir do fim de `t` e `t+2`.
- **Benchmarks:** ingenuo (repete o ultimo valor), tendencia com o crescimento medio
  dos ultimos 12 meses e tendencia com o ultimo crescimento mensal.
- **Teste de Diebold-Mariano** (erro quadratico, variancia de Newey-West, correcao de
  Harvey) do ARIMA contra cada benchmark.

## Resultado

**Ordens escolhidas:** `ARIMA(0,2,3)` para o nacional e SJC nominais; `ARIMA(2,0,2)`
com constante para o preco real. Nos nominais so o termo `MA(3)` e significativo
(-0,26 no nacional, -0,46 em SJC): e a assinatura da **media movel trimestral** do
indice, nao uma dinamica economica.

**Erro percentual medio (MAPE) por horizonte:**

| Alvo | Modelo | 1 mes | 3 meses | 6 meses | 12 meses |
|---|---|---|---|---|---|
| Nacional nominal | **ARIMA(0,2,3)** | 0,07% | 0,24% | 0,53% | 1,18% |
| | Ingenuo | 0,30% | 0,87% | 1,69% | 3,24% |
| | Tendencia (12 meses) | 0,11% | 0,32% | 0,67% | 1,47% |
| | Tendencia (ultimo crescimento) | 0,07% | 0,25% | 0,57% | 1,23% |
| SJC nominal | **ARIMA(0,2,3)** | 0,32% | 1,19% | 2,78% | 5,46% |
| | Ingenuo | 0,83% | 2,41% | 4,58% | 8,86% |
| | Tendencia (12 meses) | 0,46% | 1,26% | 2,19% | 3,45% |
| | Tendencia (ultimo crescimento) | 0,34% | 1,31% | 3,16% | 6,76% |
| Nacional real | **ARIMA(2,0,2)** | 0,28% | 0,81% | 1,51% | 2,14% |
| | Ingenuo | 0,39% | 1,05% | 1,85% | 3,20% |
| | Tendencia (12 meses) | 0,30% | 0,78% | 1,34% | 2,44% |

(RMSE, MAE e R2 da variacao acumulada completos em `reports/results/arima.md`. Para o
nacional nominal, o RMSE vai de R$ 7/m2 em 1 mes a R$ 118/m2 em 12 meses e o R2 da
variacao acumulada vai de 0,87 a 0,71.)

## O que isso significa

1. **O ARIMA supera claramente o ingenuo** em todos os alvos e horizontes do
   nominal (Diebold-Mariano p < 0,05).
2. **Mas o ganho sobre uma tendencia simples e pequeno e, em boa parte, nao
   significativo.** No nacional nominal ele vence a tendencia de 12 meses em 1 e 3
   meses (p < 0,01), e fica no limite em 6 meses (p = 0,07); em 12 meses a diferenca
   nao e significativa (p = 0,16). Contra "repetir o ultimo crescimento" nao ha
   diferenca significativa em nenhum horizonte (p de 0,18 a 0,95). Em SJC, a tendencia
   de 12 meses chega a ter erro **menor** que o ARIMA em 6 e 12 meses (diferenca nao
   significativa; so 33 a 44 origens). No preco real, o ARIMA so se separa com
   significancia da tendencia do ultimo crescimento.
3. **O erro de 0,07% em 1 mes parece excelente, mas e mecanico.** O FipeZAP e media
   movel de tres meses, entao o proximo valor ja esta quase determinado pelos dois
   anteriores. Isso nao e prova de capacidade de prever o mercado; a comparacao justa
   e contra os benchmarks de tendencia.
4. **Diagnostico dos residuos:** no nacional nominal nao ha autocorrelacao restante
   (Ljung-Box p = 0,23). Em **SJC (p = 0,004) e no preco real (p = 0,002) sobra
   autocorrelacao**: a ordem escolhida nao captura toda a dinamica nesses dois alvos.
5. **O R2 negativo em SJC** (variacao acumulada, 3 meses ou mais) indica que, em
   horizontes longos, o modelo nao supera a media das variacoes observadas na janela
   curta de teste.

## Previsao (extrapolacao, nao recomendacao)

| Alvo | Ultimo observado | Previsao para 2027-08 | IC 95% |
|---|---|---|---|
| Nacional nominal | R$ 9.954/m2 (2026-08) | R$ 10.569/m2 | 9.984 a 11.187 |
| SJC nominal | R$ 9.615/m2 (2026-08) | R$ 10.405/m2 | 9.184 a 11.789 |

A previsao supoe que o ritmo recente de crescimento continua. O intervalo de SJC
e largo, e nenhum dos modelos conhece mudancas de regime (juros, credito).

## Limitacoes

- A ordem e escolhida uma vez, na janela inicial; nao e reselecionada ao longo do
  tempo.
- O periodo de teste inclui poucos regimes (queda de crescimento em 2015-2019, alta
  recente); os testes de significancia tem poucas origens e se sobrepoem.
- O preco real nao e comparavel diretamente ao nominal: converter exigiria uma
  previsao de IPCA.
- **A meta fala em "previsao de preco e demanda": demanda nao foi modelada**, porque
  nao ha serie de demanda no projeto.

## Melhorias testadas (`python main.py arima-plus`, ~2 minutos)

Mesmo walk-forward, comparando contra o ARIMA(0,2,3). Numeros completos em
`reports/results/arima_plus.md`.

**Combinacao ARIMA + tendencia de 12 meses e ARIMAX** (preditores estacionarios defasados 12 meses):

| Alvo | Modelo | RMSE relativo ao ARIMA (1 / 3 / 6 / 12 meses) | Melhor que o ARIMA? |
|---|---|---|---|
| Nacional | Combinacao | 1,11 / 1,06 / 1,05 / 1,07 | Nao (pior, p = 0,04 a 0,39) |
| Nacional | ARIMAX credito | 0,96 / 0,94 / 0,97 / 1,01 | Nao significativo (p >= 0,22) |
| Nacional | ARIMAX juros e confianca | 0,97 / 0,96 / 1,00 / 1,05 | Nao |
| Nacional | ARIMAX 4 preditores | 0,97 / 0,97 / 1,02 / 1,07 | Nao |
| SJC | Combinacao | 1,07 / 0,92 / 0,81 / 0,70 | Menor erro, mas nao significativo (p = 0,09 em 6 meses, 0,15 em 12) |
| SJC | ARIMAX credito | 1,02 / 1,05 / 1,02 / 0,87 | Nao significativo |
| SJC | ARIMAX 4 preditores | 1,08 / 1,07 / 1,03 / 0,87 | No limite aos 12 meses (p = 0,08) |

1. **No indice nacional o ARIMA esta perto do teto** com estes dados: nenhuma alternativa
   o supera de forma significativa. O ARIMAX de credito reduz o RMSE em 4% a 6% em 1 a 3
   meses, mas a diferenca e estatisticamente nula, em linha com a analise exploratoria (sem
   relacao estavel entre os preditores macro e o preco).
2. **Em SJC, a combinacao e a tendencia simples reduzem bastante o erro em 6 e 12 meses**
   (RMSE ate 30% menor, MAPE de 5,5% para 3,8% aos 12 meses), mas com 33 a 44 origens a
   diferenca nao e significativa. E um indicio, nao uma conclusao.
3. **Intervalos de previsao do ARIMA:** no nacional sao **conservadores demais** (cobertura de
   99% a 100% para um nominal de 95%; largura de ate 14% do preco aos 12 meses). Em SJC
   **cobrem menos que o nominal** (85% a 91% de 1 a 6 meses). A incerteza declarada pelo
   modelo nao e confiavel em nenhum dos dois.
4. **Estabilidade:** o desempenho do ARIMA e parecido antes e depois de 2020 (MAPE aos 12
   meses: 1,23% e 1,14% no nacional).
5. **Cidades vizinhas defasadas:** entre as 49 cidades do Excel (sem Sao Jose dos Campos),
   **nenhuma antecipa de forma significativa** o indice nacional ou SJC no teste de Granger
   depois da correcao por multiplos testes (menor p = 0,0004 no nacional, com limiar de
   0,00017; 0,015 em SJC).

**Conclusao:** com os dados e a escala atuais, o ganho de modelos mais ricos sobre o ARIMA e o
que a literatura indicaria para series curtas e suaves: pequeno ou nulo. Isso e um resultado
valido para a meta 6. O que ainda pode mudar o quadro e **mais dados** (modelo global com
as 50 cidades, base do LSTM) e **informacao nova** (expectativas do Focus, concessoes de
credito, Google Trends), nao um arranjo diferente de ARIMA.

## Proximos passos

1. **LSTM** em painel com as 50 cidades (precisa instalar o PyTorch) e, como comparacao, um
   gradient boosting global; ambos com o mesmo walk-forward e os mesmos benchmarks.
2. Testar expectativas do Focus (BCB), concessoes de credito imobiliario e Google Trends como
   preditores com informacao nova.
3. Reavaliar a ordem de SJC e do preco real (residuos com autocorrelacao) e a calibracao
   dos intervalos.
