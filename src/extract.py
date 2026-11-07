import pandas as pd
 
from . import config
 
# Colunas de ID e CEP lidas como string desde o início,
# preservando zeros à esquerda e evitando conversões erradas.
DTYPES = {
    "orders": {"order_id": "string", "customer_id": "string"},
    "geolocation": {"geolocation_zip_code_prefix": "string"},
    "customers": {
        "customer_id": "string",
        "customer_unique_id": "string",
        "customer_zip_code_prefix": "string",
    },
    "products": {"product_id": "string"},
    "sellers": {"seller_id": "string", "seller_zip_code_prefix": "string"},
    "order_items": {
        "order_id": "string",
        "product_id": "string",
        "seller_id": "string",
    },
    "order_payments": {"order_id": "string"},
    "order_reviews": {"review_id": "string", "order_id": "string"},
    "category_translation": {},
}
 
 
def extract_table(name):
    """Lê um CSV bruto pelo nome da tabela (chave de config.RAW_FILES)."""
    path = config.DATA_RAW / config.RAW_FILES[name]
    return pd.read_csv(path, dtype=DTYPES.get(name, {}))
 
 
def extract_all_dfs():
    """Lê todas as tabelas e devolve um dicionário de DataFrames."""
    return {name: extract_table(name) for name in config.RAW_FILES}
 