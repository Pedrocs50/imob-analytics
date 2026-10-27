

**Previsão de preços de imóveis com redes neurais LSTM: comparação com ARIMA em séries do índice FipeZap**

Pedro de Moraes Machado  
Instituto Federal de São Paulo \- Campus Jacareí  
[machado.moraes@aluno.ifsp.edu.br](mailto:emailautor1@email.com.br)  
Tardelli Ronan Coelho Stekel  
Instituto Federal de São Paulo \- Campus Jacareí  
stekel@ifsp.edu.br

**Resumo**

O comportamento dos preços de imóveis ao longo do tempo apresenta dependências temporais que modelos tradicionais de regressão nem sempre capturam. Esta pesquisa tem como objetivo avaliar se redes neurais recorrentes do tipo LSTM (Long Short-Term Memory) preveem o índice de preços de imóveis com mais precisão que o modelo estatístico ARIMA. A pesquisa é exploratória e aplicada. Foi construído um banco de séries temporais com 49 séries do índice FipeZap e de indicadores do Banco Central do Brasil, do IBGE e do IPEA, com painéis mensal e trimestral organizados de modo que cada mês contenha apenas o que já estava publicado, validados por testes de vazamento temporal. Como Jacareí não consta no FipeZap, foram usados o índice nacional e São José dos Campos, cidade coberta mais próxima. As redes LSTM foram treinadas sobre o crescimento mensal das séries de 50 cidades e comparadas ao ARIMA, a uma tendência simples e a um gradient boosting global, em validação walk-forward com horizontes de 1 a 12 meses, medindo MAPE e RMSE e testando a significância das diferenças (Diebold-Mariano). No índice nacional, o ARIMA(0,2,3) obteve o menor erro (MAPE de 1,2% aos 12 meses, contra 1,7% a 2,3% das redes). Em São José dos Campos, as redes erraram menos aos 6 e 12 meses (MAPE de 2,1% a 3,3% contra 5,5% do ARIMA aos 12 meses), mas a diferença não foi estatisticamente significativa a 5%, e o ARIMA foi melhor em 1 mês. Os indicadores macroeconômicos foram integrados ao banco e analisados por correlação cruzada e causalidade de Granger, mas não foram utilizados como entradas do LSTM, o que fica como trabalho futuro. Conclui-se que nenhum modelo foi uniformemente superior: o ARIMA é difícil de superar em séries longas e suaves, enquanto as redes se mostram promissoras em séries curtas, o que justifica novos testes com preditores macroeconômicos.

**Palavras-chave:** LSTM; redes neurais; previsão de preços; mercado imobiliário; séries temporais.

