import hashlib


def sign_xml(xml_payload: str, *, mock_mode: bool = True) -> str:
    """Firma XML en modo mock por defecto para compatibilidad cPanel."""
    if not xml_payload:
        return ""
    if mock_mode:
        digest = hashlib.sha256(xml_payload.encode("utf-8")).hexdigest()
        return f"{xml_payload}\n<!-- MOCK_SIGNATURE:{digest} -->"
    # Placeholder para firma real (XAdES/XMLDSig) cuando se habilite librería compatible.
    return xml_payload
