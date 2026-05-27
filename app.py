import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="Territories Monitor", layout="wide")

st.title("Territories Monitor")
st.write("Система моніторингу територій бойових дій та тимчасово окупованих територій")

st.info("Наступний крок — підключення до бази Supabase і виведення таблиці.")
