/*
===============================================================================
Projeto: Olist Brazilian E-Commerce Analytics
Camada:  GOLD
Modelo:  Star Schema
Banco:   PostgreSQL

Responsabilidade deste arquivo:
  1. Criar o schema gold.
  2. Criar as dimensoes e tabelas fato do modelo dimensional.

Este arquivo NAO carrega dados. A carga sera implementada separadamente
em um script Python
Granularidade das fatos:
  - fact_orders:      uma linha por pedido (order_id).
  - fact_order_items: uma linha por item do pedido (order_id, order_item_id).
  - fact_payments:    uma linha por registro de pagamento
                      (order_id, payment_sequential).
  - fact_reviews:     uma linha por registro de avaliacao (review_key).

Observacoes:
  - order_id e mantido como dimensao degenerada nas fatos de itens,
    pagamentos e avaliacoes. Nao ha relacionamento fato-com-fato.
  - customer_id identifica o cadastro associado ao pedido.
    customer_unique_id permite agrupar cadastros do mesmo consumidor.
  - As chaves date_key seguem o formato YYYYMMDD.
===============================================================================
*/


/* ---------------------------------------------------------------------------
   1. FUNCAO DE CRIACAO DO SCHEMA
   A funcao fica em public porque gold ainda nao existe na primeira execucao.
--------------------------------------------------------------------------- */

CREATE OR REPLACE FUNCTION public.create_gold_schema()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    EXECUTE 'CREATE SCHEMA IF NOT EXISTS gold';
END;
$$;

SELECT public.create_gold_schema();


/* ---------------------------------------------------------------------------
   2. DIMENSOES
--------------------------------------------------------------------------- */

-- Cliente: uma linha por customer_id (cadastro da Olist).
-- customer_unique_id e mantido para analises de clientes recorrentes.
CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL UNIQUE,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix VARCHAR(5),
    customer_city VARCHAR(120),
    customer_state CHAR(2),
    customer_lat NUMERIC(10, 7),
    customer_lng NUMERIC(10, 7),

    CONSTRAINT ck_dim_customer_lat
        CHECK (customer_lat IS NULL OR customer_lat BETWEEN -90 AND 90),
    CONSTRAINT ck_dim_customer_lng
        CHECK (customer_lng IS NULL OR customer_lng BETWEEN -180 AND 180)
);


-- Produto: uma linha por product_id.
CREATE TABLE IF NOT EXISTS gold.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id VARCHAR(64) NOT NULL UNIQUE,
    product_category_name VARCHAR(120),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(12, 2),
    product_height_cm NUMERIC(12, 2),
    product_width_cm NUMERIC(12, 2),

    CONSTRAINT ck_dim_product_name_length
        CHECK (product_name_length IS NULL OR product_name_length >= 0),
    CONSTRAINT ck_dim_product_description_length
        CHECK (product_description_length IS NULL OR product_description_length >= 0),
    CONSTRAINT ck_dim_product_photos_qty
        CHECK (product_photos_qty IS NULL OR product_photos_qty >= 0),
    CONSTRAINT ck_dim_product_weight
        CHECK (product_weight_g IS NULL OR product_weight_g >= 0),
    CONSTRAINT ck_dim_product_length
        CHECK (product_length_cm IS NULL OR product_length_cm >= 0),
    CONSTRAINT ck_dim_product_height
        CHECK (product_height_cm IS NULL OR product_height_cm >= 0),
    CONSTRAINT ck_dim_product_width
        CHECK (product_width_cm IS NULL OR product_width_cm >= 0)
);


-- Vendedor: uma linha por seller_id.
CREATE TABLE IF NOT EXISTS gold.dim_seller (
    seller_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id VARCHAR(64) NOT NULL UNIQUE,
    seller_zip_code_prefix VARCHAR(5),
    seller_city VARCHAR(120),
    seller_state CHAR(2),
    seller_lat NUMERIC(10, 7),
    seller_lng NUMERIC(10, 7),

    CONSTRAINT ck_dim_seller_lat
        CHECK (seller_lat IS NULL OR seller_lat BETWEEN -90 AND 90),
    CONSTRAINT ck_dim_seller_lng
        CHECK (seller_lng IS NULL OR seller_lng BETWEEN -180 AND 180)
);


-- Calendario: uma linha por dia.
-- A populacao do calendario sera feita pelo processo de carga.
CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,

    CONSTRAINT ck_dim_date_key
        CHECK (date_key = TO_CHAR(full_date, 'YYYYMMDD')::INTEGER),
    CONSTRAINT ck_dim_date_quarter
        CHECK (quarter BETWEEN 1 AND 4),
    CONSTRAINT ck_dim_date_month
        CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT ck_dim_date_week
        CHECK (week_of_year BETWEEN 1 AND 53),
    CONSTRAINT ck_dim_date_day
        CHECK (day_of_month BETWEEN 1 AND 31),
    CONSTRAINT ck_dim_date_day_of_week
        CHECK (day_of_week BETWEEN 1 AND 7)
);


-- Tipo de pagamento: uma linha por tipo de pagamento distinto.
CREATE TABLE IF NOT EXISTS gold.dim_payment_type (
    payment_type_key SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_type VARCHAR(40) NOT NULL UNIQUE
);


-- Status do pedido: uma linha por status distinto.
CREATE TABLE IF NOT EXISTS gold.dim_order_status (
    order_status_key SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_status VARCHAR(40) NOT NULL UNIQUE
);


/* ---------------------------------------------------------------------------
   3. TABELAS FATO
--------------------------------------------------------------------------- */

-- Fato de pedidos: uma linha por order_id.
CREATE TABLE IF NOT EXISTS gold.fact_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_key BIGINT NOT NULL,
    order_status_key SMALLINT NOT NULL,

    purchase_date_key INTEGER,
    approved_date_key INTEGER,
    carrier_date_key INTEGER,
    delivered_date_key INTEGER,
    estimated_delivery_date_key INTEGER,

    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,

    approval_lead_time_hours NUMERIC(12, 2),
    delivery_lead_time_days NUMERIC(12, 2),
    delivery_delay_days NUMERIC(12, 2),

    CONSTRAINT fk_fact_orders_customer
        FOREIGN KEY (customer_key)
        REFERENCES gold.dim_customer (customer_key),

    CONSTRAINT fk_fact_orders_status
        FOREIGN KEY (order_status_key)
        REFERENCES gold.dim_order_status (order_status_key),

    CONSTRAINT fk_fact_orders_purchase_date
        FOREIGN KEY (purchase_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_orders_approved_date
        FOREIGN KEY (approved_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_orders_carrier_date
        FOREIGN KEY (carrier_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_orders_delivered_date
        FOREIGN KEY (delivered_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_orders_estimated_date
        FOREIGN KEY (estimated_delivery_date_key)
        REFERENCES gold.dim_date (date_key)
);


-- Fato de itens: uma linha por item de um pedido.
-- order_id e order_item_id formam a chave primaria composta.
CREATE TABLE IF NOT EXISTS gold.fact_order_items (
    order_id VARCHAR(64) NOT NULL,
    order_item_id INTEGER NOT NULL,

    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    seller_key BIGINT NOT NULL,
    purchase_date_key INTEGER,

    shipping_limit_date TIMESTAMP,
    price NUMERIC(12, 2) NOT NULL,
    freight_value NUMERIC(12, 2) NOT NULL,

    CONSTRAINT pk_fact_order_items
        PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT ck_fact_order_items_item_id
        CHECK (order_item_id > 0),

    CONSTRAINT ck_fact_order_items_price
        CHECK (price >= 0),

    CONSTRAINT ck_fact_order_items_freight
        CHECK (freight_value >= 0),

    CONSTRAINT fk_fact_order_items_customer
        FOREIGN KEY (customer_key)
        REFERENCES gold.dim_customer (customer_key),

    CONSTRAINT fk_fact_order_items_product
        FOREIGN KEY (product_key)
        REFERENCES gold.dim_product (product_key),

    CONSTRAINT fk_fact_order_items_seller
        FOREIGN KEY (seller_key)
        REFERENCES gold.dim_seller (seller_key),

    CONSTRAINT fk_fact_order_items_purchase_date
        FOREIGN KEY (purchase_date_key)
        REFERENCES gold.dim_date (date_key)
);


-- Fato de pagamentos: uma linha por registro/sequencia de pagamento.
-- order_id e mantido como dimensao degenerada.
CREATE TABLE IF NOT EXISTS gold.fact_payments (
    order_id VARCHAR(64) NOT NULL,
    payment_sequential INTEGER NOT NULL,

    customer_key BIGINT NOT NULL,
    purchase_date_key INTEGER,
    payment_type_key SMALLINT NOT NULL,

    payment_installments INTEGER,
    payment_value NUMERIC(12, 2) NOT NULL,

    CONSTRAINT pk_fact_payments
        PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT ck_fact_payments_sequential
        CHECK (payment_sequential > 0),

    CONSTRAINT ck_fact_payments_installments
        CHECK (payment_installments IS NULL OR payment_installments >= 0),

    CONSTRAINT ck_fact_payments_value
        CHECK (payment_value >= 0),

    CONSTRAINT fk_fact_payments_customer
        FOREIGN KEY (customer_key)
        REFERENCES gold.dim_customer (customer_key),

    CONSTRAINT fk_fact_payments_purchase_date
        FOREIGN KEY (purchase_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_payments_type
        FOREIGN KEY (payment_type_key)
        REFERENCES gold.dim_payment_type (payment_type_key)
);


-- Fato de avaliacoes: uma linha por registro de avaliacao.
-- review_id e preservado como identificador de origem, sem UNIQUE.
CREATE TABLE IF NOT EXISTS gold.fact_reviews (
    review_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id VARCHAR(64),
    order_id VARCHAR(64) NOT NULL,

    customer_key BIGINT NOT NULL,
    purchase_date_key INTEGER,
    review_date_key INTEGER,
    review_answer_date_key INTEGER,

    review_score SMALLINT NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,

    CONSTRAINT ck_fact_reviews_score
        CHECK (review_score BETWEEN 1 AND 5),

    CONSTRAINT fk_fact_reviews_customer
        FOREIGN KEY (customer_key)
        REFERENCES gold.dim_customer (customer_key),

    CONSTRAINT fk_fact_reviews_purchase_date
        FOREIGN KEY (purchase_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_reviews_review_date
        FOREIGN KEY (review_date_key)
        REFERENCES gold.dim_date (date_key),

    CONSTRAINT fk_fact_reviews_answer_date
        FOREIGN KEY (review_answer_date_key)
        REFERENCES gold.dim_date (date_key)
);


/* ---------------------------------------------------------------------------
   4. INDICES
   Indices para colunas de relacionamento e filtros frequentes.
--------------------------------------------------------------------------- */

CREATE INDEX IF NOT EXISTS idx_dim_customer_unique_id
    ON gold.dim_customer (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_dim_customer_state
    ON gold.dim_customer (customer_state);

CREATE INDEX IF NOT EXISTS idx_dim_product_category
    ON gold.dim_product (product_category_name);

CREATE INDEX IF NOT EXISTS idx_dim_seller_state
    ON gold.dim_seller (seller_state);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer
    ON gold.fact_orders (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_orders_status
    ON gold.fact_orders (order_status_key);

CREATE INDEX IF NOT EXISTS idx_fact_orders_purchase_date
    ON gold.fact_orders (purchase_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_customer
    ON gold.fact_order_items (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_product
    ON gold.fact_order_items (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_seller
    ON gold.fact_order_items (seller_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_purchase_date
    ON gold.fact_order_items (purchase_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_items_order
    ON gold.fact_order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_fact_payments_customer
    ON gold.fact_payments (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_payments_type
    ON gold.fact_payments (payment_type_key);

CREATE INDEX IF NOT EXISTS idx_fact_payments_purchase_date
    ON gold.fact_payments (purchase_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_payments_order
    ON gold.fact_payments (order_id);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_customer
    ON gold.fact_reviews (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_review_date
    ON gold.fact_reviews (review_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_order
    ON gold.fact_reviews (order_id);


/* ---------------------------------------------------------------------------
   5. CONSULTA DE CONFERENCIA
--------------------------------------------------------------------------- */

-- Deve retornar as 10 tabelas do modelo dimensional.
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'gold'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
