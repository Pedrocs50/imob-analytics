# Painel interativo (meta 8)

Data: 2026-10-05. Um unico arquivo HTML com todos os resultados do projeto, para explorar no navegador.

```bash
python main.py painel      # poucos segundos; gera reports/figures/painel_interativo.html (~7 MB)
```

Abra o arquivo no navegador (duplo clique). **Funciona offline**: a biblioteca de graficos (plotly.js) vai embutida na pagina. O arquivo e
gerado e reproduzivel, por isso **nao e versionado** (`.gitignore`).

O painel **nao recalcula nada**: le os resultados que os outros comandos ja salvaram (`reports/results/`, `data/processed/`). Se uma fonte
faltar, o cartao correspondente mostra um aviso com o comando que a gera, e o resto do painel continua funcionando.

## O que ha em cada aba

| Aba | Cartoes | O que responde |
|---|---|---|
| **Resumo** | KPIs (anuncios, R2, erro tipico, erro do ARIMA, tendencia em 12 meses), guia de navegacao e avisos de leitura | Onde estamos e o que ler com cuidado |
| **Mercado** | Mapa do R$/m2 por setor censitario (apartamento / casa); R$/m2 por bairro com faixa de 25% a 75%; distribuicao do R$/m2 | Como esta o mercado de Jacarei |
| **Modelos** | Evolucao do R2 (da regressao linear ao conjunto final); padrao x ajustado x conjunto; preco pedido x valor estimado por anuncio (com faixa de 80%); calibracao dos intervalos | Quao bem (e com que confianca) o modelo precifica |
| **Sensibilidade** | O que mais pesa (por grupo de variaveis); "e se o imovel mudasse?"; R$/m2 pela area e por suites; mesmo imovel em bairros diferentes | O que move o preco (meta 7) |
| **Series temporais** | FipeZAP nacional e de SJC com a previsao do ARIMA e seu intervalo (com seletor de periodo); erro por horizonte de ARIMA, LSTM e gradient boosting | Para onde vai o indice e qual modelo erra menos |
| **Projecao** | Cenarios de tendencia em 3, 6 e 12 meses; mediana do R$/m2 do pedido ate +12 meses; mapa do preco pedido x estimado por setor | Quanto o R$/m2 de Jacarei deve variar e onde se pede acima do estimado |

## Como usar

- **Seletores** (botoes acima do grafico): alternam entre apartamento e casa, ou entre Brasil e Sao Jose dos Campos. Cada traco do grafico
  pertence a um grupo; so o grupo escolhido fica visivel.
- **Passar o mouse** mostra os detalhes (mediana, faixa, numero de anuncios, MAE, etc.). A barra do canto do grafico amplia, move e salva a imagem em PNG.
- **Tema claro/escuro**: botao no topo; por padrao segue o sistema. A escolha fica salva no navegador. O endereco `...html#modelos` abre direto na aba.
- Funciona em telas pequenas (as abas rolam na horizontal e os cartoes viram uma coluna).

## Estrutura do codigo (`src/visualization/`)

```text
estrutura.py     Bloco (um cartao: titulo, texto de leitura, grafico OU tabela, seletor, fonte) e Secao (uma aba)
tema.py          paleta e layout base dos graficos
dados.py         leitura dos resultados (tolera arquivo ausente); setores do IBGE como GeoJSON simplificado
mapa.py          coropleta por setor, com um traco por segmento
mercado.py  modelos.py  sensibilidade.py  series.py  projecao.py     uma funcao por cartao + secao()
painel.py        KPIs, montagem do HTML (abas, tema, seletores) e gravacao do arquivo
```

Para **acrescentar um grafico**: crie uma funcao que devolva um `Bloco` em um dos modulos de secao e inclua-a na lista de `secao()`.
Para **acrescentar uma aba**: crie `nova.py` com `secao()` e inclua-a em `painel.montar()`.

## Decisoes de projeto

- **Um unico arquivo, sem servidor.** Facilita enviar ao orientador e abrir offline (por isso o plotly.js e embutido, ~4,7 MB).
- **Le resultados salvos em vez de recalcular.** O painel e rapido e nao depende dos modelos; o preco e que fica tao atualizado quanto os
  comandos que o alimentam (`modelos-avancados`, `sensibilidade`, `projecao`, `lstm`, `arima`).
- **Cores com funcao fixa.** Categorica na ordem apartamento (azul), casa (laranja), residencial (verde-agua); sequencial em um tom (azul) para o R$/m2;
  divergente azul-vermelho com meio cinza para "pedido acima/abaixo do estimado". Sem eixo duplo. As tres primeiras cores categoricas sao as
  validadas para mapas e dispersoes.
- **Mapas em Leaflet (fundo Esri)**, a mesma tecnologia do `mapa_setores_interativo.html`, que sempre funcionou: ruas e o nome de Jacarei aparecem por baixo dos setores
  censitarios (544 setores, codigo IBGE 3524402). Cada mapa e um iframe carregado so quando a aba abre, com botoes proprios (apartamento / casa), tooltip e legenda; no tema escuro
  os tiles sao invertidos por CSS. Os tiles vem da internet; sem internet o mapa nao carrega. (O fundo do OpenStreetMap foi trocado pelo do Esri porque o OSM bloqueia paginas abertas de arquivo ou iframe sem "referer" e o Carto passou a exigir chave. Uma versao anterior usava mapas do Plotly/MapLibre, que ficavam pretos e estreitos quando
  criados numa aba escondida e, em alguns casos, sem os setores.) Os poligonos sao simplificados (~30 m) para manter o arquivo pequeno.
  Os graficos do Plotly tambem sao criados so quando a aba abre, com a largura real do cartao.
- **Versao web** (`python main.py publicar`): igual ao painel local, mas com plotly.js de CDN (~2,6 MB) e links para o relatorio e o codigo; ver README, "Publicar o painel e o relatorio na web".
- **Textos de leitura em cada cartao** dizem o que o grafico mostra, qual e a conclusao e o que nao se pode concluir (ex.: associacoes, nao causalidade).

## Limitacoes

- Os seletores e o tema alteram so o que ja esta no arquivo; nao ha entrada de dados nova (para avaliar um imovel use `python main.py prever`).
- O painel reflete a **ultima execucao** de cada comando; rode `python main.py painel` de novo depois de atualizar qualquer resultado.
- Os graficos usam as cores da paleta tanto no tema claro quanto no escuro (so o texto, as grades e a pagina mudam); a legibilidade foi conferida nos dois temas.
- Revisao visual feita no navegador do app (desktop, tema claro e escuro, largura de celular). Nao foi testado em varios navegadores.
- As etapas ate "terreno e texto" do grafico de evolucao do R2 vem da ultima execucao do `reg-geo` (anterior as variaveis de condominio);
  os dois ultimos modelos vem do `modelos-avancados` final.

## Proximos passos

1. Meta 9: relatorio automatico (texto + figuras) gerado a partir dos mesmos resultados.
2. Se necessario, uma aba "Avaliar imovel" (exigiria um servico local, pois o modelo roda em Python).
