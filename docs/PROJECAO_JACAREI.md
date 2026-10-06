# Projecao de preco de Jacarei (precificacao x tendencia do FipeZAP)

Data: 2026-10-02. Numeros completos em `reports/results/projecao_jacarei.md` (tabelas em `reports/results/eda/projecao_*.csv`;
figuras `reports/figures/projecao_cenarios.png` e `reports/figures/projecao_premio_por_setor.png`).

```bash
python main.py projecao     # ~4 minutos (5 particoes x 2 modelos x 2 segmentos)
```

Implementacao: `src/pricing/projecao.py`. Depende dos parametros de `python main.py modelos-avancados` (lidos de
`reports/results/modelos_avancados/params.json` ou, se nao existir, do relatorio `modelos_avancados.md`).

## Pergunta

O VivaReal de Jacarei e uma fotografia de marco/2026 e o FipeZAP nao tem Jacarei. Como obter **quanto vale cada imovel e para onde o
R$/m2 deve ir**? Resposta em duas pecas, combinadas:

1. **Nivel (transversal):** o modelo de precificacao estima o R$/m2 de cada anuncio **sem ter visto o proprio anuncio** (previsoes
   fora da amostra, 5 particoes), com a media de LightGBM e HistGradientBoosting ajustados.
2. **Tendencia (temporal):** o ARIMA do FipeZAP de Sao Jose dos Campos (proxy mais proxima) da a variacao esperada do indice.

## Passos

1. **Valor estimado de mar/2026.** Previsao fora da amostra por anuncio (nenhum anuncio e previsto por um modelo que o viu). O
   erro relativo fora da amostra fornece os intervalos conformais do valor de cada imovel.
2. **Alinhamento no tempo.** O snapshot e de mar/2026 e o ultimo indice publicado e de ago/2026. O valor e levado ate ago/2026 com a
   variacao **observada** do indice de SJC (+4,4%; nacional +2,4%). Isso e um dado, nao previsao.
3. **Previsao.** Do ultimo indice em diante, aplica-se a previsao do ARIMA(0,2,3) de SJC (cenario central), com comparacao com o
   ARIMA nacional e com a tendencia dos ultimos 12 meses de SJC. Horizontes: 3, 6 e 12 meses.

## Resultados

Medianas de R$/m2:

| Segmento | Anuncios | Pedido | Estimado mar/2026 | Estimado hoje (ago/2026) | 3 meses | 6 meses | 12 meses | Intervalo 80% do imovel | Erro relativo mediano (fora da amostra) |
|---|---|---|---|---|---|---|---|---|---|
| Apartamento | 3.992 | 6.175 | 6.185 | 6.458 | 6.570 | 6.706 | 6.989 | +-17% | 8,1% |
| Casa | 10.254 | 4.375 | 4.402 | 4.597 | 4.676 | 4.774 | 4.974 | +-23% | 10,4% |

Cenarios de tendencia (variacao apos o ultimo indice publicado):

| Cenario | 3 meses | 6 meses | 12 meses (IC 95%) |
|---|---|---|---|
| ARIMA SJC (central) | +1,7% | +3,9% | +8,2% (-4,5% a +22,6%) |
| Tendencia de 12 meses SJC | +2,4% | +4,8% | +9,8% |
| ARIMA nacional | +1,5% | +3,1% | +6,2% (+0,3% a +12,4%) |

## Como ler

- **A mediana do pedido ficou muito perto da mediana estimada** (apartamento 6.175 x 6.185; casa 4.375 x 4.402): o modelo nao
  encontra, na media, anuncios sistematicamente caros ou baratos. A mediana do premio por setor e de -1,6% (apartamento) e -1,6% (casa).
- **A incerteza da tendencia e menor do que a do valor de cada imovel.** Em 12 meses o IC95 do ARIMA SJC e largo (-4,5% a +22,6%)
  porque `d = 2` amplia a incerteza; a faixa do ARIMA nacional e bem mais estreita. Os tres cenarios concordam na direcao (alta de 6 a 10%).
- **Erro de avaliacao de um imovel (+-17% a +-23% no intervalo de 80%)** domina a projecao: o valor de um imovel especifico
  nunca deve ser lido como ponto, e sim como faixa.
- **Mapa de premio por setor** (`projecao_premio_por_setor.png`): diferenca entre o preco pedido e o estimado. Os setores com poucos
  anuncios (5 a 10) mostram valores extremos (ex.: +32% em um setor de casas com 10 anuncios; -17% em um de apartamentos com 9).
  O mapa usa so setores com 5+ anuncios; so se deve interpretar os de 20+ (48 setores de apartamento e 125 de casa).
  Os dois poligonos grandes de area rural/periurbana tem muito poucos anuncios e cor forte: sao efeito de amostra pequena.

## Avaliar um imovel: `python main.py prever`

Implementacao: `src/pricing/prever.py`. Treina o mesmo conjunto (LightGBM + HistGradientBoosting, parametros do Optuna) em **todo o
segmento** e avalia um imovel novo; ~40 s.

```bash
python main.py prever --segmento casa --bairro "Loteamento Villa Branca" --area 150 --quartos 3 --banheiros 2 \
    --suites 1 --vagas 2 --terreno 250 --texto "casa com piscina e churrasqueira" --preco-pedido 750000
```

- **Entradas:** segmento (apartamento ou casa), bairro e area util sao obrigatorios; rua, comodos, vagas, terreno, condominio, tipo,
  lat/lon, texto do anuncio e preco pedido sao opcionais. Campo nao informado fica ausente, como nos anuncios reais.
- **Bairro:** aceito sem acento e em qualquer caixa. Se nao existir no segmento, o modelo avisa e usa so as outras informacoes.
- **Localizacao:** sem lat/lon, usa a mediana da rua no bairro (ou do bairro) para achar o setor e os vizinhos, como no treino.
- **Texto:** vira os mesmos indicadores `txt_*` do treino (precos e digitos ignorados).
- **Saida:** valor estimado hoje (R$/m2 e R$ total), intervalos de 80% e 90% e projecao central do ARIMA de SJC em 3, 6 e 12 meses.
  Se o preco pedido for informado, mostra a diferenca percentual em relacao ao estimado.
- **Limites:** os intervalos vem do teste temporal do conjunto (`modelos_avancados.md`); o imovel novo nunca entra no treino; a projecao
  e so o nivel central (sem a incerteza da tendencia).

## Premissas e limitacoes (para o relatorio)

1. **Jacarei acompanha SJC.** O FipeZAP nao cobre Jacarei; a variacao de SJC (ou do pais) e uma suposicao nao testavel hoje. So
   snapshots periodicos do VivaReal permitiriam medir a tendencia propria.
2. **Todos os imoveis variam igual** (indice unico). Nao ha tendencia por bairro ou setor.
3. **Precos pedidos, nao de venda.** O valor estimado e o preco pedido esperado; a negociacao nao esta modelada.
4. **Os dois blocos tem erros diferentes e nao foram combinados em um unico intervalo.** O intervalo conformal e do imovel (hoje); o
   IC95 do ARIMA e da tendencia. Uma faixa conjunta exigiria supor independencia entre os dois erros.
5. **Intervalos conformais** foram calibrados com os mesmos dados de treino do modelo (erro fora da amostra) e testados na divisao
   temporal em `docs/MODELOS_AVANCADOS.md` (cobertura 81% a 83% para 80% nominal).
6. Segmento **residencial** (apartamentos + casas) nao foi projetado; so apartamento e casa.
