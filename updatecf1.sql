-- updatecf1.sql
-- Módulo e-CF: configuración por compañía + cola/documentos + blobs PDF

CREATE TABLE IF NOT EXISTS ecf_company_config (
    company_id INT NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    mode VARCHAR(30) NOT NULL DEFAULT 'DIRECT_DGII',
    settings_json JSON NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id),
    CONSTRAINT fk_ecf_company_config_company
        FOREIGN KEY (company_id) REFERENCES company_info(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ecf_documents (
    id BIGINT NOT NULL AUTO_INCREMENT,
    company_id INT NOT NULL,
    invoice_id INT NULL,
    backend_mode VARCHAR(30) NOT NULL,
    ecf_number VARCHAR(30) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    xml_payload LONGTEXT NULL,
    xml_signed LONGTEXT NULL,
    provider_track_id VARCHAR(120) NULL,
    dgii_track_id VARCHAR(120) NULL,
    response_payload LONGTEXT NULL,
    error_message TEXT NULL,
    attempts INT NOT NULL DEFAULT 0,
    next_retry_at DATETIME NULL,
    issued_at DATETIME NULL,
    accepted_at DATETIME NULL,
    pdf_blob LONGBLOB NULL,
    pdf_filename VARCHAR(255) NULL,
    pdf_mime VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_ecf_documents_company_status_created (company_id, status, created_at),
    KEY ix_ecf_documents_invoice_id (invoice_id),
    CONSTRAINT fk_ecf_documents_company
        FOREIGN KEY (company_id) REFERENCES company_info(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ecf_documents_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Columnas opcionales de trazabilidad en factura tradicional (no rompen flujo existente)
ALTER TABLE invoice
    ADD COLUMN ecf_enabled_snapshot TINYINT(1) NULL,
    ADD COLUMN ecf_mode_snapshot VARCHAR(30) NULL,
    ADD COLUMN ecf_document_id BIGINT NULL,
    ADD KEY ix_invoice_ecf_document_id (ecf_document_id),
    ADD CONSTRAINT fk_invoice_ecf_document
        FOREIGN KEY (ecf_document_id) REFERENCES ecf_documents(id)
        ON DELETE SET NULL ON UPDATE CASCADE;
