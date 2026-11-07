import pandas as pd

from . import extract


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_string(df, cols):
    """Converte colunas de ID (hashes hexadecimais) para string."""
    for col in cols:
        df[col] = df[col].astype("string")
    return df


def _to_datetime(df, cols):
    """Converte colunas para datetime; valores inválidos viram NaT."""
    for col in cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _zip_to_string(df, col):
    """CEP como string de 5 dígitos, preservando zeros à esquerda."""
    df[col] = df[col].astype("string").str.zfill(5)
    return df


# ---------------------------------------------------------------------------
# Transformações por tabela
# ---------------------------------------------------------------------------
def transform_orders(df_orders):
    df = df_orders.copy()
    df = _to_string(df, ["order_id", "customer_id"])
    df = _to_datetime(df, [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ])
    return df


def transform_geolocation(df_geolocation):
    df = df_geolocation.copy()
    df = _zip_to_string(df, "geolocation_zip_code_prefix")
    df = df.drop_duplicates()
    return df


def aggregate_geolocation(df_geolocation):
    """Uma linha por prefixo de CEP (média de lat/lng).

    Útil para fazer join com customers e sellers sem multiplicar linhas.
    Espera o resultado de transform_geolocation.
    """
    return (
        df_geolocation
        .groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", "first"),
            geolocation_state=("geolocation_state", "first"),
        )
    )


def transform_customers(df_customers):
    df = df_customers.copy()
    df = _to_string(df, ["customer_id", "customer_unique_id"])
    df = _zip_to_string(df, "customer_zip_code_prefix")
    return df


def transform_products(df_products):
    df = df_products.copy()
    df = _to_string(df, ["product_id"])
    # Corrige o erro de digitação das colunas originais do dataset
    df = df.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    return df


def transform_sellers(df_sellers):
    df = df_sellers.copy()
    df = _to_string(df, ["seller_id"])
    df = _zip_to_string(df, "seller_zip_code_prefix")
    return df


def transform_order_items(df_order_items):
    df = df_order_items.copy()
    df = _to_string(df, ["order_id", "product_id", "seller_id"])
    df = _to_datetime(df, ["shipping_limit_date"])
    return df


def transform_order_payments(df_order_payments):
    df = df_order_payments.copy()
    df = _to_string(df, ["order_id"])
    return df


def transform_order_reviews(df_order_reviews):
    df = df_order_reviews.copy()
    df = _to_string(df, ["review_id", "order_id"])
    df = _to_datetime(df, ["review_creation_date", "review_answer_timestamp"])
    # review_id não é único no dataset; remove linhas totalmente duplicadas
    df = df.drop_duplicates()
    return df


def transform_category_translation(df_category_translation):
    df = df_category_translation.copy()
    return df


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def run_transform():
    """Executa todas as transformações e devolve um dicionário de DataFrames."""
    geolocation = transform_geolocation(extract.df_geolocation)

    return {
        "orders": transform_orders(extract.df_orders),
        "geolocation": geolocation,
        "geolocation_agg": aggregate_geolocation(geolocation),
        "customers": transform_customers(extract.df_customers),
        "products": transform_products(extract.df_products),
        "sellers": transform_sellers(extract.df_sellers),
        "order_items": transform_order_items(extract.df_order_items),
        "order_payments": transform_order_payments(extract.df_order_payments),
        "order_reviews": transform_order_reviews(extract.df_order_reviews),
        "category_translation": transform_category_translation(
            extract.df_category_translation
        ),
    }
