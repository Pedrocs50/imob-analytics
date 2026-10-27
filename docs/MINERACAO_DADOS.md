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
