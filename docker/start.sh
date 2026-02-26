#!/usr/bin/env bash
set -e

echo "[docker] Ejecutando migraciones..."
flask db upgrade

echo "[docker] Iniciando Tiendix..."
python app.py
