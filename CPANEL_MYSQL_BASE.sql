-- Tiendix base setup for cPanel phpMyAdmin
-- Nota: en muchos hostings cPanel NO permite CREATE DATABASE desde phpMyAdmin.
-- Si te da error, crea DB y usuario desde "MySQL Databases" en cPanel
-- y usa este script solo para validar charset/collation dentro de la DB activa.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Opcional (si tu usuario tiene permisos):
-- CREATE DATABASE IF NOT EXISTS `USUARIO_tiendix`
--   CHARACTER SET utf8mb4
--   COLLATE utf8mb4_unicode_ci;
-- USE `USUARIO_tiendix`;

-- Verificación rápida de codificación:
SELECT @@character_set_database AS character_set_database,
       @@collation_database AS collation_database;

-- IMPORTANTE:
-- Las tablas de Tiendix se crean/migran con:
-- flask db upgrade
