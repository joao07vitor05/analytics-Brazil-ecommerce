
import pandas as pd
from sqlalchemy import text


# --------------------------------------------------
# Funções auxiliares
# --------------------------------------------------

def date_key(series):
    """
    Converte uma coluna de datas para o formato YYYYMMDD.
    Valores nulos permanecem nulos.
    """
    dates = pd.to_datetime(series, errors="coerce")

    result = dates.dt.strftime("%Y%m%d")
    return pd.to_numeric(result, errors="coerce").astype("Int64")


def get_dimension(conn, table, key_column, natural_column):
    """
    Recupera uma dimensão do banco e retorna um DataFrame
    com sua chave substituta e chave natural.
    """
    query = text(
        f"""
        SELECT {natural_column}, {key_column}
        FROM gold.{table}
        """
    )

    return pd.read_sql(query, conn)


def prepare_records(df):
    """
    Converte valores nulos do Pandas para None,
    facilitando a inserção no PostgreSQL.
    """
    return (
        df.astype(object)
        .where(pd.notna(df), None)
        .to_dict("records")
    )


def insert_fact(conn, table, df, columns, conflict_columns):
    """
    Insere registros em uma tabela fato.
    Registros que já existem são ignorados.
    """
    if df.empty:
        return

    column_names = ", ".join(columns)
    values = ", ".join(f":{column}" for column in columns)
    conflicts = ", ".join(conflict_columns)

    query = text(
        f"""
        INSERT INTO gold.{table} ({column_names})
        VALUES ({values})
        ON CONFLICT ({conflicts}) DO NOTHING
        """
    )

    records = prepare_records(df[columns])
    conn.execute(query, records)


# --------------------------------------------------
# FACT ORDERS
# --------------------------------------------------

def build_fact_orders(dfs, conn):
    """
    Uma linha por pedido.
    """

    df = dfs["orders"].copy()

    # Dimensão de clientes
    customers = get_dimension(
        conn,
        "dim_customer",
        "customer_key",
        "customer_id"
    )

    df = df.merge(customers, on="customer_id", how="left")

    # Dimensão de status
    statuses = get_dimension(
        conn,
        "dim_order_status",
        "order_status_key",
        "order_status"
    )

    df = df.merge(statuses, on="order_status", how="left")

    # Chaves de data
    df["purchase_date_key"] = date_key(
        df["order_purchase_timestamp"]
    )

    df["approved_date_key"] = date_key(
        df["order_approved_at"]
    )

    df["carrier_date_key"] = date_key(
        df["order_delivered_carrier_date"]
    )

    df["delivered_date_key"] = date_key(
        df["order_delivered_customer_date"]
    )

    df["estimated_delivery_date_key"] = date_key(
        df["order_estimated_delivery_date"]
    )

    # Conversão das datas
    purchase = pd.to_datetime(
        df["order_purchase_timestamp"], errors="coerce"
    )

    approved = pd.to_datetime(
        df["order_approved_at"], errors="coerce"
    )

    delivered = pd.to_datetime(
        df["order_delivered_customer_date"], errors="coerce"
    )

    estimated = pd.to_datetime(
        df["order_estimated_delivery_date"], errors="coerce"
    )

    # Indicadores de tempo
    df["approval_lead_time_hours"] = (
        (approved - purchase).dt.total_seconds() / 3600
    )

    df["delivery_lead_time_days"] = (
        (delivered - purchase).dt.total_seconds() / 86400
    )

    df["delivery_delay_days"] = (
        (delivered - estimated).dt.total_seconds() / 86400
    )

    columns = [
        "order_id",
        "customer_key",
        "order_status_key",
        "purchase_date_key",
        "approved_date_key",
        "carrier_date_key",
        "delivered_date_key",
        "estimated_delivery_date_key",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "approval_lead_time_hours",
        "delivery_lead_time_days",
        "delivery_delay_days"
    ]

    return df[columns]


# --------------------------------------------------
# FACT ORDER ITEMS
# --------------------------------------------------

def build_fact_order_items(dfs, conn):
    """
    Uma linha por item de pedido.
    """

    df = dfs["order_items"].copy()

    # Recupera o cliente e a data de compra pelo pedido
    orders = dfs["orders"][
        [
            "order_id",
            "customer_id",
            "order_purchase_timestamp"
        ]
    ].copy()

    df = df.merge(orders, on="order_id", how="left")

    # Dimensão de clientes
    customers = get_dimension(
        conn,
        "dim_customer",
        "customer_key",
        "customer_id"
    )

    df = df.merge(customers, on="customer_id", how="left")

    # Dimensão de produtos
    products = get_dimension(
        conn,
        "dim_product",
        "product_key",
        "product_id"
    )

    df = df.merge(products, on="product_id", how="left")

    # Dimensão de vendedores
    sellers = get_dimension(
        conn,
        "dim_seller",
        "seller_key",
        "seller_id"
    )

    df = df.merge(sellers, on="seller_id", how="left")

    df["purchase_date_key"] = date_key(
        df["order_purchase_timestamp"]
    )

    columns = [
        "order_id",
        "order_item_id",
        "customer_key",
        "product_key",
        "seller_key",
        "purchase_date_key",
        "shipping_limit_date",
        "price",
        "freight_value"
    ]

    return df[columns]


# --------------------------------------------------
# FACT PAYMENTS
# --------------------------------------------------

def build_fact_payments(dfs, conn):
    """
    Uma linha por registro de pagamento do pedido.
    """

    df = dfs["order_payments"].copy()

    # Recupera cliente e data de compra
    orders = dfs["orders"][
        [
            "order_id",
            "customer_id",
            "order_purchase_timestamp"
        ]
    ].copy()

    df = df.merge(orders, on="order_id", how="left")

    # Dimensão de clientes
    customers = get_dimension(
        conn,
        "dim_customer",
        "customer_key",
        "customer_id"
    )

    df = df.merge(customers, on="customer_id", how="left")

    # Dimensão de tipos de pagamento
    payment_types = get_dimension(
        conn,
        "dim_payment_type",
        "payment_type_key",
        "payment_type"
    )

    df = df.merge(
        payment_types,
        on="payment_type",
        how="left"
    )

    df["purchase_date_key"] = date_key(
        df["order_purchase_timestamp"]
    )

    columns = [
        "order_id",
        "payment_sequential",
        "customer_key",
        "purchase_date_key",
        "payment_type_key",
        "payment_installments",
        "payment_value"
    ]

    return df[columns]


# --------------------------------------------------
# FACT REVIEWS
# --------------------------------------------------

def build_fact_reviews(dfs, conn):
    """
    Uma linha por avaliação de pedido.
    """

    df = dfs["order_reviews"].copy()

    # Recupera cliente e data de compra
    orders = dfs["orders"][
        [
            "order_id",
            "customer_id",
            "order_purchase_timestamp"
        ]
    ].copy()

    df = df.merge(orders, on="order_id", how="left")

    # Dimensão de clientes
    customers = get_dimension(
        conn,
        "dim_customer",
        "customer_key",
        "customer_id"
    )

    df = df.merge(customers, on="customer_id", how="left")

    # Chaves de data
    df["purchase_date_key"] = date_key(
        df["order_purchase_timestamp"]
    )

    df["review_date_key"] = date_key(
        df["review_creation_date"]
    )

    df["review_answer_date_key"] = date_key(
        df["review_answer_timestamp"]
    )

    columns = [
        "review_id",
        "order_id",
        "customer_key",
        "purchase_date_key",
        "review_date_key",
        "review_answer_date_key",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp"
    ]

    return df[columns]


# --------------------------------------------------
# CARGA DAS TABELAS FATO
# --------------------------------------------------

def load_facts(conn, dfs):

    # Fact Orders
    fact_orders = build_fact_orders(dfs, conn)

    insert_fact(
        conn,
        "fact_orders",
        fact_orders,
        list(fact_orders.columns),
        ["order_id"]
    )

    # Fact Order Items
    fact_order_items = build_fact_order_items(dfs, conn)

    insert_fact(
        conn,
        "fact_order_items",
        fact_order_items,
        list(fact_order_items.columns),
        ["order_id", "order_item_id"]
    )

    # Fact Payments
    fact_payments = build_fact_payments(dfs, conn)

    insert_fact(
        conn,
        "fact_payments",
        fact_payments,
        list(fact_payments.columns),
        ["order_id", "payment_sequential"]
    )

    # Fact Reviews
    fact_reviews = build_fact_reviews(dfs, conn)

    # A tabela utiliza review_key como chave primária.
    # A verificação abaixo evita inserir novamente uma
    # combinação review_id + order_id já existente.
    review_query = text(
        """
        INSERT INTO gold.fact_reviews (
            review_id,
            order_id,
            customer_key,
            purchase_date_key,
            review_date_key,
            review_answer_date_key,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            review_answer_timestamp
        )
        SELECT
            :review_id,
            :order_id,
            :customer_key,
            :purchase_date_key,
            :review_date_key,
            :review_answer_date_key,
            :review_score,
            :review_comment_title,
            :review_comment_message,
            :review_creation_date,
            :review_answer_timestamp
        WHERE NOT EXISTS (
            SELECT 1
            FROM gold.fact_reviews
            WHERE review_id = :review_id
              AND order_id = :order_id
        )
        """
    )

    if not fact_reviews.empty:
        conn.execute(
            review_query,
            prepare_records(fact_reviews)
        )

    print("Tabelas fato carregadas com sucesso.")
