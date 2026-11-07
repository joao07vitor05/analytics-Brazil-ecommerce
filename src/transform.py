import pandas as pd
import config
import extract

def transform_orders(df_orders):
    df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'])