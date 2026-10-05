# LSTM e modelos globais em painel (metas 5 e 6)

Data: 2026-10-02. Numeros completos em `reports/results/lstm.md` (tabelas em `reports/results/lstm/`;
figura `reports/figures/lstm_comparacao.png`).

```bash
python main.py lstm     # ~7 minutos (PyTorch, CPU)
```

Implementacao: `src/timeseries/lstm_painel.py`.

## Pergunta

Os dados do VivaReal de Jacarei nao formam serie temporal e o FipeZAP nao tem Jacarei. O LSTM precisa de muitas observacoes
e o indice nacional tem so 224 meses (SJC, 104). **Treinar em painel com as 50 cidades do FipeZAP ajuda?** E, como as cidades
sao muito diferentes (o nivel de preco e o comportamento variam), **dar mais peso as cidades parecidas com o alvo ajuda?**

## Desenho

- **Alvos:** SJC (proxy mais proxima de Jacarei) e indice nacional.
- **Crescimento, nao nivel.** Os modelos preveem o crescimento mensal (em log) padronizado pelo desvio-padrao de cada cidade
  **calculado so no treino**. Assim a diferenca de nivel de preco entre cidades (R$ 4.600 a R$ 15.600/m2) desaparece.
- **Entrada:** ultimos 12 meses; **saida direta:** proximos 12 meses. LSTM de 1 camada (32 unidades), parada antecipada na
  validacao mais recente, media de 3 sementes. Comparador: gradient boosting global (um modelo por horizonte).
- **Semelhanca entre cidades:** correlacao do crescimento de 12 meses da cidade com o do alvo, **usando so dados ate a
  origem** de cada reajuste (sem olhar o futuro).
- **Variantes:** (a) **controle**, so a serie do alvo; (b) painel com todas as cidades; (c) painel so com as 10 mais
  parecidas; (d) painel com todas, ponderadas pela semelhanca; mais o GB global (todas e 10 mais parecidas).
- **Avaliacao:** o mesmo walk-forward do ARIMA (janela expansiva; 1, 3, 6 e 12 meses), contra o ARIMA(0,2,3) e a tendencia
  simples, com Diebold-Mariano. Diferenca: os modelos de rede sao reajustados **a cada 12 meses** (o ARIMA, todo mes).

## Resultados

**SJC (44 origens)** — MAPE em %, e RMSE relativo ao ARIMA entre parenteses:

| Modelo | 1 mes | 3 meses | 6 meses | 12 meses |
|---|---|---|---|---|
| ARIMA(0,2,3) | 0,32 | 1,19 | 2,78 | 5,46 |
| Tendencia (12 meses) | 0,46 | 1,26 | 2,19 | 3,45 |
| LSTM controle (so o alvo) | 0,41 | 1,13 | 1,89 | **2,13** (0,45) |
| LSTM painel, todas as cidades | 0,33 | 1,13 | 2,21 | 3,27 (0,58) |
| LSTM painel, 10 mais parecidas | 0,39 | 1,15 | 2,04 | 2,47 (0,57) |
| LSTM painel ponderado | 0,36 | 1,16 | 2,26 | 3,25 (0,59) |
| GB global, todas as cidades | 0,34 | 1,13 | 1,95 | 2,50 (0,47) |

**Nacional (140 origens)** — MAPE em %:

| Modelo | 1 mes | 3 meses | 6 meses | 12 meses |
|---|---|---|---|---|
| **ARIMA(0,2,3)** | **0,07** | **0,24** | **0,53** | **1,18** |
| Tendencia (12 meses) | 0,11 | 0,32 | 0,67 | 1,47 |
| LSTM controle | 0,18 | 0,56 | 1,16 | 2,27 |
| LSTM painel, todas | 0,13 | 0,39 | 0,81 | 1,76 |
| LSTM painel, 10 mais parecidas | 0,15 | 0,44 | 0,91 | 1,87 |
| LSTM painel ponderado | 0,13 | 0,38 | 0,78 | 1,71 |
| GB global, todas | 0,10 | 0,36 | 0,75 | 1,69 |

## O que os resultados mostram

1. **No indice nacional o ARIMA ganha com folga.** Todas as variantes de LSTM e de GB tem erro maior (RMSE de 1,3 a 2,6 vezes o do
   ARIMA); a diferenca e significativa em 1 e 3 meses (p < 0,01) e fica no limite em 6 e 12 meses (p de 0,02 a 0,14). Em
   series suaves, longas e quase deterministicas, o modelo estatistico simples e dificil de bater.
2. **O painel ajuda o LSTM, mas nao o bastante.** No nacional, o painel reduz o erro do LSTM em relacao ao controle
   (MAPE aos 12 meses de 2,27% para ~1,7%; p < 0,02 ate 6 meses): **mais dados melhoram a rede**, como a hipotese previa.
3. **Em SJC o quadro se inverte.** Aos 6 e 12 meses, todas as redes e o GB global tem erro **bem menor que o ARIMA** (MAPE de
   5,5% para 2,1% a 3,3% aos 12 meses; RMSE de 0,45 a 0,59 do ARIMA). Mas com 44 origens (33 aos 12 meses) a diferenca nao e
   significativa a 5% (p entre 0,06 e 0,16). Em 1 mes o ARIMA continua melhor.
4. **O painel nao melhora o controle em SJC.** O LSTM so com a serie de SJC foi o melhor aos 12 meses (2,13%), e nenhuma
   variante de painel o supera de forma significativa (p > 0,16). Aqui o ganho nao vem de mais cidades.
5. **A semelhanca entre cidades nao trouxe ganho consistente.**
   - As 10 "mais parecidas" melhoraram o painel de SJC aos 12 meses (2,47% contra 3,27%), mas nao o controle, e pioraram o
     nacional (1,87% contra 1,76%).
   - A ponderacao por semelhanca ficou igual ao painel simples nos dois alvos.
   - As cidades mais parecidas com SJC (Praia Grande, Vila Velha, Blumenau, Santo Andre, Goiania, Balneario Camboriu) **nao sao
     as vizinhas**; para o nacional sao Sao Paulo, Rio de Janeiro e Campinas. A semelhanca de dinamica nao e geografica.
   - A hipotese de que cidades muito diferentes atrapalham o painel nao se confirmou com estes dados, mas tambem nao se mostrou
     que aproximar as parecidas ajude.
6. **Cuidado com SJC:** o bom resultado das redes em SJC pode refletir, em parte, que o ARIMA com `d = 2` **extrapola em
   excesso a aceleracao** de 2021-2022 (a tendencia simples de 12 meses tambem supera o ARIMA aos 12 meses). Com poucas origens e
   um unico periodo de teste, nao se deve generalizar.

## Conclusao para as metas 5 e 6

- **Indice nacional:** o ARIMA e o melhor modelo. O LSTM, mesmo em painel, nao o supera.
- **Sao Jose dos Campos (referencia mais proxima de Jacarei):** as redes (e o gradient boosting global) apresentam erro menor
  aos 6 e 12 meses, **mas sem significancia estatistica**; o ARIMA segue melhor em 1 mes.
- **O painel de 50 cidades ajuda quando a serie do alvo e longa e o modelo e uma rede (nacional), nao quando ela e curta
  (SJC).** Nao ha evidencia de que ponderar pela semelhanca ajude.
- Um resultado honesto para o relatorio: **nenhum modelo e uniformemente melhor**; a escolha depende do alvo e do horizonte.

## Limitacoes

- SJC tem so 44 origens de teste (33 aos 12 meses); as conclusoes sobre SJC sao indicativas.
- A semelhanca de SJC e estimada com poucos meses no comeco do teste (60 meses de treino).
- Reajuste anual das redes (o ARIMA e reajustado todo mes); 3 sementes; hiperparametros nao ajustados.
- Uma medida de semelhanca baseada em caracteristicas estruturais do municipio (populacao, renda) nao foi testada.
- O FipeZAP nao tem Jacarei: qualquer projecao para Jacarei depende de aceitar SJC ou o nacional como referencia.

## Proximos passos

1. **Projecao de preco de Jacarei:** combinar o modelo de precificacao (R$/m2 de cada imovel hoje) com a tendencia do FipeZAP
   (SJC ou nacional), com intervalo de incerteza.
2. Aumentar o numero de origens de SJC conforme novos meses do FipeZAP sejam publicados.
3. Testar uma semelhanca estrutural entre municipios, se houver razao para isso.
