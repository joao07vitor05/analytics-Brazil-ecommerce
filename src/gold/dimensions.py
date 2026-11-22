
import pandas as pd
from sqlalchemy import text


def insert_dimension(conn, table, df, conflict_column):
    """Insere registros sem duplicar chaves de negócio existentes."""

    if df.empty:
        return

    columns = list(df.columns)

    column_names = ", ".join(columns)
    values = ", ".join(f":{column}" for column in columns)

    query = text(f"""
        INSERT INTO gold.{table} ({column_names})
        VALUES ({values})
        ON CONFLICT ({conflict_column}) DO NOTHING
    """)

    records = df.astype(object).where(pd.notna(df), None).to_dict(
        orient="records"
    )

    conn.execute(query, records)


def build_dim_date(dfs):
    """Gera um calendário contínuo considerando todas as datas utilizadas."""

    date_columns = {
        "orders": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "order_items": ["shipping_limit_date"],
        "order_reviews": [
            "review_creation_date",
            "review_answer_timestamp",
        ],
    }

    dates = []

    for table, columns in date_columns.items():
        for column in columns:
            values = pd.to_datetime(
                dfs[table][column], errors="coerce"
            ).dropna()

            dates.extend(values.dt.normalize().tolist())

    if not dates:
        raise ValueError("Nenhuma data encontrada para dim_date.")

    calendar = pd.DataFrame({
        "full_date": pd.date_range(
            min(dates).date(),
            max(dates).date(),
            freq="D",
        )
    })

    calendar["date_key"] = (
        calendar["full_date"].dt.strftime("%Y%m%d").astype(int)
    )

    calendar["year"] = calendar["full_date"].dt.year
    calendar["quarter"] = calendar["full_date"].dt.quarter
    calendar["month"] = calendar["full_date"].dt.month

    month_names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março",
        4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro",
        10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }

    day_names = {
        1: "Segunda-feira", 2: "Terça-feira",
        3: "Quarta-feira", 4: "Quinta-feira",
        5: "Sexta-feira", 6: "Sábado", 7: "Domingo",
    }

    calendar["month_name"] = calendar["month"].map(month_names)
    calendar["year_month"] = calendar["full_date"].dt.strftime("%Y-%m")

    calendar["week_of_year"] = (
        calendar["full_date"].dt.isocalendar().week.astype(int)
    )

    calendar["day_of_month"] = calendar["full_date"].dt.day

    calendar["day_of_week"] = (
        calendar["full_date"].dt.dayofweek + 1
    )

    calendar["day_name"] = calendar["day_of_week"].map(day_names)

    calendar["is_weekend"] = calendar["day_of_week"] >= 6

    calendar["full_date"] = calendar["full_date"].dt.date

    return calendar


def build_dim_customer(dfs):
    """Integra clientes com suas coordenadas geográficas."""

    customers = dfs["customers"].copy()
    geolocation = dfs["geolocation_agg"].copy()

    customers["customer_zip_code_prefix"] = (
        customers["customer_zip_code_prefix"].astype(str).str.zfill(5)
    )

    geolocation["geolocation_zip_code_prefix"] = (
        geolocation["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    )

    geo = geolocation[
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ]
    ]

    df = customers.merge(
        geo,
        left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
        validate="many_to_one",
    )

    df = df.rename(columns={
        "geolocation_lat": "customer_lat",
        "geolocation_lng": "customer_lng",
    })

    return df[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
            "customer_lat",
            "customer_lng",
        ]
    ]


def build_dim_product(dfs):
    """Prepara os atributos dos produtos."""

    df = dfs["products"].copy()

    df = df.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })

    return df[
        [
            "product_id",
            "product_category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
    ]


def build_dim_seller(dfs):
    """Integra vendedores com suas coordenadas geográficas."""

    sellers = dfs["sellers"].copy()
    geolocation = dfs["geolocation_agg"].copy()

    sellers["seller_zip_code_prefix"] = (
        sellers["seller_zip_code_prefix"].astype(str).str.zfill(5)
    )

    geolocation["geolocation_zip_code_prefix"] = (
        geolocation["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    )

    geo = geolocation[
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ]
    ]

    df = sellers.merge(
        geo,
        left_on="seller_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
        validate="many_to_one",
    )

    df = df.rename(columns={
        "geolocation_lat": "seller_lat",
        "geolocation_lng": "seller_lng",
    })

    return df[
        [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
            "seller_lat",
            "seller_lng",
        ]
    ]


def build_dim_payment_type(dfs):
    """Identifica os tipos de pagamento existentes."""

    return (
        dfs["order_payments"][["payment_type"]]
        .drop_duplicates()
        .dropna()
        .sort_values("payment_type")
        .reset_index(drop=True)
    )


def build_dim_order_status(dfs):
    """Identifica os status de pedidos existentes."""

    return (
        dfs["orders"][["order_status"]]
        .drop_duplicates()
        .dropna()
        .sort_values("order_status")
        .reset_index(drop=True)
    )


def load_dimensions(conn, dfs):
    """Constrói e carrega todas as dimensões na Gold."""

    dimensions = [
        ("dim_date", build_dim_date(dfs), "date_key"),
        ("dim_customer", build_dim_customer(dfs), "customer_id"),
        ("dim_product", build_dim_product(dfs), "product_id"),
        ("dim_seller", build_dim_seller(dfs), "seller_id"),
        ("dim_payment_type", build_dim_payment_type(dfs), "payment_type"),
        ("dim_order_status", build_dim_order_status(dfs), "order_status"),
    ]

    for table, df, conflict_column in dimensions:
        insert_dimension(conn, table, df, conflict_column)

        print(f"{table}: {len(df):,} registros processados.")

    print("Dimensões carregadas com sucesso.")
