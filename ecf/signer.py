"""Firma XML e-CF."""

import hashlib


def sign_xml(xml_unsigned: str, company_cfg) -> str:
    if not xml_unsigned:
        raise ValueError("xml_unsigned está vacío")

    mock_sign = bool(getattr(company_cfg, "mock_sign", True))
    if mock_sign:
        digest = hashlib.sha256(xml_unsigned.encode("utf-8")).hexdigest()
        return f"{xml_unsigned}\n<!-- MOCK SIGNED sha256:{digest} -->"

    # Modo real (placeholder): intentar usar librería si está disponible.
    try:
        import signxml  # type: ignore  # pragma: no cover

        raise RuntimeError(
            "Firma real no implementada aún (TODO XMLDSig/XAdES). "
            "Dependencia detectada: signxml."
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Firma real requerida pero no hay dependencia/configuración disponible. "
            "Active mock_sign o configure librería de firma XML en el entorno."
        ) from exc
