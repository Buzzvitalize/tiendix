# Guía Cliente: Facturación Electrónica (e-CF)

## 1) Requisitos previos
- Estar habilitado como emisor electrónico ante DGII **o** usar proveedor (PSE).
- Tener certificado digital (.p12) si aplica su modalidad.
- Tener secuencias e-NCF disponibles.

## 2) Elegir modo
- **Directo DGII**: para empresas ya listas con integración directa.
- **Proveedor (PSE)**: opción más simple, el proveedor gestiona gran parte del flujo.

## 3) Activar en el sistema
Configurar en `POST /api/fe/config`:
- `enabled`
- `mode`
- `dgii_env` / parámetros PSE
- secuencias y settings opcionales

## 4) Certificado
### Opción DB
- `cert_storage_mode=DB`
- enviar `p12_base64`

### Opción PATH
- `cert_storage_mode=PATH`
- enviar `cert_path` (ruta segura en servidor)

## 5) Emitir primera factura
1. Emitir: `POST /api/fe/issue` con `invoice_id`.
2. Revisar estado: `GET /api/fe/doc/<id>`.
3. Forzar check: `POST /api/fe/doc/<id>/check`.
4. Descargar PDF: `GET /api/fe/doc/<id>/pdf` cuando esté disponible.

## 6) Estados y qué hacer
- `PROCESSING`: esperar siguiente chequeo.
- `ACCEPTED` / `CONDITIONAL`: documento procesado; PDF disponible.
- `REJECTED`: corregir datos fiscales y reemitir.
- `ERROR`: validar configuración y credenciales.

## 7) Seguridad
- No compartir `cert_password` ni claves API.
- Cambiar secretos periódicamente.
- Mantener copias de seguridad.

## 8) Ejemplos curl
### Configurar
```bash
curl -X POST "$BASE/api/fe/config" \
  -H "Content-Type: application/json" \
  -b cookie.txt \
  -d '{
    "enabled": true,
    "mode": "DIRECT_DGII",
    "mock_sign": true,
    "dgii_env": "precert"
  }'
```

### Emitir
```bash
curl -X POST "$BASE/api/fe/issue" \
  -H "Content-Type: application/json" \
  -b cookie.txt \
  -d '{"invoice_id": 123}'
```

### Revisar documento
```bash
curl -X GET "$BASE/api/fe/doc/1" -b cookie.txt
curl -X POST "$BASE/api/fe/doc/1/check" -b cookie.txt
curl -X GET "$BASE/api/fe/doc/1/pdf" -b cookie.txt -o ecf-1.pdf
```
