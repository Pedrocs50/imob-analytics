# Mineracao de dados dos anuncios (VivaReal de Jacarei)

Data: 2026-10-26. Numeros completos em `reports/results/mineracao.md` (tabelas em `reports/results/mineracao/`).

```bash
python main.py vivareal-prep     # limpeza (pre-requisito)
python main.py mineracao         # segundos
```

Implementacao: `src/pricing/mineracao.py`. Sao leituras **descritivas** (associacoes, nao efeitos causais).

## Etapas (coleta -> limpeza -> mineracao -> avaliacao)

| Etapa | Onde | O que faz |
|---|---|---|
| Coleta | base do orientador (`data/raw/vivareal_jacarei/*.db`, 23.128 anuncios de marco/2026); coletor proprio em `src/scraper.py` (ver `docs/COLETA_ANUNCIOS.md`) | preco, localizacao, areas, comodos, vagas, condominio, IPTU, comodidades e texto |
| Limpeza | `vivareal-prep` (`src/vivareal/`) | duplicatas por id (1.984), condominio/IPTU implausiveis -> ausente; 3.992 apartamentos, 10.254 casas |
| Mineracao | `mineracao` | correlacao de Spearman com R$/m2; K-means (k=4) por area, quartos, suites e vagas; termos do anuncio contra o preco do bairro |
| Avaliacao | `modelos-avancados`, `sensibilidade` | modelos de gradient boosting com validacao temporal (R2 0,73 apartamento / 0,80 casa) e importancia por grupo de variaveis |

## Principais achados

- **Casas:** a taxa de condominio e a caracteristica mais associada ao R$/m2 (Spearman 0,50), seguida de numero de comodidades (0,34) e suites (0,29).
- **Apartamentos:** suites (0,32), banheiros (0,26) e vagas (0,25).
- **Grupos (K-means):** casas de ~250 m2 com 4 vagas tem R$/m2 mediano ~5.360, contra ~4.300 nas de ~90 m2; apartamentos de 2 quartos com suite chegam a ~7.080.
- **Termos do anuncio (efeito sobre o preco relativo ao bairro):** em casas, "condominio" (+15,7%), "salao de festas" (+11,5%), "quadra" (+11,1%) e "portaria" (+11,0%).
  Em apartamentos, "gourmet" (+7,9%), "varanda" (+6,6%) e "academia" (+5,6%).

## Limites

- Termos como "vaga", "aviso previo" e "valores" saem com sinal negativo por serem texto padrao do anuncio, sem significado: ler so os termos de caracteristicas.
- "Salao de festas" e "quadra" marcam casas em condominio fechado: o efeito e do padrao do imovel, nao da palavra.
- Precos pedidos, retrato de um unico mes, viés de sobrevivencia.

## Mineracao avancada (`python main.py mineracao-avancada`, ~15 s)

Implementacao: `src/pricing/mineracao_avancada.py`. Relatorio: `reports/results/mineracao_avancada.md`; figuras `reports/figures/mineracao_*.png`.
A pergunta: **o que faz um imovel custar mais que os vizinhos do mesmo bairro?** O R$/m2 de cada anuncio e dividido pela mediana do proprio bairro.

| Tecnica | Resultado | Leitura honesta |
|---|---|---|
| Regras de associacao (ate 3 caracteristicas; suporte, confianca, lift) | Casas: piscina + seguranca + armarios planejados tem 56% de chance de estar no terco mais caro do bairro (base 33%, lift 1,7) | Em dados **nao vistos** o lift medio cai de 1,67 para 1,50 (casas) e de 1,73 para 1,52 (apartamentos): se sustenta. Sao marcadores de padrao de condominio, nao efeito causal |
| Arvore de decisao (profundidade 3) | Casas: acerta 71,6% contra 66,7% de quem chuta a classe mais comum (AUC 0,73) | Sinal real e modesto; basicamente casas pequenas tem R$/m2 alto. **Apartamentos: 66,3% contra 66,7% (AUC 0,59), nao aprendeu nada alem do acaso: nao apresentar como achado** |
| Escolha de k (silhueta) | Casas: k=4 tem a pior silhueta (0,25), melhor k=2 (0,40). Apartamentos: k=4 0,59, melhor k=6 0,63 | Os perfis de casas se sobrepoem: apresentar como perfis tipicos, nao como segmentos distintos. Estabilidade entre sementes: ARI 0,98 e 1,00 |
| Validacao da correlacao | IC95% por bootstrap e duas metades aleatorias | Resultados estaveis (ex.: condominio nas casas 0,48 a 0,52) |
| Imoveis fora da curva (LightGBM, previsao fora da amostra) | 86% dos apartamentos e 73% das casas ficam a ate 20% do preco esperado; 3,4% (apto) e 8,1% (casa) estao mais de 30% acima; 1,0% e 4,2% mais de 30% abaixo | Sao **candidatos a revisar** (erro de cadastro, sobrepreco, oportunidade): o modelo nao ve estado, acabamento nem fotos |
| Tempo no ar x preco relativo ao bairro | Spearman -0,06 (casas) e -0,03 (apartamentos); anuncios com mais de 2 anos ficam ~6% abaixo do bairro | Sinal fraco; anuncio antigo pode estar desatualizado. Nao confirma "anuncio caro demora mais" |
