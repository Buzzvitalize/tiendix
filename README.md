# Tiendix - Tu negocio, tu control, tu Tiendix

Simple Flask application for managing quotations, orders and invoices.

Key features:

- Company logo upload used across all generated PDFs
- QR codes on documents linking back to their online copies
- Responsive TailwindCSS layout with sidebar navigation
- Multi-tenant architecture isolating data per company
- Local RNC catalogue (`data/DGII_RNC.TXT`) auto-completes company names when entering tax IDs
- PDFs generated with FPDF using a simple modern template for quotations, orders and invoices
- Optional document notes stored with quotations and carried over to orders and invoices, appearing on generated PDFs
- PDF exports display document numbers and invoice type (Consumidor Final o Crédito Fiscal)
- Quotation form reuses existing clients and products via auto-complete fields
- Approved account requests trigger an email notification with login details

The repository does not include a prebuilt `database.sqlite`; each
environment should generate its own database using the migration
commands below.

## Configuration

Copy `.env.example` to `.env` and define a random secret key:

```
SECRET_KEY=replace_with_random_string
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=supersecret
MAIL_DEFAULT_SENDER=tiendix@example.com
```

This value secures Flask sessions and is required for the application to start.

## Multi-tenant usage

Each table stores a `company_id` and regular users with role `company` only access their own data. Administrators can manage any tenant by selecting an enterprise from the **Empresas** panel.

## AI Recommendations

An experimental endpoint `/api/recommendations` returns the top-selling products as basic "AI" suggestions.


### Debug mode (development only)

When running with `python app.py`, debug mode is **disabled by default**.
Enable it only in local development by setting `FLASK_DEBUG=1`:

```
FLASK_DEBUG=1 python app.py
```

Do not enable debug mode in production.

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask db init  # first run only
flask db migrate -m "initial"
flask db upgrade
python scripts/seed_db.py  # optional: seed admin user and sample data
pytest
python app.py
```

For company name auto-completion, download the latest `DGII_RNC.TXT` from the DGII and place it under `data/`.


## Ejecutar con Docker (guía para principiantes)

Si nunca has usado Docker, sigue estos pasos literalmente:

### 1) Instalar Docker
- Windows/Mac: instala **Docker Desktop**
- Linux: instala **Docker Engine** + **Docker Compose plugin**

Verifica que funcione:

```
docker --version
docker compose version
```

### 2) Configuración mínima
Este proyecto ya incluye `docker-compose.yml` con valores por defecto.
Solo cambia la clave de sesión en `docker-compose.yml`:

```yaml
SECRET_KEY: "cambia_esta_clave_por_una_segura"
```

> Usa una clave larga y difícil de adivinar.

### 3) Levantar el sistema
Desde la carpeta del proyecto ejecuta:

```
docker compose up --build
```

¿Qué hace este comando?
- Construye la imagen de Tiendix
- Instala dependencias
- Ejecuta migraciones (`flask db upgrade`)
- Inicia la app en el puerto `5000`

### 4) Abrir la aplicación
Abre en tu navegador:

```
http://localhost:5000
```

### 5) Apagar el sistema
En la terminal donde está corriendo, presiona `Ctrl + C`, o usa:

```
docker compose down
```

### 6) Dónde quedan tus datos
El `docker-compose.yml` monta volúmenes locales para que no pierdas información:
- `database.sqlite` (base de datos)
- `logs/` (logs)
- `static/uploads/` (logos/archivos)

### 7) Comandos útiles
Ver logs:

```
docker compose logs -f
```

Entrar al contenedor:

```
docker compose exec tiendix bash
```

Correr pruebas dentro del contenedor:

```
docker compose exec tiendix pytest
```

