import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Territories Monitor", layout="wide")

st.title("Territories Monitor")
st.write("Система моніторингу територій бойових дій та тимчасово окупованих територій")

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

query = """
select
    hromada_code_7,
    territory_name,
    oblast,
    rayon,
    category,
    status_from,
    status_to,
    loaded_at
from territory_status_history
order by territory_name;
"""

try:
    df = pd.read_sql(text(query), engine)

    st.subheader("Дані з бази")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("Не вдалося підключитися до бази або прочитати дані.")
    st.write(e)
