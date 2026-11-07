-- ============================================================================
-- Schema do banco Olist (PostgreSQL)
-- Pode ser executado várias vezes: recria as tabelas do zero.
-- ============================================================================

DROP TABLE IF EXISTS order_reviews        CASCADE;
DROP TABLE IF EXISTS order_payments       CASCADE;
DROP TABLE IF EXISTS order_items          CASCADE;
DROP TABLE IF EXISTS orders               CASCADE;
DROP TABLE IF EXISTS products             CASCADE;
DROP TABLE IF EXISTS sellers              CASCADE;
DROP TABLE IF EXISTS customers            CASCADE;
DROP TABLE IF EXISTS category_translation CASCADE;
DROP TABLE IF EXISTS geolocation          CASCADE;

-- ----------------------------------------------------------------------------
-- Tabelas de apoio (sem dependências)
-- ----------------------------------------------------------------------------

-- Uma linha por prefixo de CEP (vem de geolocation_agg no transform).
-- Sem FK de customers/sellers: há prefixos que não existem aqui.
CREATE TABLE geolocation (
    geolocation_zip_code_prefix CHAR(5) PRIMARY KEY,
    geolocation_lat             DOUBLE PRECISION,
    geolocation_lng             DOUBLE PRECISION,
    geolocation_city            TEXT,
    geolocation_state           CHAR(2)
);

CREATE TABLE category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

-- ----------------------------------------------------------------------------
-- Entidades principais
-- ----------------------------------------------------------------------------

CREATE TABLE customers (
    customer_id              CHAR(32) PRIMARY KEY,
    customer_unique_id       CHAR(32) NOT NULL,
    customer_zip_code_prefix CHAR(5),
    customer_city            TEXT,
    customer_state           CHAR(2)
);

CREATE TABLE sellers (
    seller_id              CHAR(32) PRIMARY KEY,
    seller_zip_code_prefix CHAR(5),
    seller_city            TEXT,
    seller_state           CHAR(2)
);

-- Sem FK para category_translation: algumas categorias não têm tradução.
CREATE TABLE products (
    product_id                  CHAR(32) PRIMARY KEY,
    product_category_name       TEXT,
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);

-- ----------------------------------------------------------------------------
-- Pedidos e tabelas dependentes
-- ----------------------------------------------------------------------------

CREATE TABLE orders (
    order_id                      CHAR(32) PRIMARY KEY,
    customer_id                   CHAR(32) NOT NULL REFERENCES customers (customer_id),
    order_status                  TEXT,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE order_items (
    order_id            CHAR(32) NOT NULL REFERENCES orders (order_id),
    order_item_id       INTEGER  NOT NULL,
    product_id          CHAR(32) NOT NULL REFERENCES products (product_id),
    seller_id           CHAR(32) NOT NULL REFERENCES sellers (seller_id),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2),
    freight_value       NUMERIC(10, 2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE order_payments (
    order_id             CHAR(32) NOT NULL REFERENCES orders (order_id),
    payment_sequential   INTEGER  NOT NULL,
    payment_type         TEXT,
    payment_installments INTEGER,
    payment_value        NUMERIC(10, 2),
    PRIMARY KEY (order_id, payment_sequential)
);

-- review_id sozinho NÃO é único no dataset; a chave composta é validada
-- em load.py antes da carga.
CREATE TABLE order_reviews (
    review_id               CHAR(32) NOT NULL,
    order_id                CHAR(32) NOT NULL REFERENCES orders (order_id),
    review_score            SMALLINT,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);

-- ----------------------------------------------------------------------------
-- Índices úteis para as análises (joins e filtros frequentes)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_orders_customer     ON orders (customer_id);
CREATE INDEX idx_orders_purchase     ON orders (order_purchase_timestamp);
CREATE INDEX idx_items_product       ON order_items (product_id);
CREATE INDEX idx_items_seller        ON order_items (seller_id);
CREATE INDEX idx_customers_unique    ON customers (customer_unique_id);