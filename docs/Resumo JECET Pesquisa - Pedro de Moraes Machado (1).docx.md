

**Coleta e mineração de dados de anúncios imobiliários por meio de web scraping**

Pedro de Moraes Machado  
Instituto Federal de São Paulo \- Campus Jacareí  
[machado.moraes@aluno.ifsp.edu.br](mailto:emailautor1@email.com.br)

**Resumo**

Plataformas digitais concentram grande volume de anúncios imobiliários, mas a coleta manual dessas informações é inviável pelo volume e pela necessidade de atualização. Esta pesquisa tem como objetivo aplicar coleta automatizada (web scraping) e mineração de dados a anúncios de imóveis de Jacareí-SP, identificando as características associadas ao preço por metro quadrado. A pesquisa é exploratória e descritiva. Foi desenvolvido um coletor em Selenium e a análise utiliza uma base de 23.128 anúncios de Jacareí, coletada por scraping em março de 2026, da qual foram extraídos preço, localização, coordenadas, áreas, quartos, suítes, vagas, condomínio, IPTU, comodidades e o texto do anúncio. Os dados passaram por limpeza e padronização (remoção de duplicatas pelo identificador do anúncio e tratamento de valores implausíveis de condomínio e IPTU), resultando em 3.992 apartamentos e 10.254 casas. Na mineração foram aplicadas correlação de postos de Spearman, agrupamento por K-means e análise dos termos do anúncio em relação ao preço do bairro, além de modelos de gradient boosting com validação temporal. Os modelos explicaram 73% (apartamentos) e 80% (casas) da variação do preço por m², com erro percentual médio de 11% e 15%. Nos apartamentos, a localização fina (coordenadas e preço dos vizinhos) foi o grupo mais relevante; nas casas, bairro, contexto, tamanho e condomínio tiveram pesos semelhantes. Entre as casas, a taxa de condomínio foi a característica mais associada ao preço por m² (Spearman 0,50), e termos como salão de festas, quadra e portaria apareceram em anúncios cerca de 10% acima do preço mediano do bairro. Os resultados são associações, não relações causais, e a base é um retrato único de anúncios ativos, sujeito a viés de sobrevivência e a preços de oferta, não de venda. Conclui-se que a coleta automatizada, combinada à mineração, permite transformar anúncios da web em uma base estruturada e identificar os fatores que mais se associam ao preço dos imóveis na cidade.

**Palavras-chave:** Web scraping; mineração de dados; mercado imobiliário; análise de dados; imóveis.

