# Requisitos dos resumos do JECET x o que o repositorio entrega

Os resumos enviados **nao foram alterados**. Esta tabela liga cada promessa a uma evidencia reproduzivel e diz com franqueza onde ha limite.

## A. Coleta e mineracao de dados de anuncios (web scraping)

| Promessa do resumo | Evidencia | Estado |
|---|---|---|
| Coleta automatizada de anuncios | `src/scraper.py` (Selenium, ZAP e VivaReal, JSON-LD, retomada); amostra real validada (30 de 30 anuncios por pagina); 42 testes | Atendido. A **coleta nova em volume esta parada por bloqueio do Cloudflare**; a analise usa a base de 23.128 anuncios (marco/2026) do orientador |
| Extrair preco, localizacao, area, quartos, vagas e demais caracteristicas | Campos do `imoveis_raw` (inclui condominio, IPTU, comodidades, tipo, comodos, pets, fotos, JSON-LD bruto) | Atendido |
| Organizacao, limpeza e padronizacao | `vivareal-prep`: duplicatas por id (1.984), condominio/IPTU implausiveis, 3.992 apartamentos e 10.254 casas | Atendido |
| Mineracao: relacoes entre caracteristicas e preco | `mineracao` (Spearman, K-means, termos) e `mineracao-avancada` (regras de associacao, arvore, fora da curva, tempo no ar) | Atendido |
| Padroes e fatores associados a valorizacao/desvalorizacao | Preco relativo ao bairro: regras com lift 1,5 em dados nao vistos; imoveis acima/abaixo do esperado | Atendido **como associacao**, nao causa. "Valorizacao no tempo" exigiria varias coletas (trabalho futuro) |
| Resultado: base estruturada | Banco `imoveis.db` + CSVs limpos | Atendido |
| Resultado: caracteristicas com maior relacao com o preco | Casas: condominio 0,50, comodidades 0,34, suites 0,29. Apartamentos: suites 0,32, banheiros 0,26, vagas 0,25 (IC95% estreitos) | Atendido |

## B. Previsao com LSTM e indicadores macroeconomicos

| Promessa do resumo | Evidencia | Estado |
|---|---|---|
| LSTM com precos e indicadores macro (BCB, IBGE, IPEA, FipeZap) | `lstm-macro`: 12 redes (macro x arquitetura) x 5 sementes | Atendido |
| Banco de dados centralizado | `imoveis.db` com series e anuncios | Atendido |
| MAE, RMSE e MAPE | `reports/results/lstm_macro.md` | Atendido |
| Comparacao com regressao tradicional | Ridge direto por horizonte, ARIMA e tendencia, com Diebold-Mariano | Atendido |
| "Modelo capaz de prever com maior precisao" | **Nao se confirmou**: o macro nao melhorou de forma estavel; ARIMA segue dificil de bater no nacional. Relatado como resultado negativo | Reportar com honestidade: o resumo diz "espera-se" |
| Caracteristicas dos imoveis na previsao temporal | Modelo de preco por caracteristicas (R2 0,80 casa / 0,73 apartamento, teste temporal) e series de indices | Atendido em duas frentes; o VivaReal e retrato unico, sem serie temporal |

## Limites a assumir na apresentacao

1. Retrato de um unico mes (marco/2026), precos pedidos, nao de fechamento.
2. Associacao nao e causa (condominio fechado explica a maioria das "comodidades").
3. Coleta propria em volume interrompida por bloqueio do portal; decisao de nao contornar.
4. LSTM com macro: resultado negativo.
