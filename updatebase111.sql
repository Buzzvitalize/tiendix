-- Performance hardening for high-traffic LSAPI environments.
-- Run once on production DB (MySQL/MariaDB) to reduce request pressure.

CREATE INDEX idx_notification_company_read_created
  ON notification (company_id, is_read, created_at);

CREATE INDEX idx_notification_company_message
  ON notification (company_id, message(191));

CREATE INDEX idx_product_stock_company_min_stock_stock
  ON product_stock (company_id, min_stock, stock);

CREATE INDEX idx_quotation_company_date_status
  ON quotation (company_id, date, status);

CREATE INDEX idx_order_company_date
  ON `order` (company_id, date);

CREATE INDEX idx_invoice_company_date_status
  ON invoice (company_id, date, status);
