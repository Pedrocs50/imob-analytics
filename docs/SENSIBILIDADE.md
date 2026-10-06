# Sensibilidade e relevancia das variaveis (meta 7)

Data: 2026-10-05. Numeros completos em `reports/results/sensibilidade.md` (tabelas `reports/results/eda/sens_*.csv`; figuras
`reports/figures/sensibilidade_grupos.png`, `sensibilidade_curvas.png`, `sensibilidade_bairros.png`).

```bash
python main.py sensibilidade     # ~2,5 minutos (precisa de modelos-avancados)
```

Implementacao: `src/pricing/sensibilidade.py`. Modelo analisado: o conjunto final (LightGBM + HistGradientBoosting com os parametros do Optuna).

## Tres leituras

1. **Relevancia por grupo de variaveis.** O grupo inteiro de colunas e embaralhado junto no teste temporal (5 repeticoes) e mede-se o
   aumento do erro medio (MAE). Grupos, e nao colunas, porque muitas variaveis dizem a mesma coisa (bairro, setor, coordenadas).
2. **Cenarios "e se?".** Para cada imovel do segmento, muda-se uma caracteristica e mantem-se o resto; mede-se a variacao da previsao.
3. **Imovel de referencia.** Um imovel tipico (medianas do segmento) e colocado em cada bairro (com 30+ anuncios) e se estima o R$/m2;
   mais curvas de R$/m2 pela area e pelo numero de suites.

## 1. O que mais pesa (aumento do MAE ao embaralhar o grupo, R$/m2)

| Grupo | Apartamento (MAE base 680) | Casa (MAE base 637) |
|---|---|---|
| Localizacao fina (coordenadas e vizinhos) | **360** (+53%) | 45 (+7%) |
| Bairro | 73 (+11%) | **237** (+37%) |
| Contexto (tamanho relativo, no de anuncios, distancia ao centro) | 78 (+11%) | 207 (+32%) |
| Tamanho (area util) | 109 (+16%) | 193 (+30%) |
| Condominio (taxa e tipo) | 32 (+5%) | 192 (+30%) |
| Texto do anuncio (150 colunas) | 141 (+21%) | 166 (+26%) |
| Terreno / area total | 38 (+6%) | 159 (+25%) |
| Comodos e vagas | 108 (+16%) | 150 (+24%) |
| Setor e Censo 2022 | 110 (+16%) | 85 (+13%) |

- **Apartamentos: a localizacao fina domina** (coordenadas e preco dos vizinhos, 53%). Predios proximos tem preco parecido.
- **Casas: bairro, contexto, tamanho e condominio (casa em condominio) pesam parecido**, e a localizacao fina pesa pouco: o bairro ja a
  resume. O terreno (+25%) e relevante, confirmando o ganho da etapa de novas variaveis.
- **O texto do anuncio pesa 21% a 26%**, mas o grupo tem 150 colunas: embaralhar muitas colunas de uma vez aumenta o efeito. A leitura
  correta e "o texto, em conjunto, traz informacao", nao que seja a variavel individual mais forte.
- **O Censo 2022** pesa 13% a 16% como grupo, mas e **em grande parte redundante** com a localizacao (ver `DIARIO_MODELAGEM.md`, secao 4).
- **Condominio nos apartamentos pesa pouco como grupo** (5%), embora a taxa tenha dado o maior ganho de R2 individual no experimento
  de variaveis (+0,018): o sinal que ela traz (padrao do predio) e parcialmente captado pela localizacao e pelo contexto.
- **Limite:** a permutacao subestima o grupo quando ha outro grupo correlacionado (ex.: bairro, setor e coordenadas). Os numeros nao
  somam 100% e nao devem ser lidos como "parcelas" do erro.

## 2. Cenarios "e se?" (mediana entre os imoveis; mantendo o resto)

| Cenario | Apartamento: R$/m2 | Apartamento: preco total | Casa: R$/m2 | Casa: preco total |
|---|---|---|---|---|
| +10% de area util | -3,1% | +R$ 24 mil | -3,2% | +R$ 40 mil |
| +1 suite | **+4,6%** | +R$ 20 mil | +0,9% | +R$ 6,7 mil |
| +1 vaga | +2,3% | +R$ 9,4 mil | +0,8% | +R$ 5,8 mil |
| +1 quarto | +0,1% | +R$ 0,3 mil | +0,8% | +R$ 5,9 mil |
| +1 banheiro | +0,9% | +R$ 3,4 mil | +0,9% | +R$ 6,5 mil |
| +R$ 100 na taxa de condominio | +1,1% | +R$ 4,0 mil | - | - |
| +50 m2 de terreno | - | - | **+4,2%** | +R$ 26,9 mil |
| Casa passa a ser em condominio | - | - | **+7,1%** | +R$ 43,5 mil |

- **Mais area aumenta o preco total, mas reduz o R$/m2** (-3% a cada +10%): economia de escala, esperada no mercado.
- **A suite e o diferencial dos apartamentos** (+4,6% no R$/m2; o quarto sozinho nao vale nada: +0,1%). Em casas as suites valem pouco (+0,9%).
- **Casa em condominio vale ~7% mais** que casa fora de condominio, mantendo o resto.
- O efeito de +R$ 100 de condominio positivo reflete padrao (predios mais caros cobram mais), **nao causalidade**.
- Os intervalos entre q25 e q75 sao largos (ex.: +1 suite no apartamento vai de +2,2% a +8,5%): o efeito depende do imovel e do bairro.
- **Importante:** sao associacoes aprendidas dos anuncios, nao efeitos causais. Uma suite "a mais" num mesmo imovel nao e o mesmo que
  comparar imoveis diferentes.

## 3. Bairro e curvas

- O mesmo imovel de referencia varia **de ~R$ 3.900 a ~R$ 8.400/m2** entre os bairros de apartamentos (Loteamento Villa Branca,
  Jardim Pereira do Amparo e Jardim Paraiba entre os mais caros; Jardim Novo Amanhecer, Jardim Yolanda e Bairro do Colonia entre os
  mais baratos) e de ~R$ 1.900 a ~R$ 6.100/m2 nas casas. Tabela completa em `sens_bairros.csv`.
- As curvas (`sensibilidade_curvas.png`) mostram o R$/m2 caindo com a area (nas casas, forte ate ~300 m2 e depois quase plano) e
  degraus por numero de suites nos apartamentos. Os degraus sao tipicos de modelos de arvores: a curva real e mais suave.
- Em casas o imovel de referencia nao e em condominio; por isso bairros "Condominio ..." aparecem com preco de casa **fora** de condominio
  naquele local, e a comparacao com a mediana do bairro (que e de casas em condominio) nao e direta.

## Limitacoes

- Sao analises do modelo, nao do mercado: refletem o que os precos pedidos e as variaveis disponiveis permitem aprender.
- Cenarios usam os proprios anuncios de treino (previsoes dentro da amostra); vale a diferenca entre previsoes, nao o nivel.
- A curva do imovel de referencia usa um unico bairro por segmento (o mais frequente).
- Nao ha analise por interacao (ex.: suite x bairro); poderia ser feita com dependencia parcial 2D ou valores de Shapley.
