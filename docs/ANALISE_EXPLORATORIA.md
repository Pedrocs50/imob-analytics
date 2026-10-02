# Analise exploratoria (meta 3): leitura dos resultados

Data: 2026-09-30. Numeros e tabelas completos em `reports/results/eda_series.md`
e `reports/results/eda_vivareal.md` (tabelas em CSV em `reports/results/eda/`);
figuras em `reports/figures/eda_*.png`.

```bash
python main.py eda-series     # FipeZAP + macro
python main.py eda-vivareal   # apartamento, casa, residencial
```

Este documento interpreta os resultados e separa o que a analise **mostra** do
que ela **nao** permite concluir. Nada aqui e um resultado de previsao.

# Parte 1: series temporais (FipeZAP e macro)

## O que os dados dizem sobre o alvo

1. **A variacao mensal do preco e uma serie muito persistente, nao estacionaria.**
   Autocorrelacao no lag 1 de 0,98 (nacional) e 0,81 (SJC); ADF nao rejeita raiz
   unitaria (p = 0,40 e 0,54). Passa nos testes (ADF e KPSS) so depois de uma
   diferenca adicional: o log do preco precisa de **d = 2** nas duas series
   nominais. Explicacao: o indice e media movel trimestral e o crescimento muda
   de regime devagar (2008-2011 alto, 2015-2019 quase zero, depois retomada).
2. **Estrutura de medias moveis.** Na serie com d = 2, a ACF e a PACF mostram
   significancia no lag 3 (nacional: -0,22; SJC: -0,35) e alguns lags de ordem
   maior. E o padrao esperado de uma media movel trimestral e sugere comecar a
   busca do ARIMA por `(0, 2, q)` e `(p, 2, q)` com `p, q` ate 3. A escolha final
   sai da comparacao por AIC e por erro fora da amostra, na etapa do ARIMA.
3. **Preco real (deflacionado pelo IPCA) do indice nacional passa como
   estacionario em nivel** (ADF p = 0,002; KPSS p = 0,062, valor marginal).
   Visualmente e um ciclo: sobe ate 2014, cai ate ~2022 e se recupera pouco
   (`eda_alvo_niveis.png`, `eda_crescimento_selic.png`). A conclusao de "estacionario"
   e frágil (KPSS proximo de 0,05, uma unica subida e queda no periodo); vale
   tratar como hipotese alternativa de modelagem, nao como fato.
4. **Nao ha sazonalidade.** Forca sazonal STL de 0,07 (nacional) e 0,03 (SJC);
   Kruskal-Wallis p ~ 1. Por isso nenhum grafico de sazonalidade foi gerado, e o
   ARIMA nao precisa de componente sazonal.
5. **Sao Jose dos Campos nao segue o nacional no curto prazo.** Em variacao
   mensal a correlacao e 0,45, mas isso e tendencia comum: apos estacionarizar cai
   para ~0,02. Desde 2018 o indice de SJC cresceu muito mais (210 contra 144,
   base 100 em 2018-01), com aceleracao em 2021-2022. SJC e uma referencia
   propria, nao uma versao do indice nacional.
6. **Faixas de dormitorios** (indice nacional): todas andam juntas (correlacao
   de 0,92 a 0,98 com o total), mas 1 dormitorio subiu mais (5,05x) que 4
   dormitorios (3,82x). Nao ha motivo para modelar cada faixa separadamente por
   enquanto.
7. **Pontos atipicos:** so 3 meses acima de 3,5 desvios robustos (nacional
   2011-04; SJC 2022-01 e 2022-02). Nao ha necessidade de tratamento.

## O que os preditores macro mostram

- Todos os 12 preditores ficaram estacionarios; o **saldo de credito** e a
  **desocupacao (IPEA)** precisaram de uma diferenca extra.
- **Colinearidade:** a Selic real (derivada) e negativamente correlacionada com o
  IPCA (-0,76) e o IGP-M (-0,55); os juros de financiamento (mercado e regulada)
  correlacionam 0,53. Como a Selic real e derivada do IPCA, ela e candidata a sair
  do ARIMAX.
- **Correlacao cruzada (curto prazo, series estacionarias):** **nenhuma**
  relacao passa do limiar conservador entre os lags utilizaveis. O maior |r| e
  ~0,2. A correlacao de 0,85 entre o saldo de credito e a variacao do preco, que
  aparece com as series como vinham, cai para 0,18 ao estacionarizar: era
  tendencia comum entre duas series persistentes, nao previsao.
- **Granger (estacionario):** IBC-Br (p = 0,002 no lag 1) e confianca do
  consumidor (p = 0,047) sao os unicos com p < 0,05 para o nacional; para SJC,
  a Selic (p = 0,027). **Nenhum passa a correcao de Bonferroni** (p < 0,0007).
  Com 72 testes por alvo, alguns p < 0,05 ocorreriam por acaso.
- **Relacoes de baixa frequencia (variacao de 12 meses)** parecem fortes na
  amostra toda (credito 0,93; confianca 0,82), mas **nao se sustentam por
  subperiodo**: o credito vai de +0,95 (2009-2014) e +0,85 (2015-2020) para
  **-0,09 (2021-2026)**; a confianca de 0,56 para -0,04 e 0,10; a Selic real e o
  INCC trocam de sinal. Sao series com autocorrelacao de 0,87 a 0,94 no lag 12,
  ou seja, poucas observacoes independentes (cerca de 18 anos). O que se ve e
  um unico ciclo de expansao e queda, nao uma relacao estavel.
- **Trimestral (nacional; desocupacao e renda de SP, Selic, IPCA e IBC-Br),
  series estacionarias:** o maior |r| de cada preditor e de 0,14 a 0,23, sempre
  abaixo do limiar de 95% (0,23 a 0,30). Nada significativo.

**Leitura honesta:** com estes dados, o macro nao mostra poder preditivo
estavel para a variacao mensal do preco. Isso nao prova que nao existe efeito
(a dupla diferenciacao apaga relacoes de longo prazo e a amostra e curta), mas
significa que **o ganho de um ARIMAX ou de um LSTM multivariado sobre um ARIMA
univariado e uma hipotese a testar fora da amostra, nao algo a assumir**. Isso e
um resultado valido para a meta 6.

## Suficiencia amostral (apos estacionarizar)

| Cenario | Observacoes | Obs. por variavel |
|---|---|---|
| ARIMA univariado, nacional | 222 | 222 |
| ARIMAX/LSTM, nacional, 9 preditores com historico desde 2008 | 221 | 24,6 |
| ARIMAX/LSTM, nacional, 12 preditores | 173 | 14,4 |
| ARIMA univariado, SJC | 102 | 102 |
| ARIMAX/LSTM, SJC, 12 preditores | 101 | 8,4 |
| Trimestral univariado, nacional / SJC | 72 / 32 | - |
| Trimestral, nacional, com desocupacao e renda de SP | 48 | 24 |

Com 101 observacoes e 8 a 11 por variavel, um LSTM multivariado para SJC tem
dados muito escassos; para o indice nacional (221 observacoes) e viavel, com
poucos preditores.

## Decisoes para as proximas etapas (a confirmar)

1. **Alvo principal:** log do FipeZAP nacional nominal (224 meses), com `d = 2`.
   SJC como alvo secundario (referencia local), sabendo que so tem 104 meses.
2. **Alvo alternativo:** log do preco real (`d = 0`), somando uma previsao de
   inflacao. Vale comparar as duas formulacoes na meta 6.
3. **Sem termo sazonal.**
4. **Preditores para o ARIMAX:** comecar com poucos e economicamente
   motivados (Selic ou juros de financiamento, saldo de credito, IBC-Br,
   confianca), **sem a Selic real** (colinear com o IPCA). Todos entram com a
   defasagem de publicacao (painel as-of) e estacionarizados. Como o teste
   univariado nao selecionou nada de forma robusta, a decisao de incluir ou nao
   deve vir da comparacao fora da amostra.
5. **Validacao:** usar janela expansiva (walk-forward) com origem movel; nunca
   embaralhar a serie. O periodo 2021-2026 e onde o padrao do credito mudou, entao
   vale reservar esse trecho como teste.
6. **Cuidado metodologico:** o FipeZAP e media movel trimestral. Isso torna a
   previsao a 1 mes a frente aparentemente facil e os erros correlacionados; a
   comparacao ARIMA x LSTM deve reportar tambem horizontes de 3 e 6 meses.

# Parte 2: datasets do VivaReal

Base: `data/processed/vivareal/{apartamento,casa,residencial}.csv` (3.992,
10.254 e 14.246 linhas).

## Achados

1. **Distribuicao do alvo:** apos a limpeza, o `preco_m2` e razoavelmente
   simetrico (assimetria de 0,40 em apartamento e 0,58 em casa; a do log e
   -0,28 e -0,39). A transformacao logaritmica **nao e necessaria por causa da
   assimetria**; pode ser mantida ou removida conforme a validacao.
2. **Tipos tem niveis de preco diferentes:** mediana de R$/m2 de 6.193
   (apartamento), 6.021 (casa em condominio) e 3.840 (casa comum). No modelo
   `residencial` e obrigatorio informar o segmento/tipo, senao ele aprende
   sobretudo a diferenca entre tipos.
3. **Condominio (casas):** casas em condominio custam R$ 6.021/m2 contra R$
   3.840 (mediana, +57%, p < 0,001). A taxa de condominio correlaciona 0,51 com o
   preco, mas isso vem sobretudo de ela ser um **indicador de condominio**: a
   taxa esta ausente em 47,5% das casas fora de condominio e em so 3,2% das
   casas em condominio. Entre quem tem taxa positiva, a correlacao cai para
   0,04. Consequencia: a taxa e redundante com `em_condominio`, e o fato de
   estar **ausente** carrega informacao, entao imputar por mediana esconderia
   isso. Para apartamentos a taxa correlaciona 0,19 entre quem tem valor.
4. **Localizacao importa e tem furos:** so ~48% dos anuncios tem coordenadas.
   Latitude correlaciona 0,46 com o preco em apartamentos e 0,36 em casas; o
   mapa (`eda_vivareal_mapa.png`) mostra um agrupamento de precos altos no
   nordeste de Jacarei. O **bairro** explica 35% (apartamento) e 39% (casa) da
   variancia do log do preco por m2 (entre bairros com 30 ou mais anuncios,
   que cobrem ~93% da base). Mas 34 dos 71 bairros de apartamento tem menos de
   10 anuncios; precisam de agrupamento ou suavizacao.
5. **Area util quase nao explica o preco por m2:** correlacao de 0,11 em
   apartamento e -0,03 em casa. O tamanho vem mais por suites, banheiros e vagas
   (0,25 a 0,32 em apartamento).
6. **Sem multicolinearidade entre as variaveis de tamanho:** VIF de 1,4 a 2,6.
7. **Valores ausentes:** suites 13-16%, IPTU ~30%, condominio 36% nas casas,
   coordenadas ~52%.
8. **Valores implausiveis que a limpeza atual nao trata:** taxa de condominio
   acima de R$ 5.000 (9 apartamentos, 8 casas; maximos de R$ 620 mil e R$ 2,5
   milhoes), IPTU anual acima de R$ 30.000 (1 e 19; maximo de R$ 1,8 milhao) e
   alguns valores positivos abaixo de R$ 50. Zeros sao legitimos (imovel sem
   taxa) e nao devem ser removidos.
9. **Tempo:** 2026-T1 concentra a maioria dos anuncios (1.788 apartamentos e
   3.591 casas). As medianas por trimestre de criacao nao mostram tendencia e
   tem viés de sobrevivencia; nao servem como serie de precos.

## Decisoes para as proximas etapas (a confirmar)

1. **Ajustar `vivareal-prep`:** tratar condominio > R$ 5.000 e IPTU > R$ 30.000
   como ausentes (nao remover a linha) e criar indicadores de "taxa informada".
2. **Variaveis de partida por segmento:** area, quartos, banheiros, suites, vagas,
   comodidades, bairro suavizado, `em_condominio` (casas) e, como teste separado,
   coordenadas. Condominio e IPTU entram como teste comparativo (com e sem),
   porque o ganho vem da ausencia, nao do valor.
3. **Modelo residencial:** incluir o tipo/segmento como variavel.
4. **Ordem sugerida:** regressao linear multipla por segmento como referencia,
   depois Random Forest reaproveitando o baseline (com os limites atuais
   documentados) e comparar.

# Limitacoes

- O teste de vazamento cobre o alinhamento no tempo, nao a **revisao** dos
  dados: o IBC-Br dessazonalizado foi revisado (ate 0,26%) e a versao usada e a de
  setembro/2026. Cinco defasagens seguem estimadas (ver `docs/SERIES_TEMPORAIS.md`).
- As correlacoes cruzadas usam limiar conservador (n/3 para a serie suavizada;
  n/12 nas variacoes de 12 meses). E exploratorio: nao ha correcao formal para
  autocorrelacao dos dois lados.
- O Granger assume dinamica linear e estabilidade; a mudanca de regime do
  credito em 2021 sugere que isso nao vale em toda a amostra.
- As series trimestrais do IBGE tem lacunas na propria fonte (renda de SP, 8
  trimestres); ficaram como ausentes.
- Nada aqui compara modelos: as figuras e testes apenas orientam a escolha.
