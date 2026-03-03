from models import db


class EcfCompanyConfig(db.Model):
    __tablename__ = "ecf_company_config"

    company_id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    mode = db.Column(db.String(30), nullable=False, default="DIRECT_DGII")

    dgii_env = db.Column(db.String(20))
    mock_sign = db.Column(db.Boolean, nullable=False, default=True)
    cert_storage_mode = db.Column(db.String(10))
    cert_p12_bytes = db.Column(db.LargeBinary)
    cert_path = db.Column(db.String(255))
    cert_password = db.Column(db.String(255))
    token_cache = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    seq_enfcf_consumidor_last = db.Column(db.BigInteger)
    seq_enfcf_credito_last = db.Column(db.BigInteger)

    pse_base_url = db.Column(db.String(255))
    pse_issue_url = db.Column(db.String(255))
    pse_status_url = db.Column(db.String(255))
    pse_pdf_url = db.Column(db.String(255))
    pse_api_key = db.Column(db.String(255))
    pse_client_id = db.Column(db.String(255))
    pse_client_secret = db.Column(db.String(255))
    pse_webhook_secret = db.Column(db.String(255))
    pse_env = db.Column(db.String(50))

    settings_json = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        server_onupdate=db.func.current_timestamp(),
    )

    def to_safe_dict(self) -> dict:
        """Representación sin secretos/sensibles."""
        return {
            "company_id": self.company_id,
            "enabled": bool(self.enabled),
            "mode": self.mode,
            "dgii_env": self.dgii_env,
            "mock_sign": bool(self.mock_sign),
            "cert_storage_mode": self.cert_storage_mode,
            "cert_path": self.cert_path,
            "token_expires_at": self.token_expires_at,
            "seq_enfcf_consumidor_last": self.seq_enfcf_consumidor_last,
            "seq_enfcf_credito_last": self.seq_enfcf_credito_last,
            "pse_base_url": self.pse_base_url,
            "pse_issue_url": self.pse_issue_url,
            "pse_status_url": self.pse_status_url,
            "pse_pdf_url": self.pse_pdf_url,
            "pse_client_id": self.pse_client_id,
            "pse_env": self.pse_env,
            "settings_json": self.settings_json,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class EcfDocument(db.Model):
    __tablename__ = "ecf_document"

    id = db.Column(db.BigInteger().with_variant(db.BigInteger, "mysql"), primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, nullable=False, index=True)
    invoice_id = db.Column(db.Integer, nullable=False, index=True)

    backend_mode = db.Column(db.String(30), nullable=False, index=True)
    tipo_ecf = db.Column(db.String(5), nullable=False)
    e_ncf = db.Column(db.String(30), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="DRAFT", index=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    next_retry_at = db.Column(db.DateTime, index=True)

    xml_unsigned = db.Column(db.Text)
    xml_signed = db.Column(db.Text)

    track_id = db.Column(db.String(80), index=True)
    response_payload = db.Column(db.Text)
    error_message = db.Column(db.Text)

    sent_at = db.Column(db.DateTime)
    last_check_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)

    pdf_blob = db.Column(db.LargeBinary)
    pdf_mime = db.Column(db.String(50), default="application/pdf")
    pdf_filename = db.Column(db.String(255))
    pdf_size_bytes = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        server_onupdate=db.func.current_timestamp(),
    )

    events = db.relationship("EcfEvent", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("company_id", "e_ncf", name="uq_ecf_document_company_enfcf"),
    )


class EcfEvent(db.Model):
    __tablename__ = "ecf_events"

    id = db.Column(db.BigInteger().with_variant(db.BigInteger, "mysql"), primary_key=True, autoincrement=True)
    ecf_id = db.Column(db.BigInteger, db.ForeignKey("ecf_document.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = db.Column(db.String(20), nullable=False)
    payload_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

    document = db.relationship("EcfDocument", back_populates="events")
