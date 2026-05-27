import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Territories Monitor", layout="wide")

st.title("Territories Monitor")
st.caption("Моніторинг територій бойових дій та тимчасово окупованих територій")

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

df = pd.read_sql(text(query), engine)

tab1, tab2 = st.tabs(["Станом на дату", "Історія громади"])

with tab1:
    st.subheader("Станом на дату")

    selected_date = st.date_input("Дата", value=pd.Timestamp.today())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        oblasts = ["Усі"] + sorted(df["oblast"].dropna().unique().tolist())
        selected_oblast = st.selectbox("Область", oblasts)

    temp_for_rayon = df.copy()
    if selected_oblast != "Усі":
        temp_for_rayon = temp_for_rayon[temp_for_rayon["oblast"] == selected_oblast]

    with col2:
        rayons = ["Усі"] + sorted(temp_for_rayon["rayon"].dropna().unique().tolist())
        selected_rayon = st.selectbox("Район", rayons)

    with col3:
        categories = ["Усі"] + sorted(df["category"].dropna().unique().tolist())
        selected_category = st.selectbox("Категорія", categories)

    with col4:
        search_text = st.text_input("Пошук громади")

    filtered = df.copy()

    filtered["status_from"] = pd.to_datetime(filtered["status_from"])
    filtered["status_to"] = pd.to_datetime(filtered["status_to"])

    selected_date = pd.to_datetime(selected_date)

    filtered = filtered[
        (filtered["status_from"] <= selected_date)
        & (
            filtered["status_to"].isna()
            | (filtered["status_to"] >= selected_date)
        )
    ]

    if selected_oblast != "Усі":
        filtered = filtered[filtered["oblast"] == selected_oblast]

    if selected_rayon != "Усі":
        filtered = filtered[filtered["rayon"] == selected_rayon]

    if selected_category != "Усі":
        filtered = filtered[filtered["category"] == selected_category]

    if search_text:
        filtered = filtered[
            filtered["territory_name"].str.contains(search_text, case=False, na=False)
        ]

    st.metric("Кількість записів", len(filtered))

    st.dataframe(filtered, use_container_width=True)

with tab2:
    st.subheader("Історія громади / району / області")

    search_hromada = st.text_input(
        "Введи назву громади, району, області або код",
        key="history_search"
    )

    history = df.copy()

    if search_hromada:
        mask = (
            history["territory_name"].str.contains(search_hromada, case=False, na=False)
            | history["hromada_code_7"].str.contains(search_hromada, case=False, na=False)
            | history["rayon"].str.contains(search_hromada, case=False, na=False)
            | history["oblast"].str.contains(search_hromada, case=False, na=False)
        )

        history = history[mask]

        st.metric("Кількість записів", len(history))
        st.dataframe(history, use_container_width=True)

    else:
        st.info("Введи назву громади, району, області або код, щоб побачити історію.")
