# LSTM com indicadores macroeconomicos (metas 5 e 6)

Data: 2026-10-26. Numeros completos em `reports/results/lstm_macro.md` (tabelas em `reports/results/lstm_macro/`;
figura `reports/figures/lstm_macro_comparacao.png`). Relatorio e painel: secao 5.1 e aba "Series temporais".

```bash
python main.py lstm-macro            # ~20 min (PyTorch, CPU; 2 alvos x 18 modelos x 5 sementes)
python main.py lstm-macro --teste    # ~1 min, 1 semente e poucas origens: so verifica se roda; nao usar os numeros
```

Implementacao: `src/timeseries/lstm_macro.py` (reaproveita a rede e o walk-forward de `lstm_painel.py`).

## Pergunta

O resumo do trabalho propoe um LSTM que relacione o historico de precos ao cenario macroeconomico. **Incluir indicadores do BCB e do IPEA
melhora o LSTM?** Resposta deste experimento: **nao**.

## Desenho

- **Alvos e painel:** os mesmos de `docs/MODELOS_LSTM.md` (SJC como proxy de Jacarei e indice nacional; painel de 50 cidades; entrada de 12 meses, saida direta de 12).
- **Macro:** 8 indicadores (Selic meta, IPCA, INCC, PTAX, IBC-Br, saldo de credito imobiliario, ICC e Selic real), do painel *as-of* (cada mes so contem o que ja estava publicado).
  Transformados para estacionarios e **padronizados so com o treino de cada reajuste**. O macro e comum a todas as cidades: cada janela de cada cidade usa o macro das mesmas datas.
- **Variantes:** 4 conjuntos de macro (nenhum; completo; "juros e confianca"; "credito + juros + confianca + IBC-Br" — os dois ultimos definidos antes, no ARIMAX de `arima_plus.py`) x 3 arquiteturas
  (pequena 16 unidades/dropout 0,3; base 32/0,1; grande 64/0,2) = 12 redes, media de 5 sementes.
- **Comparadores:** ARIMA(0,2,3), tendencia de 12 meses e regressao linear (Ridge) direta por horizonte, com e sem macro (e com cada subconjunto).
- **Selecao x confirmacao:** as primeiras 60% das origens **escolhem** a variante; as 40% finais **confirmam**. Nota = RMSE relativo ao ARIMA, media dos horizontes de 1, 3, 6 e 12 meses.
  Sem isso, escolher a melhor variante olhando o proprio teste daria um numero otimista.
- **Metricas:** MAE, RMSE e MAPE (e Diebold-Mariano) — as do resumo.

## Resultados (RMSE relativo ao ARIMA; menor e melhor)

| | SJC selecao | SJC confirmacao | Nacional selecao | Nacional confirmacao |
|---|---|---|---|---|
| ARIMA(0,2,3) | 1,00 | 1,00 | 1,00 | 1,00 |
| LSTM sem macro, pequena | 0,84 | **0,97** | 1,89 | 1,18 |
| LSTM sem macro, base | 0,84 | 1,05 | 1,74 | **1,01** |
| LSTM credito + juros + confianca + IBC-Br, base (escolhida na selecao em SJC) | **0,83** | 1,34 | 1,55 | 1,81 |
| LSTM macro completo, base | 1,08 | 2,23 | 1,52 | 2,75 |
| Regressao linear (so o alvo) | 1,01 | 0,50 | 1,21 | 1,08 |

1. **O macro nao ajudou.** Na confirmacao, a melhor rede com macro tem RMSE relativo de 1,14 (SJC) e 1,69 (nacional); a melhor sem macro, 0,97 e 1,01.
2. **A variante vencedora na selecao nao se manteve.** Em SJC passou de 0,83 para 1,34; no nacional, de 1,16 para 2,18. Escolher pelo teste teria enganado.
3. **Sem macro, a rede pequena foi a mais estavel** (0,84 -> 0,97 em SJC), quase empatada com o ARIMA na confirmacao.
4. **No indice nacional o ARIMA continua melhor** que todas as redes.
5. **A regressao so com o alvo** foi a melhor em SJC na confirmacao (0,50) mas ruim na selecao (1,01): instavel, com poucas origens.

## Leitura e limites

- Uma explicacao plausivel, **nao testada aqui**: poucas observacoes mensais (SJC tem 104 meses) e indicadores lentos; a rede com macro tem mais parametros que o sinal sustenta.
- SJC tem 44 origens (cerca de 18 na confirmacao): as diferencas pequenas nao sao significativas.
- O experimento e um resultado valido para a meta 6: o ganho esperado pelo resumo (previsao melhor com macro) **nao apareceu** nestes dados.
- Possiveis proximos testes: macro defasado em mais meses, frequencia trimestral, serie propria de Jacarei (quando houver recoletas periodicas) e regularizacao especifica do macro.
- As caracteristicas dos imoveis entram pelo modelo de precificacao (`docs/MODELOS_AVANCADOS.md`), combinado com a tendencia desta trilha em `docs/PROJECAO_JACAREI.md`; o VivaReal e uma fotografia, sem historico para alimentar o LSTM.
