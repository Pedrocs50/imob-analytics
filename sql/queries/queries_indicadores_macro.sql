-- ==========================================================
-- INDICADORES MACRO (BCB/IBGE/FGV) - CONSULTAS BASE
-- ==========================================================

-- 1) Conferir se a tabela existe e volume atual
SELECT COUNT(*) AS total_indicadores
FROM indicadores_macro;

-- 2) Cobertura por fonte e serie
SELECT
  fonte,
  codigo_serie,
  COALESCE(nome_serie, '(sem_nome)') AS nome_serie,
  frequencia,
  COUNT(*) AS total_pontos,
  MIN(data_ref) AS inicio,
  MAX(data_ref) AS fim
FROM indicadores_macro
GROUP BY fonte, codigo_serie, nome_serie, frequencia
ORDER BY fonte, codigo_serie;

-- 3) Ultimos valores por serie
SELECT
  fonte,
  codigo_serie,
  nome_serie,
  data_ref,
  valor,
  unidade
FROM indicadores_macro
ORDER BY data_ref DESC, fonte, codigo_serie
LIMIT 50;

-- 4) Template de insert manual (se quiser testar uma serie)
-- INSERT INTO indicadores_macro
--   (fonte, codigo_serie, nome_serie, data_ref, valor, unidade, frequencia)
-- VALUES
--   ('BCB', '432', 'SELIC Meta', '2025-01-01', 11.75, '% a.a.', 'M')
-- ON CONFLICT(fonte, codigo_serie, data_ref)
-- DO UPDATE SET
--   nome_serie = excluded.nome_serie,
--   valor = excluded.valor,
--   unidade = excluded.unidade,
--   frequencia = excluded.frequencia;
