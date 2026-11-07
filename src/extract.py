import pandas as pd
from . import config


def extract_orders():
    orders = pd.read_csv(config.DATA_RAW / config.RAW_FILES["orders"])
    return orders

def extract_geolocation():
    geolocation = pd.read_csv(config.DATA_RAW / config.RAW_FILES["geolocation"])
    return geolocation

def extract_customers():
    customers = pd.read_csv(config.DATA_RAW / config.RAW_FILES["customers"])
    return customers

def extract_products():
    products = pd.read_csv(config.DATA_RAW / config.RAW_FILES["products"])
    return products

def extract_sellers():
    sellers = pd.read_csv(config.DATA_RAW / config.RAW_FILES["sellers"])
    return sellers

def extract_order_items():
    order_items = pd.read_csv(config.DATA_RAW / config.RAW_FILES["order_items"])
    return order_items

def extract_order_payments():
    order_payments = pd.read_csv(config.DATA_RAW / config.RAW_FILES["order_payments"])
    return order_payments

def extract_order_reviews():
    order_reviews = pd.read_csv(config.DATA_RAW / config.RAW_FILES["order_reviews"])
    return order_reviews

def extract_category_translation():
    category_translation = pd.read_csv(config.DATA_RAW / config.RAW_FILES["category_translation"])
    return category_translation

def extract_all_dfs():
    dataframes = {
        "orders": extract_orders(),
        "geolocation": extract_geolocation(),
        "customers": extract_customers(),
        "products": extract_products(),
        "sellers": extract_sellers(),
        "order_items": extract_order_items(),
        "order_payments": extract_order_payments(),
        "order_reviews": extract_order_reviews(),
        "category_translation": extract_category_translation()
    }
    return dataframes


df_orders = extract_orders()
df_geolocation = extract_geolocation()
df_customers = extract_customers()
df_products = extract_products()
df_sellers = extract_sellers()
df_order_items = extract_order_items()
df_order_payments = extract_order_payments()
df_order_reviews = extract_order_reviews()
df_category_translation = extract_category_translation()

df_all_dataframes = extract_all_dfs()