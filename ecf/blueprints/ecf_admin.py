from flask import Blueprint, Response, request, session

from ecf.repository import get_company_config_safe


ecf_admin_bp = Blueprint("ecf_admin_bp", __name__, url_prefix="/fe")


def _resolve_company_id() -> int:
    role = (session.get("role") or "").strip().lower()
    session_company = session.get("company_id")
    q_company = request.args.get("company_id")
    if role == "admin" and q_company:
        return int(q_company)
    if session_company is not None:
        return int(session_company)
    raise ValueError("company_id no disponible en sesión")


@ecf_admin_bp.get("/guia")
def fe_guia():
    company_id = _resolve_company_id()
    cfg = get_company_config_safe(company_id) or {}
    enabled = bool(cfg.get("enabled"))
    mode = cfg.get("mode") or "DIRECT_DGII"

    html = f"""
    <html><head><title>Guía e-CF</title></head><body style='font-family:Arial,sans-serif;max-width:980px;margin:2rem auto;'>
      <h1>Guía de Facturación Electrónica (e-CF)</h1>
      <p><strong>Compañía:</strong> {company_id} | <strong>FE activa:</strong> {'Sí' if enabled else 'No'} | <strong>Modo:</strong> {mode}</p>
      <h2>Modos disponibles</h2>
      <ul>
        <li><strong>DIRECT_DGII:</strong> emisión directa a DGII (stub/real).</li>
        <li><strong>PSE_EXTERNAL:</strong> envío a proveedor externo por API.</li>
        <li><strong>PSE_ECOSEA:</strong> stub futuro para PSE propio.</li>
      </ul>
      <h2>Checklist: qué necesito</h2>
      <ul>
        <li>RNC emisor y secuencias iniciales.</li>
        <li>Definir modo e-CF por compañía.</li>
        <li>Si aplica certificado: DB o PATH + password.</li>
        <li>Si usa PSE: URLs y credenciales API.</li>
      </ul>
      <h2>Pasos de configuración</h2>
      <ol>
        <li>Configurar por API <code>POST /api/fe/config</code>.</li>
        <li>Emitir primera factura con <code>POST /api/fe/issue</code>.</li>
        <li>Consultar estado con <code>GET /api/fe/doc/&lt;id&gt;</code> y <code>POST /api/fe/doc/&lt;id&gt;/check</code>.</li>
      </ol>
      <h2>Estados</h2>
      <p>DRAFT, SIGNED, SENT, PROCESSING, ACCEPTED, CONDITIONAL, REJECTED, ERROR.</p>
      <h2>Seguridad del certificado</h2>
      <p>Evite exponer <code>cert_password</code> y bytes del certificado. Use acceso restringido en cPanel.</p>
    </body></html>
    """
    return Response(html, mimetype="text/html")
