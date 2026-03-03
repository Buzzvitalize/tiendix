# Guía para cliente: activar Facturación Electrónica (e-CF)

## Paso 1: Elegir plan e-CF
Solicite activación de e-CF para su compañía.

## Paso 2: Elegir modo
- **Directo DGII**: su sistema conecta directo a DGII.
- **Proveedor externo (PSE)**: su sistema envía al proveedor.
- **Mi PSE futuro (ECOSEA)**: modo de preparación (stub).

## Paso 3: Activación
Entre a `/fe/wizard` y complete:
- Company ID
- Modo
- Activar FE

## Paso 4: Emisión
El sistema emite e-CF y procesa estados automáticamente por cron.

## Paso 5: Seguimiento
Consulte la guía interna en `/fe/guia` y estados técnicos por API.

## Notas
- Si FE no está activado, su facturación normal (NCF) sigue igual.
- PDF e-CF se conserva cuando DGII/proveedor devuelve estado aceptado o condicional.
