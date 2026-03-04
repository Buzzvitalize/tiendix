# Timeout Runbook (cPanel / Flask)

## 1) Mapa de capas donde puede ocurrir timeout
1. Cliente → CDN/WAF (ej. Cloudflare)
2. Proxy web (Nginx/Apache)
3. WSGI (Passenger/Gunicorn)
4. Flask app
5. DB (MySQL/MariaDB)
6. Integraciones externas (SMTP/PSE/APIs)

## 2) Instrumentación incluida en la app
- `X-Request-ID` por request (acepta propagación entrante o genera uno nuevo).
- Logs estructurados JSON:
  - `request_start`
  - `request_end` (incluye `duration_ms`)
  - `request_fail`
  - `slow_query` (SQL lento)
- Umbrales configurables por entorno:
  - `SLOW_REQUEST_WARN_MS` (default `2000`)
  - `SLOW_REQUEST_ERROR_MS` (default `10000`)
  - `SLOW_QUERY_WARN_MS` (default `500`)

## 3) Endpoints de diagnóstico
- `GET /__health` → liveness básico.
- `GET /__ready` → readiness + check DB `SELECT 1`.
- `GET /__admin/profile/reportes` (solo admin + `ENABLE_ROUTE_PROFILING=1`) para perfilado cProfile de reportes.

## 4) Reproducción determinística
> Reemplaza `https://app.ecosea.do` por tu dominio.

```bash
curl -sS -o /dev/null -w "code=%{http_code} total=%{time_total}\n" https://app.ecosea.do/__health
curl -sS -o /dev/null -w "code=%{http_code} total=%{time_total}\n" https://app.ecosea.do/__ready
curl -sS -o /dev/null -w "code=%{http_code} total=%{time_total}\n" "https://app.ecosea.do/reportes?fecha_inicio=2026-01-01&fecha_fin=2026-03-01"
curl -sS -o /dev/null -w "code=%{http_code} total=%{time_total}\n" "https://app.ecosea.do/reportes/export?formato=csv"
```

## 5) Qué revisar en logs
Buscar request lentos y SQL lentos por `request_id`:

```bash
# ejemplo (si tienes acceso shell)
rg -n '"event": "request_end"|"event": "slow_query"|"event": "request_fail"' logs/app.log
```

Luego correlacionar por `request_id` para ver:
- ruta exacta,
- tiempo total,
- query SQL más lenta,
- si hubo excepción final.

## 6) Config recomendada (cPanel/Passenger/Gunicorn/Proxy)
Si tienes control de configuración, alinea timeouts:

### Apache
```apache
Timeout 120
ProxyTimeout 120
```

### Nginx
```nginx
proxy_connect_timeout 30s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

### Gunicorn
```bash
gunicorn app:app --workers 3 --threads 4 --timeout 120 --graceful-timeout 30
```

### Passenger (si aplica)
```apache
PassengerStartTimeout 120
PassengerAppEnv production
```

> Si en cPanel compartido no puedes cambiar proxy/WSGI, la estrategia correcta es app-level: paginación, streaming, colas async y fail-fast en integraciones externas.

## 7) Integraciones externas (PSE/SMTP)
### PSE
Nuevas variables:
- `PSE_HTTP_TIMEOUT_SEC` (default `20`)
- `PSE_HTTP_MAX_RETRIES` (default `2`)
- `PSE_HTTP_BACKOFF_SEC` (default `0.4`)

### SMTP
La app usa timeout explícito con `MAIL_CONNECT_TIMEOUT_SEC` y soporta aislamiento rápido con `MAIL_ENABLED=0`.

Prueba de aislamiento recomendada:
1. En cPanel > Setup Python App, define `MAIL_ENABLED=0`.
2. Reinicia la app.
3. Repite la operación que dispara timeout.
4. Si el timeout desaparece, el cuello está en SMTP/red saliente.
5. Rehabilita con `MAIL_ENABLED=1` tras ajustar proveedor SMTP (puerto TLS/SSL, firewall, credenciales).

## 8) Criterios de éxito post-fix
1. `request_end.duration_ms` p95 < 2s para listados comunes.
2. Exportes grandes no agotan memoria (streaming/async).
3. `slow_query` disminuye y se concentra en casos acotados.
4. `__ready` estable en 200 durante carga normal.

## 9) Rollback seguro
1. Revertir al commit anterior.
2. Reiniciar app en cPanel.
3. Verificar `__health` y `__ready`.
4. Mantener instrumentación en rollback si es posible para no perder trazabilidad.


## 10) Flujo específico para phpMyAdmin (sin acceso root)
Cuando solo tienes phpMyAdmin (sin shell ni MySQL root), usa `maint/phpmyadmin_timeout_kit.sql`.

Pasos recomendados:
1. Ejecuta bloques 1–4 para validar versión, límites y estado de índices.
2. Ejecuta bloque 6 para medir volumen real de tablas críticas.
3. Ejecuta los `EXPLAIN` del bloque 7 ajustando `company_id` y fechas.
4. Si `EXPLAIN` no usa índices esperados (`type=ALL`, `rows` muy alto), corrige índices desde migración o manualmente.
5. Cruza hallazgos con `request_id` y eventos `slow_query` en `logs/app.log`.

Señales de riesgo frecuentes en hosting cPanel/phpMyAdmin:
- `max_connections` bajo + muchas sesiones en `SHOW PROCESSLIST`.
- `tmp_table_size` muy bajo para agregaciones de reportes.
- `EXPLAIN` con full scan en `invoice`/`invoice_item` durante reportes.
- crecimiento de `invoice_item` sin mantenimiento de índices.
