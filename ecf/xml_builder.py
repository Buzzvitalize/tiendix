"""Builder XML interno para e-CF (fase inicial)."""

from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring


def build_ecf_xml(invoice, items, company_cfg, tipo_ecf: str) -> str:
    """Construye XML mínimo interno para e-CF.

    TODO: adaptar nodos al esquema DGII oficial cuando se integre modo real.
    """
    if not invoice:
        raise ValueError("Invoice requerido para construir XML e-CF")
    if not items:
        raise ValueError("Invoice sin items; no se puede construir XML e-CF")
    if not tipo_ecf:
        raise ValueError("tipo_ecf es obligatorio")

    emisor_rnc = _extract_emisor_rnc(invoice, company_cfg)
    if not emisor_rnc:
        raise ValueError("No se encontró RNC del emisor (company_info.rnc)")

    receptor_id = ((getattr(invoice.client, "identifier", None) or "").strip() if getattr(invoice, "client", None) else "")
    fecha = (getattr(invoice, "date", None) or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")
    e_ncf = (getattr(invoice, "ncf", None) or "").strip()
    if not e_ncf:
        raise ValueError("Invoice.ncf es obligatorio para construir XML e-CF")

    root = Element("eCF")
    encabezado = SubElement(root, "Encabezado")
    SubElement(encabezado, "TipoECF").text = str(tipo_ecf)
    SubElement(encabezado, "ENCF").text = e_ncf
    SubElement(encabezado, "FechaEmision").text = fecha

    emisor = SubElement(encabezado, "Emisor")
    SubElement(emisor, "RNCEmisor").text = emisor_rnc

    receptor = SubElement(encabezado, "Receptor")
    SubElement(receptor, "Identificador").text = receptor_id

    montos = SubElement(root, "Montos")
    SubElement(montos, "Subtotal").text = _fmt_num(getattr(invoice, "subtotal", 0))
    SubElement(montos, "ITBIS").text = _fmt_num(getattr(invoice, "itbis", 0))
    SubElement(montos, "Total").text = _fmt_num(getattr(invoice, "total", 0))

    detalle = SubElement(root, "DetalleItems")
    for idx, item in enumerate(items, start=1):
        if not getattr(item, "product_name", None):
            raise ValueError(f"Item #{idx} sin descripción (product_name)")
        linea = SubElement(detalle, "Item")
        SubElement(linea, "Linea").text = str(idx)
        SubElement(linea, "Descripcion").text = str(item.product_name)
        SubElement(linea, "Cantidad").text = _fmt_num(getattr(item, "quantity", 0))
        SubElement(linea, "PrecioUnitario").text = _fmt_num(getattr(item, "unit_price", 0))
        SubElement(linea, "TieneITBIS").text = "1" if bool(getattr(item, "has_itbis", False)) else "0"

    return tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def _extract_emisor_rnc(invoice, company_cfg) -> str:
    company = getattr(invoice, "company", None)
    if company and getattr(company, "rnc", None):
        return str(company.rnc).strip()
    cfg_rnc = getattr(company_cfg, "settings_json", None)
    if isinstance(cfg_rnc, dict):
        return str(cfg_rnc.get("emisor_rnc") or "").strip()
    return ""


def _fmt_num(value) -> str:
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "0.00"
