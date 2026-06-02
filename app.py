import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="Моніторинг територій",
    page_icon="🇺🇦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 1.2rem;
    }

    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 58%, #0f766e 100%);
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
    }

    .hero h1 {
        margin: 0 0 0.45rem 0;
        font-size: 2.05rem;
        line-height: 1.15;
    }

    .hero p {
        margin: 0;
        opacity: 0.92;
        font-size: 1.02rem;
    }

    .source-card {
        padding: 1rem 1.15rem;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.32);
        background: rgba(248, 250, 252, 0.84);
        margin-bottom: 1rem;
    }

    .small-note {
        color: #64748b;
        font-size: 0.9rem;
    }

    .footer {
        margin-top: 2.4rem;
        padding: 1rem 0 0.3rem 0;
        border-top: 1px solid rgba(148, 163, 184, 0.35);
        color: #64748b;
        text-align: center;
        font-size: 0.9rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(248, 250, 252, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 18px;
        padding: 0.75rem 0.9rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <h1>Моніторинг територій бойових дій та тимчасово окупованих територій</h1>
        <p>Інтерактивний перегляд офіційного переліку територій за областями, районами, громадами, категоріями та датами дії статусу.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

DATABASE_URL = st.secrets["DATABASE_URL"]


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)


engine = get_engine()


@st.cache_data(ttl=600)
def load_latest_document():
    documents_query = """
    select
        source_name,
        source_url,
        document_number,
        document_date,
        loaded_at
    from documents
    order by loaded_at desc
    limit 1;
    """
    return pd.read_sql(text(documents_query), engine)


@st.cache_data(ttl=600)
def load_territories():
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
    data = pd.read_sql(text(query), engine)
    data["status_from"] = pd.to_datetime(data["status_from"], errors="coerce")
    data["status_to"] = pd.to_datetime(data["status_to"], errors="coerce")
    data["loaded_at"] = pd.to_datetime(data["loaded_at"], errors="coerce")
    return data


latest_doc = load_latest_document()
df = load_territories()

if latest_doc.empty:
    st.warning("Інформацію про останній документ не знайдено в базі даних.")
else:
    doc = latest_doc.iloc[0]
    st.markdown(
        f"""
        <div class="source-card">
            <b>Джерело даних:</b> {doc['source_name']}<br>
            <b>Наказ:</b> №{doc['document_number']} від {doc['document_date']}<br>
            <b>Останнє оновлення бази:</b> {doc['loaded_at']}<br>
            <a href="{doc['source_url']}" target="_blank">Відкрити офіційне джерело</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

if df.empty:
    st.error("У базі даних немає записів для відображення.")
    st.stop()

min_date = df["status_from"].min()
max_known_date = df["status_to"].max()
open_statuses = df["status_to"].isna().sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Усього записів у базі", f"{len(df):,}".replace(",", " "))
kpi2.metric("Областей", df["oblast"].dropna().nunique())
kpi3.metric("Районів", df["rayon"].dropna().nunique())
kpi4.metric("Записів без кінцевої дати", f"{open_statuses:,}".replace(",", " "))

with st.expander("Що показує цей моніторинг"):
    st.write(
        "Система дозволяє перевірити, який статус мала територія на обрану дату, "
        "відфільтрувати записи за областю, районом і категорією, а також переглянути історію "
        "конкретної громади, району або області. Дані слід трактувати як технічне відображення "
        "офіційного переліку, а не як окремий нормативно-правовий акт. Для юридичного використання "
        "варто звіряти результат із посиланням на офіційне джерело."
    )

st.sidebar.header("Параметри перегляду")
st.sidebar.caption("Фільтри застосовуються до вкладки зі станом на дату.")

selected_date = st.sidebar.date_input("Дата", value=pd.Timestamp.today())

oblasts = ["Усі"] + sorted(df["oblast"].dropna().unique().tolist())
selected_oblast = st.sidebar.selectbox("Область", oblasts)

temp_for_rayon = df.copy()
if selected_oblast != "Усі":
    temp_for_rayon = temp_for_rayon[temp_for_rayon["oblast"] == selected_oblast]

rayons = ["Усі"] + sorted(temp_for_rayon["rayon"].dropna().unique().tolist())
selected_rayon = st.sidebar.selectbox("Район", rayons)

categories = ["Усі"] + sorted(df["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Категорія", categories)
search_text = st.sidebar.text_input("Пошук громади")

filtered = df.copy()
selected_date = pd.to_datetime(selected_date)
filtered = filtered[
    (filtered["status_from"] <= selected_date)
    & (filtered["status_to"].isna() | (filtered["status_to"] >= selected_date))
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


def prepare_display_table(data):
    table = data.copy()
    table["status_from"] = table["status_from"].dt.strftime("%d.%m.%Y")
    table["status_to"] = table["status_to"].dt.strftime("%d.%m.%Y").fillna("чинний / не зазначено")
    table["loaded_at"] = table["loaded_at"].dt.strftime("%d.%m.%Y %H:%M").fillna("")
    table = table.rename(
        columns={
            "hromada_code_7": "Код громади",
            "territory_name": "Назва території",
            "oblast": "Область",
            "rayon": "Район",
            "category": "Категорія",
            "status_from": "Початок статусу",
            "status_to": "Кінець статусу",
            "loaded_at": "Завантажено в базу",
        }
    )
    return table


tab1, tab2, tab3 = st.tabs(["Станом на дату", "Історія території", "Аналітика"])

with tab1:
    st.subheader("Станом на дату")
    st.markdown(
        f"<span class='small-note'>Показано записи, чинні станом на {selected_date.strftime('%d.%m.%Y')}.</span>",
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Кількість записів", f"{len(filtered):,}".replace(",", " "))
    m2.metric("Областей у вибірці", filtered["oblast"].dropna().nunique())
    m3.metric("Категорій у вибірці", filtered["category"].dropna().nunique())

    st.dataframe(prepare_display_table(filtered), use_container_width=True, hide_index=True)

    st.download_button(
        label="Завантажити CSV",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="territories_filtered.csv",
        mime="text/csv",
    )

with tab2:
    st.subheader("Історія громади / району / області")

    search_hromada = st.text_input(
        "Введи назву громади, району, області або код",
        key="history_search",
    )

    history = df.copy()

    if search_hromada:
        mask = (
            history["territory_name"].str.contains(search_hromada, case=False, na=False)
            | history["hromada_code_7"].astype(str).str.contains(search_hromada, case=False, na=False)
            | history["rayon"].str.contains(search_hromada, case=False, na=False)
            | history["oblast"].str.contains(search_hromada, case=False, na=False)
        )

        history = history[mask].sort_values(["territory_name", "status_from"])

        st.metric("Кількість записів", f"{len(history):,}".replace(",", " "))
        st.dataframe(prepare_display_table(history), use_container_width=True, hide_index=True)
    else:
        st.info("Введи назву громади, району, області або код, щоб побачити історію.")

with tab3:
    st.subheader("Аналітичний зріз")

    if filtered.empty:
        st.info("Для обраних фільтрів немає даних для аналітики.")
    else:
        category_stats = (
            filtered.groupby("category", dropna=False)
            .size()
            .reset_index(name="Кількість записів")
            .sort_values("Кількість записів", ascending=False)
        )

        oblast_stats = (
            filtered.groupby("oblast", dropna=False)
            .size()
            .reset_index(name="Кількість записів")
            .sort_values("Кількість записів", ascending=False)
        )

        left, right = st.columns([1, 1])
        with left:
            st.write("Розподіл за категоріями")
            st.bar_chart(category_stats, x="category", y="Кількість записів")

        with right:
            st.write("Топ областей за кількістю записів")
            st.dataframe(oblast_stats.head(10), use_container_width=True, hide_index=True)

        top_category = category_stats.iloc[0]["category"]
        top_count = int(category_stats.iloc[0]["Кількість записів"])
        st.info(
            f"Найбільша категорія у поточній вибірці: {top_category} — {top_count} записів. "
            "Цей блок можна розширити до автоматичної короткої аналітичної довідки для звіту."
        )

st.markdown(
    """
    <div class="footer">
        Створено Єфремовим Арсеном<br>
        Інструмент для зручного перегляду офіційних даних щодо територій бойових дій та тимчасово окупованих територій.
    </div>
    """,
    unsafe_allow_html=True,
)
