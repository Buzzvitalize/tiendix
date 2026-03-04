# cPanel + LiteSpeed (LSAPI) tuning notes

Estas recomendaciones ayudan a reducir errores tipo `Reached max children process limit` en Setup Python App.

## Variables de entorno recomendadas

Configura estas variables en cPanel -> **Setup Python App** -> **Environment variables**:

- `LSAPI_CHILDREN=12` (sube gradualmente entre 12 y 20 según RAM/plan).
- `MAX_EXPORT_ROWS=50000` (o menor si el hosting es muy limitado).
- `PDF_LOCK_WAIT_SECONDS=30` (evita doble generación concurrente de PDF).
- `EAGER_PDF_ON_CREATE=0` (recomendado; generación diferida en background).

> Sugerencia: empieza con `LSAPI_CHILDREN=12`, monitorea CPU/RAM, luego sube a 16 o 20 si hay margen.

## Ajustes operativos sugeridos

1. Reinicia la app después de cambiar variables.
2. Prefiere exportaciones asíncronas para datasets grandes.
3. Deja que LiteSpeed/Nginx sirva `/generated_docs/...` estáticamente en producción cuando sea posible.
4. Programa cron para limpiezas de archivos temporales y logs si el disco es ajustado.

## Señales de saturación

- Mensajes repetidos `Reached max children process limit`.
- Aumento de timeouts en endpoints pesados (`/reportes`, exportes, PDFs).
- Cola de exportes creciendo sin drenarse.

## Checklist rápido

- [ ] `LSAPI_CHILDREN` ajustado a capacidad real del plan.
- [ ] `EAGER_PDF_ON_CREATE=0` en producción.
- [ ] `PDF_LOCK_WAIT_SECONDS=30`.
- [ ] Exportes no críticos usando modo async.
