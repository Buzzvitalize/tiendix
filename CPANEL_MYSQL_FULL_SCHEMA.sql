-- Tiendix full schema for MySQL/phpMyAdmin
-- Generated automatically from SQLAlchemy models.
SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Optional (if your hosting user has privileges):
-- CREATE DATABASE IF NOT EXISTS `USUARIO_tiendix` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE `USUARIO_tiendix`;


CREATE TABLE account_request (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	account_type VARCHAR(20) NOT NULL, 
	first_name VARCHAR(120) NOT NULL, 
	last_name VARCHAR(120) NOT NULL, 
	company VARCHAR(120) NOT NULL, 
	identifier VARCHAR(50) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	address VARCHAR(200), 
	website VARCHAR(120), 
	username VARCHAR(80) NOT NULL, 
	password VARCHAR(120) NOT NULL, 
	created_at DATETIME, 
	accepted_terms BOOL NOT NULL, 
	accepted_terms_at DATETIME, 
	accepted_terms_ip VARCHAR(45), 
	accepted_terms_user_agent VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (username)
);


CREATE TABLE company_info (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	street VARCHAR(120) NOT NULL, 
	sector VARCHAR(120) NOT NULL, 
	province VARCHAR(120) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	rnc VARCHAR(50) NOT NULL, 
	website VARCHAR(120), 
	logo VARCHAR(120), 
	ncf_final INTEGER, 
	ncf_fiscal INTEGER, 
	PRIMARY KEY (id)
);


CREATE TABLE export_log (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user VARCHAR(80), 
	company_id INTEGER, 
	formato VARCHAR(10), 
	tipo VARCHAR(20), 
	filtros TEXT, 
	status VARCHAR(20), 
	message TEXT, 
	file_path VARCHAR(200), 
	created_at DATETIME, 
	PRIMARY KEY (id)
);


CREATE TABLE client (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	last_name VARCHAR(120), 
	identifier VARCHAR(50), 
	phone VARCHAR(50), 
	email VARCHAR(120), 
	street VARCHAR(120), 
	sector VARCHAR(120), 
	province VARCHAR(120), 
	is_final_consumer BOOL, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_client_identifier_company UNIQUE (identifier, company_id), 
	CONSTRAINT uq_client_email_company UNIQUE (email, company_id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE notification (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	company_id INTEGER NOT NULL, 
	message VARCHAR(200) NOT NULL, 
	is_read BOOL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE product (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	code VARCHAR(50) NOT NULL, 
	reference VARCHAR(50), 
	name VARCHAR(120) NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	price FLOAT NOT NULL, 
	cost_price FLOAT, 
	category VARCHAR(50), 
	has_itbis BOOL, 
	stock INTEGER, 
	min_stock INTEGER, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE user (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(80) NOT NULL, 
	password VARCHAR(128) NOT NULL, 
	email VARCHAR(120), 
	first_name VARCHAR(120) NOT NULL, 
	last_name VARCHAR(120) NOT NULL, 
	`role` VARCHAR(20), 
	company_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE warehouse (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	address VARCHAR(200), 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE audit_log (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(80), 
	`role` VARCHAR(20), 
	company_id INTEGER, 
	action VARCHAR(80) NOT NULL, 
	entity VARCHAR(80) NOT NULL, 
	entity_id VARCHAR(80), 
	status VARCHAR(20), 
	details TEXT, 
	ip VARCHAR(45), 
	user_agent VARCHAR(255), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);


CREATE TABLE error_report (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(80), 
	company_id INTEGER, 
	title VARCHAR(180) NOT NULL, 
	module VARCHAR(80) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	page_url VARCHAR(255), 
	happened_at DATETIME, 
	expected_behavior TEXT, 
	actual_behavior TEXT NOT NULL, 
	steps_to_reproduce TEXT NOT NULL, 
	contact_email VARCHAR(120), 
	ip VARCHAR(45), 
	user_agent VARCHAR(255), 
	admin_notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);


CREATE TABLE inventory_movement (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	movement_type VARCHAR(10) NOT NULL, 
	reference_type VARCHAR(20), 
	reference_id INTEGER, 
	timestamp DATETIME, 
	warehouse_id INTEGER, 
	company_id INTEGER NOT NULL, 
	executed_by INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES product (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouse (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id), 
	FOREIGN KEY(executed_by) REFERENCES user (id)
);


CREATE TABLE ncf_log (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	company_id INTEGER NOT NULL, 
	old_final INTEGER, 
	old_fiscal INTEGER, 
	new_final INTEGER, 
	new_fiscal INTEGER, 
	changed_by INTEGER, 
	changed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id), 
	FOREIGN KEY(changed_by) REFERENCES user (id)
);


CREATE TABLE product_price_log (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	old_price FLOAT, 
	new_price FLOAT NOT NULL, 
	old_cost_price FLOAT, 
	new_cost_price FLOAT, 
	changed_by INTEGER, 
	changed_at DATETIME NOT NULL, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES product (id), 
	FOREIGN KEY(changed_by) REFERENCES user (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE product_stock (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	warehouse_id INTEGER NOT NULL, 
	stock INTEGER, 
	min_stock INTEGER, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_product_wh UNIQUE (product_id, warehouse_id), 
	FOREIGN KEY(product_id) REFERENCES product (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouse (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE quotation (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	client_id INTEGER NOT NULL, 
	date DATETIME, 
	valid_until DATETIME NOT NULL, 
	subtotal FLOAT NOT NULL, 
	itbis FLOAT NOT NULL, 
	total FLOAT NOT NULL, 
	seller VARCHAR(120), 
	payment_method VARCHAR(20), 
	bank VARCHAR(50), 
	note TEXT, 
	status VARCHAR(20), 
	company_id INTEGER NOT NULL, 
	warehouse_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES client (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouse (id)
);


CREATE TABLE system_announcement (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(180) NOT NULL, 
	message TEXT NOT NULL, 
	scheduled_for DATETIME, 
	is_active BOOL NOT NULL, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES user (id)
);


CREATE TABLE `order` (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	client_id INTEGER NOT NULL, 
	quotation_id INTEGER, 
	date DATETIME, 
	status VARCHAR(20), 
	delivery_date DATETIME, 
	subtotal FLOAT NOT NULL, 
	itbis FLOAT NOT NULL, 
	total FLOAT NOT NULL, 
	seller VARCHAR(120), 
	payment_method VARCHAR(20), 
	bank VARCHAR(50), 
	note TEXT, 
	customer_po VARCHAR(120), 
	warehouse_id INTEGER, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES client (id), 
	FOREIGN KEY(quotation_id) REFERENCES quotation (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouse (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE quotation_item (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	quotation_id INTEGER NOT NULL, 
	code VARCHAR(50), 
	reference VARCHAR(50), 
	product_name VARCHAR(120) NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	unit_price FLOAT NOT NULL, 
	quantity INTEGER NOT NULL, 
	discount FLOAT, 
	category VARCHAR(50), 
	has_itbis BOOL, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(quotation_id) REFERENCES quotation (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE invoice (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	client_id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	date DATETIME, 
	subtotal FLOAT NOT NULL, 
	itbis FLOAT NOT NULL, 
	total FLOAT NOT NULL, 
	ncf VARCHAR(20), 
	seller VARCHAR(120), 
	payment_method VARCHAR(20), 
	bank VARCHAR(50), 
	invoice_type VARCHAR(20), 
	status VARCHAR(20), 
	note TEXT, 
	warehouse_id INTEGER, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES client (id), 
	FOREIGN KEY(order_id) REFERENCES `order` (id), 
	UNIQUE (ncf), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouse (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE order_item (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	code VARCHAR(50), 
	reference VARCHAR(50), 
	product_name VARCHAR(120) NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	unit_price FLOAT NOT NULL, 
	quantity INTEGER NOT NULL, 
	discount FLOAT, 
	category VARCHAR(50), 
	has_itbis BOOL, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES `order` (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE invoice_item (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	invoice_id INTEGER NOT NULL, 
	code VARCHAR(50), 
	reference VARCHAR(50), 
	product_name VARCHAR(120) NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	unit_price FLOAT NOT NULL, 
	quantity INTEGER NOT NULL, 
	discount FLOAT, 
	category VARCHAR(50), 
	has_itbis BOOL, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoice (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);


CREATE TABLE payment (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	invoice_id INTEGER NOT NULL, 
	amount FLOAT NOT NULL, 
	date DATETIME, 
	company_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoice (id), 
	FOREIGN KEY(company_id) REFERENCES company_info (id)
);

-- Notes:
-- 1) Import this SQL in phpMyAdmin with the target DB selected.
-- 2) Then run: flask db upgrade
--    (keeps Alembic migration history in sync for future updates).
