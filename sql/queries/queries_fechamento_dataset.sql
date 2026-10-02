-- ==========================================================
-- CHECKLIST DE FECHAMENTO DO DATASET (RAW + PROCESSADOS)
-- ==========================================================

-- 1) Volume bruto e volume limpo
SELECT COUNT(*) AS total_raw FROM imoveis_raw;
SELECT COUNT(*) AS total_processados FROM imoveis_processados;

-- 2) Cobertura por segmento/filtro (resumo)
SELECT
  segmento,
  preco_min_filtro,
  MIN(pagina) AS primeira_pagina,
  MAX(pagina) AS ultima_pagina,
  COUNT(*) AS paginas_marcadas,
  CASE
    WHEN MIN(pagina) = 1 AND COUNT(*) = MAX(pagina) THEN 'OK_CONTIGUO'
    ELSE 'ATENCAO_GAP_OU_INICIO_NAO_1'
  END AS status_cobertura
FROM progresso_scraping
GROUP BY segmento, preco_min_filtro
ORDER BY segmento, preco_min_filtro;

-- 3) Quais paginas faltam por segmento/filtro (se houver gap)
WITH RECURSIVE paginas_esperadas AS (
  SELECT
    segmento,
    preco_min_filtro,
    1 AS pagina,
    MAX(pagina) AS max_pagina
  FROM progresso_scraping
  GROUP BY segmento, preco_min_filtro

  UNION ALL

  SELECT
    segmento,
    preco_min_filtro,
    pagina + 1,
    max_pagina
  FROM paginas_esperadas
  WHERE pagina < max_pagina
)
SELECT
  pe.segmento,
  pe.preco_min_filtro,
  pe.pagina AS pagina_faltante
FROM paginas_esperadas pe
LEFT JOIN progresso_scraping ps
  ON ps.segmento = pe.segmento
 AND ps.preco_min_filtro = pe.preco_min_filtro
 AND ps.pagina = pe.pagina
WHERE ps.id IS NULL
ORDER BY pe.segmento, pe.preco_min_filtro, pe.pagina;

-- 4) Distribuicao da base bruta por segmento
SELECT
  segmento,
  COUNT(*) AS total
FROM imoveis_raw
GROUP BY segmento
ORDER BY total DESC;

-- 5) Evidencia: terrenos/lotes dentro do segmento "imoveis"
SELECT
  segmento,
  COUNT(*) AS total_terreno_ou_lote
FROM imoveis_raw
WHERE LOWER(endereco) LIKE '%terreno%'
   OR LOWER(endereco) LIKE '%lote%'
GROUP BY segmento
ORDER BY total_terreno_ou_lote DESC;

-- 6) Qualidade da base processada
SELECT
  SUM(CASE WHEN preco_venda IS NULL THEN 1 ELSE 0 END) AS null_preco_venda,
  SUM(CASE WHEN area_m2 IS NULL THEN 1 ELSE 0 END) AS null_area_m2,
  SUM(CASE WHEN preco_m2 IS NULL THEN 1 ELSE 0 END) AS null_preco_m2,
  SUM(CASE WHEN area_m2 <= 0 THEN 1 ELSE 0 END) AS area_m2_invalida,
  COUNT(*) AS total_processados
FROM imoveis_processados;

-- 7) Distribuicao por tipo (base processada)
SELECT
  tipo,
  COUNT(*) AS total,
  ROUND(AVG(preco_m2), 2) AS preco_m2_medio
FROM imoveis_processados
GROUP BY tipo
ORDER BY total DESC;

-- 8) Faixas de preco_m2 para detectar outliers grosseiros
SELECT
  SUM(CASE WHEN preco_m2 < 500 THEN 1 ELSE 0 END) AS abaixo_500,
  SUM(CASE WHEN preco_m2 BETWEEN 500 AND 30000 THEN 1 ELSE 0 END) AS entre_500_e_30000,
  SUM(CASE WHEN preco_m2 > 30000 THEN 1 ELSE 0 END) AS acima_30000
FROM imoveis_processados;
