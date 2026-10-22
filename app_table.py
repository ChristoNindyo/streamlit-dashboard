import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

st.set_page_config(page_title="MySQL Table", layout="wide")
st.title("Data Table")


@st.cache_resource
def get_engine():
    cfg = st.secrets["mysql"]
    url = URL.create(
        "mysql+pymysql",
        username=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        database=cfg["database"],
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=300)
def load_data():
    query = "SELECT * FROM view_penerimaannbebanPMB_kelompok ORDER BY tglspk DESC LIMIT 100"
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


if st.button("Refresh data"):
    st.cache_data.clear()

try:
    df = load_data()
    st.caption(f"{len(df)} rows")
    st.dataframe(df, width="stretch")
except Exception as e:
    st.error(f"Could not load data: {e}")