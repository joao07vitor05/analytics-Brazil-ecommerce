"""
Configurações centrais do projeto.

Todos os caminhos e credenciais ficam aqui, para que nenhum outro arquivo
precise "chutar" onde estão os dados ou qual é a senha do banco.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# --- Caminhos -------------------------------------------------------------
# config.py está em src/, então a raiz do projeto é o pai da pasta src
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Cria a pasta de saída caso ainda não exista
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# --- Arquivos do dataset ----------------------------------------------------
# Chave = nome curto que usaremos no código; valor = nome do CSV do Kaggle
RAW_FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}