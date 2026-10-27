# Roteiro das apresentações do JECET

Dois trabalhos: **(A) coleta e mineração de dados** e **(B) LSTM x ARIMA**. Números conferidos em `README.md`,
`reports/results/mineracao.md`, `docs/MODELOS_LSTM.md` e `docs/SENSIBILIDADE.md`.

## A. Coleta e mineração de dados de anúncios

**Sequência de slides (8 a 10):**
1. Problema: muitos anúncios, coleta manual inviável.
2. Coleta: scraping de anúncios de Jacareí (Selenium, ZAP Imóveis e VivaReal, lendo o JSON-LD que a própria página traz); base de análise de 23.128 anúncios, coletada em março/2026.
3. Limpeza: duplicatas pelo id do anúncio (1.984 removidas), condomínio/IPTU implausíveis tratados -> 3.992 apartamentos e 10.254 casas (`reports/results/vivareal_limpeza.md`).
4. Mineração (1): correlação com R$/m2. Casas: condomínio 0,50; comodidades 0,34; suítes 0,29. Apartamentos: suítes 0,32; banheiros 0,26; vagas 0,25.
5. Mineração (2): 4 grupos de imóveis (K-means). Casas de ~250 m2 e 4 vagas têm R$/m2 mediano ~5.360 contra ~4.300 das de ~90 m2.
6. Mineração (3): termos do anúncio vs preço do bairro. Casas: condomínio +15,7%, salão de festas +11,5%, quadra +11,1%, portaria +11,0%.
7. Modelo de preço: R2 0,73 (apartamento) e 0,80 (casa) em teste temporal; MAPE 11% e 15%.
8. O que mais pesa: apartamento = localização fina (+53% de erro se embaralhar); casa = bairro, contexto, tamanho e condomínio parecidos.
9. Limitações (não esconder): retrato único, viés de sobrevivência, preço de oferta, associação não é causa.

**Perguntas prováveis:**
- *"O scraper é seu?"* Desenvolvi um coletor em Selenium (`src/scraper.py`: dois portais em paralelo, leitura do JSON-LD, retomada, deduplicação entre portais, 38 testes), mas a análise usa a base de 23.128 anúncios de março/2026 compartilhada pelo orientador. Diga isso com clareza.
- *"Isso é legal / respeita o site?"* Dados públicos de anúncios, sem dados pessoais guardados (nome do anunciante, telefones e imagens ficam de fora). O coletor lê o `robots.txt` e respeita as regras. Se o portal pede CAPTCHA, uma pessoa resolve na janela; se **nega o acesso** (Cloudflare "you have been blocked", que aconteceu em 2026-10-26 depois de várias rodadas de teste), o coletor **para e não contorna** (sem proxy, sem trocar de IP, sem esconder o navegador). Falta checagem formal dos termos de uso; isso é trabalho futuro.
- *"Por que não coletou mais dados agora?"* Os portais bloquearam o acesso após rodadas repetidas de teste. Decisão: não burlar o bloqueio; usar a base do orientador (março/2026) e, no futuro, recoletas espaçadas ou dados abertos (ITBI). O que foi validado: a amostra real dos dois portais (30 anúncios por página no JSON-LD, batendo com os cards) e a detecção de bloqueio.
- *"Que campos o scraper guarda?"* Preço, área, quartos, banheiros, vagas, comodidades, bairro, rua, data de publicação, condomínio, IPTU, tipo do imóvel, cômodos, aceita pets, fotos, destaque e o JSON-LD bruto do anúncio (sem anunciante e sem imagens).
- *"Isso é mineração ou só estatística?"* Agrupamento (K-means), análise de termos do texto e importância de variáveis por permutação, dentro de um fluxo coleta -> limpeza -> mineração -> avaliação.
- *"Vale para o preço de venda?"* Não: são preços pedidos. Não há preço de fechamento.
- *"Por que o `bairro` e os termos não são causais?"* Termos como "salão de festas" marcam casa em condomínio fechado; o efeito é do padrão do imóvel, não da palavra.

## B. LSTM x ARIMA

**Sequência de slides (8 a 10):**
1. Pergunta: redes LSTM preveem o índice de preços melhor que o ARIMA?
2. Dados: 49 séries (FipeZap, BCB, IBGE, IPEA) em banco único; painéis "as-of" e teste de vazamento (0 falhas).
3. Por que SJC: Jacareí não está no FipeZap; SJC é a cidade coberta mais próxima.
4. Método: LSTM treinada em painel de 50 cidades, prevendo crescimento; walk-forward de 1 a 12 meses; Diebold-Mariano.
5. Nacional: ARIMA(0,2,3) vence (MAPE 1,18% aos 12 meses vs 1,7% a 2,3% das redes).
6. SJC: redes erram menos aos 6 e 12 meses (MAPE 2,1% a 3,3% vs 5,5%), mas **sem significância** (p de 0,06 a 0,16); ARIMA melhor em 1 mês.
7. Conclusão honesta: nenhum modelo é uniformemente melhor; ARIMA é difícil de bater em série longa e suave.
8. Macro no LSTM: testado (`python main.py lstm-macro`, 12 variantes de rede x 4 conjuntos de macro, 5 sementes, 2 alvos). **O macro não melhorou**: a variante escolhida pelo período de seleção (crédito + juros + confiança + IBC-Br) piorou na confirmação (RMSE 1,34x o do ARIMA em SJC, contra 0,83x na seleção). Sem macro, a rede pequena ficou estável (0,84x na seleção, 0,97x na confirmação).
9. Trabalho futuro: série própria de Jacareí (recoletas periódicas), mais dados para o LSTM.

**Perguntas prováveis:**
- *"Cadê o macro no LSTM?"* Foi testado: BCB, IBGE e IPEA (8 indicadores, e 2 subconjuntos definidos antes) entraram como entradas da rede, em painel de 50 cidades, com as mesmas sementes e a mesma validação. Nenhuma variante com macro superou a sem macro de forma estável; a que ganhou na seleção perdeu na confirmação. Resultado negativo, relatado em `reports/results/lstm_macro.md`. Possíveis motivos: poucas observações mensais (SJC tem 104 meses) e macro lento demais para prever o índice em 12 meses.
- *"Por que não usou as características dos imóveis no LSTM?"* O preço por características é outro problema (transversal, tratado no trabalho A); o VivaReal é um retrato único, sem série temporal.
- *"E o MAE e o R²?"* MAE, RMSE e MAPE estão em `reports/results/lstm_macro.md` (para o ARIMA, as regressões e as redes). O R² não é usado porque o alvo é o nível do índice, em que quase tudo dá R² próximo de 1; o erro por horizonte é mais informativo.
- *"Poucos dados?"* Sim: SJC tem 104 meses e 44 origens de teste; por isso a falta de significância é um achado, não um defeito escondido.
