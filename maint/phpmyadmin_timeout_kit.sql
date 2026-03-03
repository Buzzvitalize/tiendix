-- Tiendix timeout kit for phpMyAdmin / MySQL-MariaDB
-- Uso: pegar por bloques en phpMyAdmin (SQL tab).
-- Objetivo: identificar cuellos de botella de DB que provocan Request Timeout.

-- 1) Contexto y límites actuales
SELECT NOW() AS now_ts;
SHOW VARIABLES LIKE 'version%';
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'wait_timeout';
SHOW VARIABLES LIKE 'interactive_timeout';
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';
SHOW VARIABLES LIKE 'tmp_table_size';
SHOW VARIABLES LIKE 'max_heap_table_size';

-- 2) Ver sesiones activas (si tienes permiso)
SHOW FULL PROCESSLIST;

-- 3) Detectar tablas grandes (estimado)
SELECT
  table_name,
  table_rows,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY (data_length + index_length) DESC
LIMIT 30;

-- 4) Verificar índices críticos para reportes/timeout paths
SHOW INDEX FROM invoice;
SHOW INDEX FROM invoice_item;
SHOW INDEX FROM quotation;
SHOW INDEX FROM `order`;

-- 5) Auditoría de consultas lentas en logs de app (tabla export_log útil para correlación de reportes)
SELECT id, created_at, user, formato, tipo, status, message, file_path
FROM export_log
ORDER BY id DESC
LIMIT 100;

-- 6) Conteos operativos para dimensionar rutas pesadas
SELECT 'invoice' AS tbl, COUNT(*) AS total FROM invoice
UNION ALL SELECT 'invoice_item', COUNT(*) FROM invoice_item
UNION ALL SELECT 'quotation', COUNT(*) FROM quotation
UNION ALL SELECT 'order', COUNT(*) FROM `order`
UNION ALL SELECT 'client', COUNT(*) FROM client
UNION ALL SELECT 'product', COUNT(*) FROM product;

-- 7) (Opcional) pruebas de selectividad en filtros de reportes
-- Ajusta fechas para tu ventana real.
EXPLAIN SELECT id, company_id, date, status
FROM invoice
WHERE company_id = 1
  AND date BETWEEN '2026-01-01' AND '2026-03-01'
  AND status = 'Pagada'
ORDER BY date DESC
LIMIT 50;

EXPLAIN SELECT category, SUM(quantity * unit_price) AS total
FROM invoice_item
WHERE company_id = 1
GROUP BY category;

-- 8) (Solo si detectas índice faltante y no existe en SHOW INDEX)
-- CREATE INDEX ix_invoice_company_date ON invoice(company_id, date);
-- CREATE INDEX ix_invoice_company_status_date ON invoice(company_id, status, date);
-- CREATE INDEX ix_invoice_item_company_category ON invoice_item(company_id, category);
-- CREATE INDEX ix_invoice_item_invoice_company ON invoice_item(invoice_id, company_id);
