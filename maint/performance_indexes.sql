-- Performance indexes for Tiendix (MySQL 8+)
-- Idempotent style using IF NOT EXISTS.

CREATE INDEX IF NOT EXISTS ix_invoice_company_date_status ON invoice (company_id, date, status);
CREATE INDEX IF NOT EXISTS ix_invoice_company_client_date ON invoice (company_id, client_id, date);
CREATE INDEX IF NOT EXISTS ix_invoice_order_id ON invoice (order_id);

CREATE INDEX IF NOT EXISTS ix_order_company_date ON `order` (company_id, date);
CREATE INDEX IF NOT EXISTS ix_order_company_client_date ON `order` (company_id, client_id, date);
CREATE INDEX IF NOT EXISTS ix_order_quotation_id ON `order` (quotation_id);

CREATE INDEX IF NOT EXISTS ix_quotation_company_date_status ON quotation (company_id, date, status);
CREATE INDEX IF NOT EXISTS ix_quotation_company_valid_until ON quotation (company_id, valid_until);

CREATE INDEX IF NOT EXISTS ix_invoice_item_invoice_id ON invoice_item (invoice_id);
CREATE INDEX IF NOT EXISTS ix_order_item_order_id ON order_item (order_id);
CREATE INDEX IF NOT EXISTS ix_quotation_item_quotation_id ON quotation_item (quotation_id);

CREATE INDEX IF NOT EXISTS ix_payment_invoice_date ON payment (invoice_id, date);
CREATE INDEX IF NOT EXISTS ix_notification_company_read_created ON notification (company_id, is_read, created_at);
