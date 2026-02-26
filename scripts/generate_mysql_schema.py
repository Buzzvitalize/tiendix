"""Generate MySQL schema SQL from SQLAlchemy models.

Usage:
  python scripts/generate_mysql_schema.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql

from app import app
from models import db

OUT_FILE = Path('CPANEL_MYSQL_FULL_SCHEMA.sql')


def main() -> None:
    with app.app_context():
        dialect = mysql.dialect()
        lines = [
            '-- Tiendix full schema for MySQL/phpMyAdmin',
            '-- Generated automatically from SQLAlchemy models.',
            'SET NAMES utf8mb4;',
            "SET time_zone = '+00:00';",
            '',
            '-- Optional (if your hosting user has privileges):',
            '-- CREATE DATABASE IF NOT EXISTS `USUARIO_tiendix` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;',
            '-- USE `USUARIO_tiendix`;',
            '',
        ]

        for table in db.metadata.sorted_tables:
            stmt = str(CreateTable(table).compile(dialect=dialect)).rstrip() + ';'
            lines.append(stmt)
            lines.append('')

        lines.extend([
            '-- Notes:',
            '-- 1) Import this SQL in phpMyAdmin with the target DB selected.',
            '-- 2) Then run: flask db upgrade',
            '--    (keeps Alembic migration history in sync for future updates).',
            '',
        ])

        OUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
        print(f'Wrote {OUT_FILE}')


if __name__ == '__main__':
    main()
