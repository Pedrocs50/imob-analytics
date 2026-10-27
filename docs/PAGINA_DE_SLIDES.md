# Apresentações do JECET (página web)

Pasta `site/apresentacao/` (publicada no GitHub Pages junto do site). Abrir `site/apresentacao/index.html` (menu) ou direto:

- `a-mineracao.html`: **Apresentação A**, coleta e mineração de dados (16 slides, ~10 min + 1 extra).
- `b-lstm.html`: **Apresentação B**, LSTM e macroeconomia (11 slides, ~10 min).

Arquivos: `assets/deck.css` e `deck.js` (motor), `graficos.js` (gráficos próprios), `dados.js` (números dos resultados, gerados dos CSVs em `reports/results/`), `img/` (figuras e logo do JECET 2026).

## Teclas

| Tecla | Ação |
|---|---|
| `F` | tela cheia |
| `→` `←` ou clique | avança / volta (os itens aparecem um a um) |
| `Tab` | alterna as abas do slide (Casas/Apartamentos, SJC/Nacional...) |
| `P` | janela de notas do apresentador com cronômetro (arrastar para o monitor do notebook) |
| `G` | lista de slides |
| clique numa figura | amplia |

Os slides "Painel interativo" incorporam `../painel.html` e precisam de internet (Plotly por CDN). Sem internet, pule esses slides.

## Atualizar os números

`python main.py mineracao-avancada` regenera os CSVs. Os números de `assets/dados.js` (correlações, regras, tolerância, MAPE) vêm desses CSVs e dos de `reports/results/lstm_macro/`; o gráfico "seleção x confirmação" (B6) tem os valores de `lstm_macro_*_selecao.csv` digitados em `graficos.js` (constante `SEL`).

## Ensaio

Texto de fala de cada slide: tecla `P` (notas) ou o bloco `<aside class="notas">` de cada slide no HTML.
