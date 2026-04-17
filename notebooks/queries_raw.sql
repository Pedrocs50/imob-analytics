-- 1) Volume total coletado
SELECT COUNT(*) AS total_raw
FROM imoveis_raw;

-- 2) Volume por segmento (casas/apartamentos/imoveis/terrenos)
SELECT segmento, COUNT(*) AS total
FROM imoveis_raw
GROUP BY segmento
ORDER BY total DESC;

-- 3) Cobertura de scraping por faixa
SELECT
  segmento,
  preco_min_filtro,
  MIN(pagina) AS primeira_pagina,
  MAX(pagina) AS ultima_pagina,
  COUNT(*) AS paginas_coletadas
FROM progresso_scraping
GROUP BY segmento, preco_min_filtro
ORDER BY segmento, preco_min_filtro;

-- 4) Verificar se “terreno/lote” está vindo dentro de imoveis
SELECT COUNT(*) AS qtd_terreno_texto
FROM imoveis_raw
WHERE LOWER(endereco) LIKE '%terreno%'
   OR LOWER(endereco) LIKE '%lote%';

-- 5) Onde estão esses “terrenos” (por segmento)
SELECT segmento, COUNT(*) AS total
FROM imoveis_raw
WHERE LOWER(endereco) LIKE '%terreno%'
   OR LOWER(endereco) LIKE '%lote%'
GROUP BY segmento
ORDER BY total DESC;

-- 6) Qualidade dos campos (faltantes)
SELECT
  SUM(CASE WHEN preco IS NULL OR TRIM(preco) = '' OR preco = 'N/A' THEN 1 ELSE 0 END) AS sem_preco,
  SUM(CASE WHEN area IS NULL OR TRIM(area) = '' OR area = 'N/A' THEN 1 ELSE 0 END) AS sem_area,
  SUM(CASE WHEN endereco IS NULL OR TRIM(endereco) = '' OR endereco = 'N/A' THEN 1 ELSE 0 END) AS sem_endereco,
  COUNT(*) AS total
FROM imoveis_raw;

-- 7) Qualidade por segmento (percentual com preço/área)
SELECT
  segmento,
  COUNT(*) AS total,
  ROUND(100.0 * SUM(CASE WHEN preco IS NOT NULL AND TRIM(preco) <> '' AND preco <> 'N/A' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_com_preco,
  ROUND(100.0 * SUM(CASE WHEN area IS NOT NULL AND TRIM(area) <> '' AND area <> 'N/A' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_com_area
FROM imoveis_raw
GROUP BY segmento
ORDER BY total DESC;

-- 8) Estimativa de duplicados no bruto
SELECT
  COUNT(*) AS total_linhas,
  COUNT(DISTINCT COALESCE(endereco,'') || '|' || COALESCE(preco,'') || '|' || COALESCE(area,'')) AS unicos_est,
  COUNT(*) - COUNT(DISTINCT COALESCE(endereco,'') || '|' || COALESCE(preco,'') || '|' || COALESCE(area,'')) AS duplicados_est
FROM imoveis_raw;

-- 9) Densidade por página (amostra de desempenho da coleta)
SELECT
  segmento,
  preco_min_filtro,
  pagina,
  COUNT(*) AS anuncios_na_pagina
FROM imoveis_raw
GROUP BY segmento, preco_min_filtro, pagina
ORDER BY anuncios_na_pagina DESC
LIMIT 30;

-- 10) Amostra de anúncios de terreno/lote para evidência
SELECT
  id, segmento, preco_min_filtro, pagina, endereco, preco, area
FROM imoveis_raw
WHERE LOWER(endereco) LIKE '%terreno%'
   OR LOWER(endereco) LIKE '%lote%'
LIMIT 50;

-- 11) quantos registros ficou na tabela limpa
SELECT COUNT(*) AS total_processados FROM imoveis_processados;
SELECT tipo, COUNT(*) AS total FROM imoveis_processados GROUP BY tipo ORDER BY total DESC;

