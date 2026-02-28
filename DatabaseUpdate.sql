-- Tiendix incremental database update script (MySQL/MariaDB)
-- Purpose: update an existing installation without dropping data.
-- Usage (phpMyAdmin): open current DB and run this file as SQL.

SET @db := DATABASE();

DELIMITER $$
DROP PROCEDURE IF EXISTS sp_tiendix_database_update $$
CREATE PROCEDURE sp_tiendix_database_update()
BEGIN
    -- 1) Harden password columns to avoid truncated hashes
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'user' AND column_name = 'password'
    ) THEN
        SET @sql := 'ALTER TABLE `user` MODIFY COLUMN `password` VARCHAR(255) NOT NULL';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'account_request' AND column_name = 'password'
    ) THEN
        SET @sql := 'ALTER TABLE `account_request` MODIFY COLUMN `password` VARCHAR(255) NOT NULL';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    -- 2) account_request terms fields (if missing)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'account_request' AND column_name = 'accepted_terms'
    ) THEN
        SET @sql := 'ALTER TABLE `account_request` ADD COLUMN `accepted_terms` TINYINT(1) NOT NULL DEFAULT 0';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'account_request' AND column_name = 'accepted_terms_at'
    ) THEN
        SET @sql := 'ALTER TABLE `account_request` ADD COLUMN `accepted_terms_at` DATETIME NULL';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'account_request' AND column_name = 'accepted_terms_ip'
    ) THEN
        SET @sql := 'ALTER TABLE `account_request` ADD COLUMN `accepted_terms_ip` VARCHAR(45) NULL';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = @db AND table_name = 'account_request' AND column_name = 'accepted_terms_user_agent'
    ) THEN
        SET @sql := 'ALTER TABLE `account_request` ADD COLUMN `accepted_terms_user_agent` VARCHAR(255) NULL';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    -- 3) New operational tables
    SET @sql := 'CREATE TABLE IF NOT EXISTS `error_report` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `created_at` DATETIME NOT NULL,
      `updated_at` DATETIME NOT NULL,
      `user_id` INT NULL,
      `username` VARCHAR(80) NULL,
      `company_id` INT NULL,
      `title` VARCHAR(180) NOT NULL,
      `module` VARCHAR(80) NOT NULL,
      `severity` VARCHAR(20) NOT NULL DEFAULT ''media'',
      `status` VARCHAR(20) NOT NULL DEFAULT ''abierto'',
      `page_url` VARCHAR(255) NULL,
      `happened_at` DATETIME NULL,
      `expected_behavior` TEXT NULL,
      `actual_behavior` TEXT NOT NULL,
      `steps_to_reproduce` TEXT NOT NULL,
      `contact_email` VARCHAR(120) NULL,
      `ip` VARCHAR(45) NULL,
      `user_agent` VARCHAR(255) NULL,
      `admin_notes` TEXT NULL,
      PRIMARY KEY (`id`),
      KEY `ix_error_report_created_at` (`created_at`),
      KEY `ix_error_report_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci';
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql := 'CREATE TABLE IF NOT EXISTS `system_announcement` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `title` VARCHAR(180) NOT NULL,
      `message` TEXT NOT NULL,
      `scheduled_for` DATETIME NULL,
      `is_active` TINYINT(1) NOT NULL DEFAULT 1,
      `created_by` INT NULL,
      `created_at` DATETIME NOT NULL,
      `updated_at` DATETIME NOT NULL,
      PRIMARY KEY (`id`),
      KEY `ix_system_announcement_active_updated` (`is_active`,`updated_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci';
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql := 'CREATE TABLE IF NOT EXISTS `app_setting` (
      `key` VARCHAR(80) NOT NULL,
      `value` VARCHAR(255) NOT NULL,
      `updated_at` DATETIME NOT NULL,
      PRIMARY KEY (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci';
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql := 'CREATE TABLE IF NOT EXISTS `rnc_registry` (
      `rnc` VARCHAR(20) NOT NULL,
      `name` VARCHAR(180) NOT NULL,
      `source` VARCHAR(40) NOT NULL DEFAULT ''upload'',
      `updated_at` DATETIME NOT NULL,
      PRIMARY KEY (`rnc`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci';
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql := 'CREATE TABLE IF NOT EXISTS `audit_log` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `created_at` DATETIME NOT NULL,
      `user_id` INT NULL,
      `username` VARCHAR(80) NULL,
      `role` VARCHAR(20) NULL,
      `company_id` INT NULL,
      `action` VARCHAR(80) NOT NULL,
      `entity` VARCHAR(80) NOT NULL,
      `entity_id` VARCHAR(80) NULL,
      `status` VARCHAR(20) NULL DEFAULT ''ok'',
      `details` TEXT NULL,
      `ip` VARCHAR(45) NULL,
      `user_agent` VARCHAR(255) NULL,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci';
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    -- 4) Performance indexes (if missing)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = @db AND table_name = 'audit_log' AND index_name = 'ix_audit_log_created_at'
    ) THEN
        SET @sql := 'CREATE INDEX `ix_audit_log_created_at` ON `audit_log` (`created_at`)';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = @db AND table_name = 'audit_log' AND index_name = 'ix_audit_log_action_created_at'
    ) THEN
        SET @sql := 'CREATE INDEX `ix_audit_log_action_created_at` ON `audit_log` (`action`, `created_at`)';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = @db AND table_name = 'audit_log' AND index_name = 'ix_audit_log_entity_entity_id'
    ) THEN
        SET @sql := 'CREATE INDEX `ix_audit_log_entity_entity_id` ON `audit_log` (`entity`, `entity_id`)';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = @db AND table_name = 'audit_log' AND index_name = 'ix_audit_log_user_id_created_at'
    ) THEN
        SET @sql := 'CREATE INDEX `ix_audit_log_user_id_created_at` ON `audit_log` (`user_id`, `created_at`)';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = @db AND table_name = 'rnc_registry' AND index_name = 'ix_rnc_registry_updated_at'
    ) THEN
        SET @sql := 'CREATE INDEX `ix_rnc_registry_updated_at` ON `rnc_registry` (`updated_at`)';
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

    -- 5) Default app setting used by cpanel flow
    INSERT INTO app_setting (`key`, `value`, `updated_at`)
    VALUES ('signup_auto_approve', '0', NOW())
    ON DUPLICATE KEY UPDATE `updated_at` = VALUES(`updated_at`);
END $$
DELIMITER ;

CALL sp_tiendix_database_update();
DROP PROCEDURE IF EXISTS sp_tiendix_database_update;

-- Optional verification queries:
-- SELECT COUNT(*) FROM audit_log;
-- SELECT COUNT(*) FROM rnc_registry;
-- SELECT `key`, `value` FROM app_setting WHERE `key` = 'signup_auto_approve';
