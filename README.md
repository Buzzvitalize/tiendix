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

## cPanel (Python Setup + phpMyAdmin/MySQL)

Para producción en cPanel se recomienda usar MySQL/MariaDB (no `sqlite`).

1. Crea base y usuario en **cPanel > MySQL Databases**.
2. En **Setup Python App > Environment Variables** puedes usar cualquiera de estas opciones.

**Opción A (rápida, recomendada): variables simples**
```
APP_ENV=production
SECRET_KEY=clave_larga_y_segura
DB_DRIVER=mysql+pymysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=USUARIO_tiendix
DB_USER=USUARIO_dbuser
DB_PASSWORD=clave_db
PDF_ARCHIVE_ROOT=/home/USUARIO/tiendix_data/generated_docs
```

**Opción B (URL completa):**
```
APP_ENV=production
SECRET_KEY=clave_larga_y_segura
DATABASE_URL=mysql+pymysql://USUARIO_dbuser:clave_db@localhost:3306/USUARIO_tiendix?charset=utf8mb4
PDF_ARCHIVE_ROOT=/home/USUARIO/tiendix_data/generated_docs
```

> La app soporta `mysql://...` y lo corrige automáticamente a `mysql+pymysql://...`.

3. Activa el virtualenv e instala dependencias.
4. Ejecuta migraciones:

```
flask db upgrade
```

5. Reinicia la app desde Setup Python App.

Consulta también `CPANEL_PYTHON_GUIA.txt`, `CPANEL_MYSQL_BASE.sql`, `CPANEL_MYSQL_FULL_SCHEMA.sql` y `.env.cpanel.example`.

Si ya tienes una instalación en producción y solo quieres actualizar el esquema sin reinstalar, ejecuta `DatabaseUpdate.sql` en tu base actual (phpMyAdmin).

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
