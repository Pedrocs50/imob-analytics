# Roteiro das apresentações do JECET

Dois trabalhos: **(A) coleta e mineração de dados** e **(B) LSTM x ARIMA**. Números conferidos em `README.md`,
`reports/results/mineracao.md`, `docs/MODELOS_LSTM.md` e `docs/SENSIBILIDADE.md`.

## A. Coleta e mineração de dados de anúncios

**Fio condutor:** *o que faz um imóvel custar mais que os vizinhos do mesmo bairro?* O scraping é só a entrada; o foco é a mineração.

**Sequência de slides (11):** (figuras em `reports/figures/`; números em `reports/results/mineracao*.md`)
1. **Problema e pergunta:** coleta manual não escala; o que explica preço além do bairro?
2. **Dados:** scraping (ZAP e VivaReal, JSON-LD) e a base de análise de 23.128 anúncios (março/2026). *Uma frase sobre o bloqueio do Cloudflare e a decisão de não contornar.*
3. **Limpeza:** 1.984 duplicatas, condomínio/IPTU implausíveis tratados; 3.992 apartamentos e 10.254 casas.
4. **Método:** comparar cada anúncio com a mediana do **próprio bairro** (tira o efeito "bairro caro"); técnicas: correlação, grupos, regras, árvore, anomalias.
5. **Correlações** (`mineracao_correlacao_casa.png`, `..._apartamento.png`): casas: condomínio 0,50, comodidades 0,34, suítes 0,29; apartamentos: suítes 0,32, banheiros 0,26, vagas 0,25; IC95% estreitos e iguais nas duas metades.
6. **Perfis de imóveis** (`mineracao_grupos_casa.png`): casas de ~250 m² e 4 vagas: R$/m² mediano ~5.330 contra ~4.250 nas de ~90 m². *Dizer:* a silhueta é baixa nas casas, então são perfis típicos que se sobrepõem, não segmentos distintos.
7. **Regras de associação:** piscina + segurança + armários planejados → 56% de chance de preço alto para o bairro (média 33%, lift 1,7). **Validação:** em metade dos dados que não participou da escolha, o lift médio cai só de 1,67 para 1,50.
8. **Árvore de decisão** (`mineracao_arvore_casa.png`): acerta 71,6% (contra 66,7% de chutar a classe mais comum). *Não mostrar a árvore dos apartamentos (não superou o acaso); dizer que ali o sinal está nas regras.*
9. **Imóveis fora da curva** (`mineracao_fora_da_curva_*.png`): 86% dos apartamentos e 73% das casas ficam a até 20% do esperado; os extremos são candidatos a revisar (erro de cadastro, sobrepreço, oportunidade), não prova.
10. **Modelo de preço:** R² 0,80 (casa) e 0,73 (apartamento) em teste temporal; MAPE 15% e 11%; o que mais pesa: localização fina (apartamento) e bairro/tamanho/condomínio (casa).
11. **Limitações e próximos passos:** retrato de um mês, preços pedidos, associação não é causa; recoletas espaçadas para ver valorização no tempo; dados abertos (ITBI).

**Slide de backup (se perguntarem):** tempo no ar x preço (Spearman −0,06; anúncios com mais de 2 anos ~6% abaixo do bairro, sinal fraco).

**Perguntas prováveis:**
- *"O scraper é seu?"* Desenvolvi um coletor em Selenium (`src/scraper.py`: dois portais em paralelo, leitura do JSON-LD, retomada, deduplicação entre portais, 38 testes), mas a análise usa a base de 23.128 anúncios de março/2026 compartilhada pelo orientador. Diga isso com clareza.
- *"Isso é legal / respeita o site?"* Dados públicos de anúncios, sem dados pessoais guardados (nome do anunciante, telefones e imagens ficam de fora). O coletor lê o `robots.txt` e respeita as regras. Se o portal pede CAPTCHA, uma pessoa resolve na janela; se **nega o acesso** (Cloudflare "you have been blocked", que aconteceu em 2026-10-26 depois de várias rodadas de teste), o coletor **para e não contorna** (sem proxy, sem trocar de IP, sem esconder o navegador). Falta checagem formal dos termos de uso; isso é trabalho futuro.
- *"Por que não coletou mais dados agora?"* Os portais bloquearam o acesso após rodadas repetidas de teste. Decisão: não burlar o bloqueio; usar a base do orientador (março/2026) e, no futuro, recoletas espaçadas ou dados abertos (ITBI). O que foi validado: a amostra real dos dois portais (30 anúncios por página no JSON-LD, batendo com os cards) e a detecção de bloqueio.
- *"Que campos o scraper guarda?"* Preço, área, quartos, banheiros, vagas, comodidades, bairro, rua, data de publicação, condomínio, IPTU, tipo do imóvel, cômodos, aceita pets, fotos, destaque e o JSON-LD bruto do anúncio (sem anunciante e sem imagens).
- *"Como sabe que as regras não são acaso?"* Escolhi as 10 melhores regras numa metade dos anúncios e medi na outra: o lift médio cai de 1,67 para 1,50 (casas) e de 1,73 para 1,52 (apartamentos), ainda bem acima de 1. Correlações têm IC95% por bootstrap.
- *"Por que 4 grupos?"* Escolha por interpretação: a silhueta de k=4 é baixa nas casas (0,25; melhor k=2, 0,40), então os grupos se sobrepõem e servem como perfis descritivos. Estabilidade entre sementes: ARI 0,98 (casas) e 1,00 (apartamentos).
- *"A árvore dos apartamentos?"* Não superou o acaso (66,3% contra 66,7%); por isso a análise de apartamentos usa regras e correlações, e isso está dito no relatório.
- *"Os imóveis 'fora da curva' estão caros ou baratos?"* Não dá para afirmar: o modelo não vê estado de conservação, acabamento nem fotos. São candidatos a revisar (cadastro errado, sobrepreço, oportunidade).
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
