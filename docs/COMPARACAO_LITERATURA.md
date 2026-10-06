# Comparacao com a literatura

Data: 2026-10-05. Fonte unica dos trabalhos: `src/reporting/referencias.py` (a secao 7 e o apendice B do relatorio sao gerados dela; ver
`docs/RELATORIO_AUTOMATICO.md`). Este documento explica **como** comparar e **o que** a comparacao permite concluir.

## Como foi feita a pesquisa e o que foi (e nao foi) verificado

Busca na web por trabalhos sobre (a) precificacao de imoveis com aprendizado de maquina no Brasil, (b) ARIMA contra LSTM em precos de imoveis,
(c) intervalos de previsao conformais em imoveis, (d) texto de anuncios como variavel, (e) desconto entre preco anunciado e de venda e (f) precisao de
avaliadores automaticos. Cada trabalho foi aberto e os numeros abaixo foram lidos no **resumo ou no texto**; quando so havia o resumo, isso esta dito na ressalva.

| Trabalho | O que foi lido | Limite da leitura |
|---|---|---|
| Neri (2020), UFMG | Resumo e capitulos de dados e metodo: 16.919 treino + 1.877 teste, MAPE 8,21%, R² 93,92%, particao aleatoria 90/10 | Texto completo do inicio; nao se reproduziu a base |
| Pereira (2025), UFPB | Pagina do repositorio com resumo: R² 85,42%, MAPE 18,21%, RMSE R$ 227.677 | So o resumo; nao informa a validacao nem o n |
| Zilli e Bastos (2024), USP | Resumo: 1.572 apartamentos, gradient boosting melhor em todas as metricas | So o resumo; sem valores absolutos por modelo |
| Bastos e Paquette (2024), ISEG | Resumo e inicio do texto: conformal quantile regression, cobertura exata | Nao se leu a secao de resultados numericos |
| Hansson e Rostami (2019), Uppsala | Resumo: ARIMA sazonal supera o LSTM em 12 meses | So o resumo; sem metricas numericas |
| Siami-Namini e Siami Namin (2018), arXiv | Resumo: LSTM reduz o erro em 84% a 87% frente ao ARIMA | Series financeiras/economicas; so o resumo |
| Cambridge (NLE) e UConn (2019) sobre texto | Resumos e paginas de busca; "+15% por desvio-padrao de qualidade" vem do UConn | Nao se abriu o texto completo |
| FipeZAP via B3 Bora Investir | Pagina: desconto medio 8% (12 anos), 12% com desconto, 68% das compras com desconto (set/2025) | Fonte secundaria |
| Zillow | Pagina de precisao: erro mediano ~1,8% (a venda) e ~7% (fora do mercado) | Metrica da propria empresa; EUA |

**Consequencia:** a comparacao e **qualitativa e de ordem de grandeza**. Nao ha trabalho identico (Jacarei, preco pedido, divisao temporal),
e varios numeros vem de resumos. Uma revisao sistematica exigiria ler os textos completos e, se possivel, replicar os metodos nesta base.

## Como comparar com justica

Tres diferencas mudam os numeros e precisam ser neutralizadas:

1. **O que e previsto.** Os trabalhos brasileiros reportam o **preco total**; este projeto prediz o **R$/m2** (mais dificil: a area, que explica boa parte do
   preco total, ja foi removida). Para comparar, calculou-se o R² e o MAPE do **preco total** a partir das previsoes fora da amostra do projeto.
2. **Como se valida.** Belo Horizonte usa uma unica divisao aleatoria 90/10. O R² do projeto comparavel e o de **5 particoes aleatorias fora da amostra**; o R² do
   **teste temporal** (anuncios mais recentes) e mais duro e e o que o projeto usa como principal.
3. **O tipo de preco.** Tudo aqui e **preco pedido**. A venda costuma ser menor (FipeZAP: desconto medio de 8%).

## Resultados da comparacao

| Medida | Apartamento | Casa |
|---|---|---|
| R² do preco total, particao aleatoria (5-fold, fora da amostra) | 0,85 | 0,90 |
| MAPE do preco total | 11,2% | 15,3% |
| R² do R$/m2, teste temporal (conjunto final) | 0,73 | 0,80 |
| MAPE do R$/m2, teste temporal | 11,1% | 15,0% |
| Erro relativo mediano fora da amostra | 8,1% | 10,4% |

Referencias: Belo Horizonte (apartamentos) MAPE 8,21% e R² 0,94; Joao Pessoa MAPE 18,21% e R² 0,85.

### O que **concorda** com a literatura

- **Gradient boosting e arvores superam o modelo linear e o Random Forest** (Zilli e Bastos, 2024). Aqui: R² temporal de apartamento 0,49 (linear) -> 0,62 (gradient boosting
  sem coordenadas); o Random Forest, nas mesmas condicoes, fica abaixo do gradient boosting nos tres segmentos.
- **Area e localizacao no topo** (Pereira, 2025: area, coordenadas, aluguel do bairro). Aqui: area e, nos apartamentos, a localizacao fina; nas casas, bairro, tamanho e condominio.
- **Texto e atributos adicionais ajudam** (Cambridge, UConn). Aqui: terreno e texto elevaram o R² temporal das casas em +0,044.
- **Intervalos conformais cobrem o nominal** e sao mais largos onde o imovel e mais heterogeneo (Bastos e Paquette, 2024). Aqui: cobertura de 81% a 82% para 80% nominal, e intervalos
  mais largos nas casas (±23,6%) que nos apartamentos (±18,0%).
- **ARIMA vence o LSTM em precos de imoveis suaves** (Hansson e Rostami, 2019). Aqui: no indice nacional o ARIMA tem o menor erro em todos os horizontes.

### O que **difere** e por que

- **MAPE do preco total entre os dois extremos brasileiros** (8,21% e 18,21%): o do projeto (11% a 15%) fica no meio. Belo Horizonte tem muito mais dados, uma unica divisao aleatoria
  e apartamentos (mais homogeneos); Joao Pessoa mistura tipos e nao informa a validacao.
- **LSTM nao supera o ARIMA aqui, ao contrario de Siami-Namini e Siami Namin (2018).** Hipoteses (nao testadas): o indice FipeZAP e muito mais suave e curto que as series financeiras do
  estudo, e o ARIMA e reestimado todo mes no *walk-forward*. O resultado depende do tipo de serie e do desenho da avaliacao.
- **Em Sao Jose dos Campos** as redes erram menos aos 6 e 12 meses, o que lembra o resultado de Siami-Namini, mas **sem significancia estatistica** (poucas origens): nao se
  deve generalizar.

### Preco pedido e avaliadores automaticos

- Descontos de negociacao de 8% em media (12% quando ha) significam que as estimativas deste projeto sao **precos pedidos esperados**, nao de venda.
- O erro mediano da Zillow (~7% fora do mercado, ~1,8% a venda, esse ultimo usando o preco anunciado como entrada) e da **mesma ordem de grandeza** do erro relativo mediano do
  projeto (8% a 10%), em mercado menor, com bem menos dados e prevendo o preco pedido.

## Conclusao

Os resultados sao **consistentes com a literatura** nos pontos comparaveis e **nao contradizem** nenhum trabalho lido; a divergencia com Siami-Namini e explicada por diferencas
de serie e avaliacao. O ganho de originalidade esta em: (i) validacao **temporal** em dados de anuncios de uma cidade media brasileira, (ii) tratamento explicito de dados faltantes
sem vazamento do preco, (iii) intervalos calibrados e testados, (iv) ponte entre precificacao transversal e tendencia de indice com premissas declaradas.

## Proximos passos para uma comparacao mais forte

1. Ler os textos completos de Neri (2020), Zilli e Bastos (2024) e Pereira (2025) e replicar as divisoes (ex.: 90/10 aleatoria) na base de Jacarei.
2. Incluir uma base de **precos de transacao** (ou um ajuste de negociacao) para comparar com Zillow-tipo AVMs de forma justa.
3. Buscar estudos sobre indices FipeZAP com ARIMA/LSTM (a busca feita encontrou estudos de bolhas com ARIMA, nao de previsao com LSTM).
