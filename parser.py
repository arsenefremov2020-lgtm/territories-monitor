import os
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

test_row = pd.DataFrame([{
    "full_code": "UA00000000000000000",
    "hromada_code_7": "0000000",
    "territory_name": "Тестова громада",
    "oblast": "Тестова область",
    "rayon": "Тестовий район",
    "category": "Тестова категорія",
    "status_from": "2026-01-01",
    "status_to": None
}])

test_row.to_sql(
    "territory_status_history",
    engine,
    if_exists="append",
    index=False
)

print("Test row inserted successfully")
