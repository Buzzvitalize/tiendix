-- updatecf1.sql
-- FASE 2/6: Base de datos e-CF (sin cambios a tablas existentes del flujo NCF)
-- Compatible con MySQL/MariaDB en cPanel/phpMyAdmin.

SET NAMES utf8mb4;

-- =====================================================
-- 1) Configuración e-CF por compañía
-- Tabla real de compañías detectada: company_info(id)
-- =====================================================
CREATE TABLE IF NOT EXISTS ecf_company_config (
    company_id INT NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    mode ENUM('DIRECT_DGII','PSE_EXTERNAL','PSE_ECOSEA') NOT NULL DEFAULT 'DIRECT_DGII',

    -- DGII / firma
    dgii_env VARCHAR(20) NULL,
    mock_sign TINYINT(1) NOT NULL DEFAULT 1,
    cert_storage_mode ENUM('DB','PATH') NULL,
    cert_p12_bytes LONGBLOB NULL,
    cert_path VARCHAR(255) NULL,
    cert_password VARCHAR(255) NULL,
    token_cache TEXT NULL,
    token_expires_at DATETIME NULL,
    seq_enfcf_consumidor_last BIGINT NULL,
    seq_enfcf_credito_last BIGINT NULL,

    -- PSE_EXTERNAL
    pse_base_url VARCHAR(255) NULL,
    pse_issue_url VARCHAR(255) NULL,
    pse_status_url VARCHAR(255) NULL,
    pse_pdf_url VARCHAR(255) NULL,
    pse_api_key VARCHAR(255) NULL,
    pse_client_id VARCHAR(255) NULL,
    pse_client_secret VARCHAR(255) NULL,
    pse_webhook_secret VARCHAR(255) NULL,
    pse_env VARCHAR(50) NULL,

    -- Futuros flags
    settings_json JSON NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (company_id),
    CONSTRAINT fk_ecf_company_config_company
        FOREIGN KEY (company_id) REFERENCES company_info(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =====================================================
-- 2) Cola / trazabilidad de documentos e-CF
-- Nota de compatibilidad: se dejan índices en company_id/invoice_id y
-- NO se agrega FK contra invoice/company_info por posible desalineación de
-- tipos BIGINT UNSIGNED vs INTEGER existentes en instalaciones actuales.
-- =====================================================
CREATE TABLE IF NOT EXISTS ecf_document (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    invoice_id BIGINT UNSIGNED NOT NULL,

    backend_mode ENUM('DIRECT_DGII','PSE_EXTERNAL','PSE_ECOSEA') NOT NULL,
    tipo_ecf VARCHAR(5) NOT NULL,
    e_ncf VARCHAR(30) NOT NULL,

    status ENUM('DRAFT','SIGNED','SENT','PROCESSING','ACCEPTED','CONDITIONAL','REJECTED','ERROR')
        NOT NULL DEFAULT 'DRAFT',
    attempts INT UNSIGNED NOT NULL DEFAULT 0,
    next_retry_at DATETIME NULL,

    xml_unsigned LONGTEXT NULL,
    xml_signed LONGTEXT NULL,

    track_id VARCHAR(80) NULL,
    response_payload LONGTEXT NULL,
    error_message TEXT NULL,

    sent_at DATETIME NULL,
    last_check_at DATETIME NULL,
    accepted_at DATETIME NULL,

    pdf_blob LONGBLOB NULL,
    pdf_mime VARCHAR(50) NULL DEFAULT 'application/pdf',
    pdf_filename VARCHAR(255) NULL,
    pdf_size_bytes INT UNSIGNED NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_ecf_document_company_enfcf (company_id, e_ncf),
    KEY ix_ecf_document_track_id (track_id),
    KEY ix_ecf_document_status_next_retry (status, next_retry_at),
    KEY ix_ecf_document_invoice_id (invoice_id),
    KEY ix_ecf_document_backend_mode (backend_mode),
    KEY ix_ecf_document_company_id (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =====================================================
-- 3) Auditoría de eventos e-CF
-- =====================================================
CREATE TABLE IF NOT EXISTS ecf_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ecf_id BIGINT UNSIGNED NOT NULL,
    event_type ENUM('BUILD_XML','SIGN','AUTH','SEND','STATUS_CHECK','PDF','ERROR') NOT NULL,
    payload_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_ecf_events_ecf_id (ecf_id),
    CONSTRAINT fk_ecf_events_ecf
        FOREIGN KEY (ecf_id) REFERENCES ecf_document(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 4) Importante para esta fase
-- No se alteran tablas existentes (invoice, invoice_item, etc.).
-- Cualquier columna adicional en invoice (ej. ecf_id) se deja opcional para
-- una fase posterior.
-- =====================================================
