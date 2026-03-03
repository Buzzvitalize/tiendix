# e-CF (Administración/Técnica)

## 1) Ejecutar `updatecf1.sql` en phpMyAdmin
1. Entrar a **cPanel > phpMyAdmin**.
2. Seleccionar la base de datos de Tiendix.
3. Pestaña **Importar**.
4. Cargar y ejecutar `updatecf1.sql`.
5. Verificar tablas: `ecf_company_config`, `ecf_document`, `ecf_events`.

## 2) Endpoints API
Base: sesión activa en el sistema.

- `GET /api/fe/config`
- `POST /api/fe/config`
- `POST /api/fe/issue`
- `GET /api/fe/doc/<id>`
- `POST /api/fe/doc/<id>/check`
- `GET /api/fe/doc/<id>/pdf`

## 3) Configuración por modo

### DIRECT_DGII
- `mode=DIRECT_DGII`
- Recomendado iniciar con `mock_sign=true`.
- `dgii_env`: `precert`, `cert`, `prod`.

### PSE_EXTERNAL
- `mode=PSE_EXTERNAL`
- Definir `pse_base_url` o `pse_issue_url` + `pse_status_url` (+ `pse_pdf_url` opcional).
- Credenciales: `pse_api_key` o `pse_client_id` + `pse_client_secret`.

### PSE_ECOSEA (stub)
- `mode=PSE_ECOSEA`
- Para pruebas internas.

## 4) Cron cPanel
### Comando recomendado
```bash
cd /home/USUARIO/apps/tiendix
source /home/USUARIO/virtualenv/tiendix/3.11/bin/activate
flask ecf_process_pending --limit 50
```

Frecuencia sugerida: cada **1 o 2 minutos**.

## 5) Variables de entorno PSE stub
```bash
ECOSEA_PSE_STUB_ENABLED=1
ECOSEA_PSE_STUB_SECRET=tu_secreto_largo
```
Enviar header:
```http
X-PSE-SECRET: tu_secreto_largo
```

## 6) Notas de seguridad
- Nunca exponer `cert_password` ni bytes del certificado en respuestas API.
- Preferir `cert_storage_mode=PATH` cuando exista filesystem seguro en servidor.
- Si usa `DB` (BLOB), asegurar respaldos frecuentes de MySQL y control de acceso.
- Revisar permisos de archivos y backups cifrados.
