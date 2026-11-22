
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from src.gold.dimensions import load_dimensions
from src.gold.facts import load_facts


ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT_DIR / "sql" / "gold_schema.sql"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5435/olist"
)

# Tabelas que serão lidas da camada Silver.
SILVER_TABLES = [
    "customers",
    "sellers",
    "products",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "geolocation",
]


def read_silver_tables(engine):
    """
    Lê as tabelas da camada Silver e retorna um dicionário
    de DataFrames para utilização na camada Gold.
    """

    dfs = {}

    with engine.connect() as conn:
        for table in SILVER_TABLES:
            dfs[table] = pd.read_sql_table(
                table_name=table,
                con=conn
            )

    # A tabela geolocation será utilizada com o nome
    # esperado pelas funções de construção das dimensões.
    dfs["geolocation_agg"] = dfs.pop("geolocation")

    return dfs


def create_gold_tables(engine):
    """
    Executa o arquivo SQL responsável pela criação
    do schema e das tabelas da camada Gold.
    """

    sql = SCHEMA_FILE.read_text(encoding="utf-8")

    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def main():
    engine = create_engine(DATABASE_URL)

    print("Iniciando carga da camada Gold...")

    try:
        # 1. Ler dados da Silver
        dfs = read_silver_tables(engine)

        print("Tabelas Silver carregadas.")

        # 2. Criar estrutura Gold
        create_gold_tables(engine)

        print("Estrutura Gold criada.")

        # 3. Carregar dimensões
        with engine.begin() as conn:
            load_dimensions(conn, dfs)

        print("Dimensões carregadas.")

        # 4. Carregar fatos
        with engine.begin() as conn:
            load_facts(conn, dfs)

        print("Tabelas fato carregadas.")

        print("\nCarga da camada Gold concluída com sucesso!")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
