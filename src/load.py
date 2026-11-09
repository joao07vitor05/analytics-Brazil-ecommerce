import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# URL de conexão. Ajuste os valores padrão para os do seu container,
# ou defina a variável de ambiente DATABASE_URL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5435/olist",
)

# Caminho do schema (pasta sql/ na raiz do projeto)
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"

# Ordem de carga: tabelas "pai" primeiro, por causa das chaves estrangeiras.
# (nome da tabela no banco, chave do dicionário vindo do transform)
LOAD_ORDER = [
    ("geolocation", "geolocation_agg"),
    ("category_translation", "category_translation"),
    ("customers", "customers"),
    ("sellers", "sellers"),
    ("products", "products"),
    ("orders", "orders"),
    ("order_items", "order_items"),
    ("order_payments", "order_payments"),
    ("order_reviews", "order_reviews"),
]

# Chaves primárias de cada tabela (espelham o schema.sql)
PRIMARY_KEYS = {
    "geolocation_agg": ["geolocation_zip_code_prefix"],
    "category_translation": ["product_category_name"],
    "customers": ["customer_id"],
    "sellers": ["seller_id"],
    "products": ["product_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id", "order_id"],
}

# Chaves estrangeiras: (tabela filha, coluna, tabela pai, coluna pai)
FOREIGN_KEYS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
]


def validate(dfs):
    """Confere duplicatas de chave primária e registros órfãos antes da carga."""
    errors = []

    for name, cols in PRIMARY_KEYS.items():
        n_dup = dfs[name].duplicated(subset=cols).sum()
        if n_dup:
            errors.append(f"{name}: {n_dup} linhas com chave duplicada em {cols}")

    for child, col, parent, parent_col in FOREIGN_KEYS:
        orphans = ~dfs[child][col].isin(dfs[parent][parent_col])
        if orphans.sum():
            errors.append(
                f"{child}.{col}: {orphans.sum()} valores sem correspondente "
                f"em {parent}.{parent_col}"
            )

    if errors:
        raise ValueError("Validação falhou:\n- " + "\n- ".join(errors))
    print("Validação OK.")


def create_schema(engine):
    """Executa o schema.sql (recria todas as tabelas do zero)."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("Schema criado.")


def load_all(dfs):
    """Valida, cria o schema e carrega todas as tabelas no PostgreSQL."""
    validate(dfs)

    engine = create_engine(DATABASE_URL)
    create_schema(engine)

    for table, key in LOAD_ORDER:
        dfs[key].to_sql(
            table,
            engine,
            if_exists="append",  # o schema já existe; só insere os dados
            index=False,
            method="multi",
            chunksize=5000,
        )
        print(f"{table}: {len(dfs[key])} linhas carregadas.")

    engine.dispose()