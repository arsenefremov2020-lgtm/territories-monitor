import streamlit as st
import pandas as pd
import pydeck as pdk
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

    .map-note {
        padding: 0.85rem 1rem;
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.22);
        background: rgba(239, 246, 255, 0.86);
        color: #1e3a8a;
        margin-bottom: 1rem;
        font-size: 0.94rem;
    }

    .insight-card {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.3);
        background: rgba(248, 250, 252, 0.92);
        margin-top: 0.7rem;
        margin-bottom: 0.7rem;
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

OBLAST_COORDS = {
    "автономна республіка крим": {"lat": 45.3529, "lon": 34.5054, "label": "Автономна Республіка Крим"},
    "вінницька": {"lat": 49.2331, "lon": 28.4682, "label": "Вінницька область"},
    "волинська": {"lat": 50.7472, "lon": 25.3254, "label": "Волинська область"},
    "дніпропетровська": {"lat": 48.4647, "lon": 35.0462, "label": "Дніпропетровська область"},
    "донецька": {"lat": 48.0159, "lon": 37.8029, "label": "Донецька область"},
    "житомирська": {"lat": 50.2547, "lon": 28.6587, "label": "Житомирська область"},
    "закарпатська": {"lat": 48.6208, "lon": 22.2879, "label": "Закарпатська область"},
    "запорізька": {"lat": 47.8388, "lon": 35.1396, "label": "Запорізька область"},
    "івано-франківська": {"lat": 48.9226, "lon": 24.7111, "label": "Івано-Франківська область"},
    "київська": {"lat": 50.4501, "lon": 30.5234, "label": "Київська область"},
    "кіровоградська": {"lat": 48.5079, "lon": 32.2623, "label": "Кіровоградська область"},
    "луганська": {"lat": 48.5740, "lon": 39.3078, "label": "Луганська область"},
    "львівська": {"lat": 49.8397, "lon": 24.0297, "label": "Львівська область"},
    "миколаївська": {"lat": 46.9750, "lon": 31.9946, "label": "Миколаївська область"},
    "одеська": {"lat": 46.4825, "lon": 30.7233, "label": "Одеська область"},
    "полтавська": {"lat": 49.5883, "lon": 34.5514, "label": "Полтавська область"},
    "рівненська": {"lat": 50.6199, "lon": 26.2516, "label": "Рівненська область"},
    "сумська": {"lat": 50.9077, "lon": 34.7981, "label": "Сумська область"},
    "тернопільська": {"lat": 49.5535, "lon": 25.5948, "label": "Тернопільська область"},
    "харківська": {"lat": 49.9935, "lon": 36.2304, "label": "Харківська область"},
    "херсонська": {"lat": 46.6354, "lon": 32.6169, "label": "Херсонська область"},
    "хмельницька": {"lat": 49.4229, "lon": 26.9871, "label": "Хмельницька область"},
    "черкаська": {"lat": 49.4444, "lon": 32.0598, "label": "Черкаська область"},
    "чернівецька": {"lat": 48.2915, "lon": 25.9403, "label": "Чернівецька область"},
    "чернігівська": {"lat": 51.4982, "lon": 31.2893, "label": "Чернігівська область"},
}

CATEGORY_COLORS = {
    "Території можливих бойових дій": [59, 130, 246, 165],
    "Території бойових дій": [245, 158, 11, 175],
    "Території активних бойових дій": [220, 38, 38, 185],
    "Тимчасово окуповані території": [88, 28, 135, 180],
}
DEFAULT_COLOR = [15, 118, 110, 165]


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


def normalize_oblast_name(value):
    if pd.isna(value):
        return None

    normalized = str(value).strip().lower()
    normalized = normalized.replace("область", "")
    normalized = normalized.replace("м.", "")
    normalized = " ".join(normalized.split())
    return normalized


def dominant_category(categories):
    if categories.empty:
        return "Немає даних"
    return categories.value_counts().idxmax()


def build_oblast_map_data(data):
    if data.empty:
        return pd.DataFrame(
            columns=[
                "oblast",
                "lat",
                "lon",
                "records",
                "communities",
                "dominant_category",
                "radius",
                "color",
            ]
        )

    prepared = data.assign(oblast_key=data["oblast"].apply(normalize_oblast_name))

    grouped = (
        prepared.groupby("oblast_key", dropna=True)
        .agg(
            records=("territory_name", "size"),
            communities=("hromada_code_7", "nunique"),
            dominant_category=("category", dominant_category),
        )
        .reset_index()
    )

    rows = []
    max_records = max(grouped["records"].max(), 1)

    for _, row in grouped.iterrows():
        coords = OBLAST_COORDS.get(row["oblast_key"])
        if not coords:
            continue

        records = int(row["records"])
        dominant = row["dominant_category"]
        rows.append(
            {
                "oblast": coords["label"],
                "lat": coords["lat"],
                "lon": coords["lon"],
                "records": records,
                "communities": int(row["communities"]),
                "dominant_category": dominant,
                "radius": 16000 + int((records / max_records) * 52000),
                "color": CATEGORY_COLORS.get(dominant, DEFAULT_COLOR),
            }
        )

    return pd.DataFrame(rows).sort_values("records", ascending=False)


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


def render_pydeck_map(map_data):
    if map_data.empty:
        return

    center_lat = float(map_data["lat"].mean())
    center_lon = float(map_data["lon"].mean())
    zoom = 5 if len(map_data) > 1 else 6

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=0,
    )

    tooltip = {
        "html": "<b>{oblast}</b><br/>Записів: {records}<br/>Громад: {communities}<br/>Переважна категорія: {dominant_category}",
        "style": {
            "backgroundColor": "#0f172a",
            "color": "white",
            "fontSize": "13px",
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None,
    )

    st.pydeck_chart(deck, use_container_width=True)


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
st.sidebar.caption("Фільтри застосовуються до таблиці, аналітики та карти.")

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

map_data = build_oblast_map_data(filtered)

tab1, tab2, tab3, tab4 = st.tabs(["Станом на дату", "Історія території", "Аналітика", "Карта"])

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

with tab4:
    st.subheader("Карта та просторовий зріз")
    st.markdown(
        """
        <div class="map-note">
            Карта показує оглядову концентрацію записів за областями. Розмір точки залежить від кількості записів,
            а колір — від переважної категорії у відповідній області для поточної вибірки.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if map_data.empty:
        st.info("Для обраних фільтрів немає даних, які можна показати на карті.")
    else:
        map_metric_1, map_metric_2, map_metric_3, map_metric_4 = st.columns(4)
        map_metric_1.metric("Областей на карті", len(map_data))
        map_metric_2.metric("Записів у вибірці", f"{int(map_data['records'].sum()):,}".replace(",", " "))
        map_metric_3.metric("Громад у вибірці", f"{int(map_data['communities'].sum()):,}".replace(",", " "))
        map_metric_4.metric("Найбільша область", map_data.iloc[0]["oblast"])

        map_left, map_right = st.columns([2.2, 1])

        with map_left:
            render_pydeck_map(map_data)

        with map_right:
            st.write("Легенда категорій")
            legend_items = pd.DataFrame(
                [
                    {"Категорія": "Можливі бойові дії", "Позначення": "синя точка"},
                    {"Категорія": "Бойові дії", "Позначення": "помаранчева точка"},
                    {"Категорія": "Активні бойові дії", "Позначення": "червона точка"},
                    {"Категорія": "Тимчасово окуповані", "Позначення": "фіолетова точка"},
                ]
            )
            st.dataframe(legend_items, use_container_width=True, hide_index=True)

            st.write("Топ областей")
            st.dataframe(
                map_data[["oblast", "records", "communities", "dominant_category"]]
                .rename(
                    columns={
                        "oblast": "Область",
                        "records": "Записів",
                        "communities": "Громад",
                        "dominant_category": "Переважна категорія",
                    }
                )
                .head(10),
                use_container_width=True,
                hide_index=True,
            )

        top_oblast = map_data.iloc[0]["oblast"]
        top_records = int(map_data.iloc[0]["records"])
        total_records = int(map_data["records"].sum())
        top_share = round(top_records / total_records * 100, 1) if total_records else 0
        top_dominant_category = map_data.iloc[0]["dominant_category"]

        st.markdown(
            f"""
            <div class="insight-card">
                <b>Короткий висновок по карті.</b><br>
                Найбільша концентрація записів у поточній вибірці припадає на <b>{top_oblast}</b> — {top_records} записів,
                або близько {top_share}% від усіх записів, відображених на карті. Переважна категорія для цієї області:
                <b>{top_dominant_category}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Обмеження цієї карти"):
            st.write(
                "Це не карта меж громад. Вона показує агреговану картину по областях, тому її варто використовувати "
                "для швидкого огляду концентрації записів. Для точного просторового аналізу потрібно додати geojson "
                "меж громад або районів і зв'язати його з кодами територій."
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
