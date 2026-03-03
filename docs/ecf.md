# Módulo DGII e-CF (Admin/Técnica)

## Resumen
Se agregó un módulo e-CF desacoplado en `ecf/` con 3 modos por compañía:

1. `DIRECT_DGII`
2. `PSE_EXTERNAL`
3. `PSE_ECOSEA` (stub futuro)

El flujo tradicional NCF sigue intacto por defecto. Solo se usa e-CF si se activa por compañía en `ecf_company_config`.

## Blueprints
- `ecf_api_bp`: `/api/fe/*`
- `ecf_admin_bp`: `/fe/*`
- `pse_gateway_bp`: `/pse/ecosea/*` (stub)

## Operación en cPanel
Sin workers permanentes. Usar Cron:

```bash
cd /home/usuario/app
source /home/usuario/virtualenv/app/3.11/bin/activate
flask ecf_process_pending --limit 50
```

Frecuencia recomendada: cada 1-5 minutos.

## CLI
Comando registrado:

```bash
flask ecf_process_pending --limit 50
```

## API mínima
### Configurar compañía
`POST /api/fe/configure`

```json
{
  "company_id": 1,
  "enabled": true,
  "mode": "DIRECT_DGII",
  "settings": {
    "mock_sign": true,
    "dgii_submit_url": ""
  }
}
```

### Encolar emisión
`POST /api/fe/emit`

```json
{
  "company_id": 1,
  "invoice_id": 1201,
  "xml_payload": "<eCF>...</eCF>"
}
```

### Estado
`GET /api/fe/status/<doc_id>`

## Firma XML
Archivo `ecf/signer.py` incluye firma mock por defecto para compatibilidad con cPanel compartido.
- `mock_sign=true`: agrega huella SHA256 en comentario XML.
- Implementación real se deja preparada para fase futura.

## Persistencia PDF
`ecf_documents.pdf_blob` se llena **solo** en estados `ACCEPTED` o `CONDITIONAL`.

## Integración con facturación actual
No se reemplazaron rutas/funciones existentes de NCF tradicional.
La integración recomendada en siguiente fase es invocar `EcfService.enqueue_invoice(...)` tras crear factura cuando FE esté activa.
