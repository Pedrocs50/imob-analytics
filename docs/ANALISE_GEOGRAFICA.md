# Analise geografica e modelos com latitude e longitude

Data: 2026-10-02. Numeros completos em `reports/results/regressao_geo.md` (tabelas em
`reports/results/eda/regressao_geo_metricas.csv`); mapas `reports/figures/geo_mapa_*.png`.

```bash
python main.py reg-geo     # ~35 segundos
```

Implementacao: `src/pricing/geo.py`. Contorno de Jacarei: API do IBGE (`data/raw/ibge/jacarei_contorno.geojson`).

## O que foi feito

Ate aqui os modelos de precificacao nao usavam as colunas `lat` e `lon`, porque so ~48%
dos anuncios as tem (1.908 apartamentos, 4.974 casas, 6.882 no residencial). Agora elas
entram de tres formas, **sem vazamento** (validacao com holdout aleatorio, 5-fold e divisao
temporal):

1. **Superficie lat/lon** no modelo linear (x, y, x2, y2, x*y em km, padronizados).
2. **Preco dos vizinhos (kNN):** mediana do R$/m2 dos 15 anuncios mais proximos e
   distancia media a eles. No treino cada anuncio fica **de fora do proprio calculo**;
   no teste so os anuncios do treino contam. Sem coordenadas, usa-se a mediana do bairro e
   o indicador `tem_coord` vale 0.
3. **Gradient boosting** (`HistGradientBoostingRegressor`) com `lat`/`lon` crus e o bairro
   como categoria, para medir o valor da geografia sem impor forma funcional.

## Resultados (divisao temporal, todos os anuncios; R2 | MAE em R$/m2)

| Modelo | Apartamento | Casa | Residencial |
|---|---|---|---|
| OLS base (sem coordenadas) | 0,49 \| 1.012 | 0,58 \| 972 | 0,60 \| 1.011 |
| OLS + superficie lat/lon | 0,48 \| 1.022 | 0,59 \| 968 | 0,60 \| 1.010 |
| OLS + vizinhos (kNN) | 0,58 \| 885 | 0,61 \| 933 | 0,63 \| 961 |
| Gradient boosting sem coordenadas | 0,63 \| 820 | 0,72 \| 762 | 0,72 \| 812 |
| Gradient boosting com lat/lon | 0,67 \| 770 | 0,73 \| 759 | 0,73 \| 801 |
| Gradient boosting + vizinhos | 0,69 \| 752 | 0,72 \| 759 | 0,74 \| 791 |
| **Gradient boosting com lat/lon + vizinhos** | **0,69 \| 747** | **0,73 \| 756** | **0,74 \| 787** |

MAPE do melhor modelo: 12,0% (apartamento), 17,5% (casa), 16,5% (residencial), contra 17,0%,
22,3% e 21,1% do OLS base.

## O que os resultados mostram

1. **A geografia ajuda muito em apartamentos.** Entre os que tem coordenadas, o gradient
   boosting vai de R2 0,63 (sem) para 0,70 (com lat/lon), e o OLS de 0,49 para 0,62 so
   com o preco dos vizinhos. Em casas o ganho e pequeno (+0,01): o bairro e `em_condominio`
   ja capturam boa parte da localizacao.
2. **Uma superficie suave de lat/lon nao ajuda o modelo linear;** o que ajuda e o preco dos
   vizinhos. O preco do espaco e irregular (condominios, loteamentos), nao um gradiente liso.
3. **Achado importante: o modelo linear estava limitando o resultado.** Mesmo sem
   coordenadas, o gradient boosting sobe o R2 de 0,49 para 0,63 (apartamento) e de 0,58 para
   0,72 (casa), usando as mesmas variaveis. Ha interacoes e nao linearidades (por exemplo
   area x bairro) que a regressao linear nao ve. O erro medio cai de ~R$ 1.010 para ~R$ 750
   por m2 (-26%).
4. **O mapa de residuos** (`geo_mapa_residuos.png`) mostra que, sem coordenadas, os
   apartamentos tem erros agrupados no espaco (sub e superestimativas por regiao) e que o
   preco dos vizinhos praticamente elimina esse padrao.
5. **Mapa de precos** (`geo_mapa_preco_m2.png`): os maiores R$/m2 ficam no nordeste da area
   urbana (regiao de Villa Branca e Jardim California), nos dois segmentos.

## Qualidade das coordenadas

- Todas tem 6 casas decimais (nao ha truncamento) e 2 anuncios foram descartados por estarem
  fora de uma caixa em torno de Jacarei.
- 58% dos anuncios com coordenadas compartilham o ponto exato com outro, e o maior ponto tem
  71 anuncios: e o padrao esperado de **predios e condominios**, onde varias unidades tem a
  mesma posicao.

## Limitacoes (leia antes de citar os numeros)

- **So ~48% dos anuncios tem coordenadas.** Para os demais, a geografia entra so pelo bairro.
- **O preco dos vizinhos inclui outras unidades do mesmo predio.** Para um anuncio novo em um
  predio ja anunciado isso e legitimo, mas o ganho e menor em locais sem anuncios
  anteriores. A divisao temporal reduz, mas nao elimina, esse efeito.
- Os hiperparametros do gradient boosting **nao foram ajustados**; os valores acima sao um
  piso, nao um teto, mas tambem nao foram otimizados no conjunto de teste.
- Os resultados sao de um unico snapshot (marco/2026) e nao dizem nada sobre a evolucao dos
  precos no tempo.

## Atualizacao: coordenadas imputadas e setores do IBGE

**Imputacao das coordenadas ausentes.** Os 10.273 anuncios sem coordenadas tem todos o bairro, e 26% tem a
rua. As coordenadas ausentes agora sao preenchidas **so com coordenadas, nunca com o preco** (sem vazamento do
alvo): mediana da rua dentro do bairro (>= 2 anuncios com coordenada real) e, na falta, mediana do bairro
(>= 3). A dispersao tipica das coordenadas reais e de ~0,07 km dentro da rua e ~0,34 km dentro do bairro, da
ordem do tamanho de um setor. O indicador `coord_origem` (real, rua, bairro) entra nos modelos. Com isso 99%
dos anuncios passam a ter coordenada (so 33 a 47 por segmento ficam sem).

**Setor censitario do IBGE.** Cada anuncio e associado ao setor do Censo 2022 que o contem (juncao espacial
com os 544 setores de Jacarei) e o setor entra como categoria (setores com menos de 15 anuncios viram uma so).

Resultados (divisao temporal, todos os anuncios; R2 | MAE em R$/m2). Os modelos sem coordenadas deste quadro
diferem um pouco do quadro anterior porque as categorias raras do gradient boosting agora sao agrupadas:

| Modelo | Apartamento | Casa | Residencial |
|---|---|---|---|
| OLS base (sem coordenadas) | 0,49 \| 1.012 | 0,58 \| 972 | 0,60 \| 1.011 |
| Gradient boosting sem coordenadas | 0,62 \| 830 | 0,72 \| 768 | 0,73 \| 808 |
| Gradient boosting, lat/lon reais | 0,67 \| 767 | 0,73 \| 762 | 0,73 \| 800 |
| Gradient boosting, lat/lon imputadas | 0,68 \| 760 | 0,73 \| 760 | 0,74 \| 799 |
| Gradient boosting + setor IBGE | 0,68 \| 753 | 0,73 \| 754 | 0,74 \| 788 |
| **Imputadas + vizinhos + setor** | **0,70 \| 735** | **0,73 \| 759** | **0,74 \| 783** |

**O que isso mostra (e o que nao mostra):**

1. **Imputar pelo bairro ajuda pouco e so em apartamentos.** Nos apartamentos **sem coordenada real**, o gradient
   boosting com coordenadas imputadas tem R2 de 0,66, contra 0,63 sem coordenadas (+0,03); com coordenadas reais
   disponiveis o ganho some. Em casas e no residencial o ganho e nulo. Faz sentido: a coordenada do bairro nao
   traz informacao alem do proprio bairro, que o modelo ja usa. A imputacao serve para usar o mesmo pipeline em
   todos os anuncios, nao para criar informacao nova.
2. **O setor do IBGE soma pouco** (+0,01 em apartamentos com os vizinhos; +0,004 no residencial). Seu maior
   valor e analitico (mapa e comparacao entre areas) e como ponte para variaveis do Censo.
3. **O melhor modelo** (imputadas + vizinhos + setor) reduz o erro medio de ~R$ 1.010 para R$ 735 (apartamento),
   R$ 759 (casa) e R$ 783 (residencial) por m2.

## Mapa por setores do IBGE (`python main.py mapa-setores`)

- Estatico: `reports/figures/geo_mapa_setores.png`. **Interativo:** `reports/figures/mapa_setores_interativo.html`
  (abra no navegador; alterna apartamento e casa; ao passar o mouse mostra setor, numero de anuncios, mediana e
  quartis do R$/m2). Tabela de todos os setores: `reports/results/eda/setores_preco.csv`.
- Usa so anuncios com **coordenada real** (a imputada poria varios anuncios no mesmo ponto). Setores com menos de 5
  anuncios ficam em branco: 105 setores de apartamento e 280 de casa tem 5+ anuncios, de 198 e 404 com algum.
- R$/m2 mediano por setor: de ~R$ 3.000 a R$ 9.700 (apartamento) e de ~R$ 1.900 a R$ 8.400 (casa).
- Os poligonos grandes do noroeste e do sudoeste sao setores rurais ou de loteamentos fechados e dominam
  visualmente o mapa de casas; a malha urbana fica concentrada ao centro-nordeste.
- **Mostra nivel de preco, nao crescimento.** O crescimento por area exige varios snapshots do VivaReal.

## Proximos passos geograficos

- Variaveis do Censo 2022 por setor (renda, densidade, domicilios), que exigem outro download do IBGE.
- Coletar snapshots periodicos do VivaReal para medir crescimento de preco por setor.
