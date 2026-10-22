import datetime as dt

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

TABLE = "view_penerimaannbebanLSN"
DATE_COL = "tglspk"
MAX_ROWS = 10000  # safety limit so the page doesn't get too heavy

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
def load_summary(start, end):
    query = text(
        f"SELECT cabang, "
        f"MAX(tglinputspk) AS max_tglinputspk, "
        f"SUM(panel) AS sum_panel, "
        f"COUNT(DISTINCT no_spk) AS count_spk "
        f"FROM {TABLE} "
        f"WHERE {DATE_COL} >= :start AND {DATE_COL} < :end_next "
        f"GROUP BY cabang "
        f"ORDER BY cabang"
    )
    params = {"start": start, "end_next": end + dt.timedelta(days=1)}
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn, params=params)


@st.cache_data(ttl=300)
def load_data(start, end):
    query = text(
        f"SELECT * FROM {TABLE} "
        f"WHERE {DATE_COL} >= :start AND {DATE_COL} < :end_next "
        f"ORDER BY {DATE_COL} DESC LIMIT {MAX_ROWS}"
    )
    params = {"start": start, "end_next": end + dt.timedelta(days=1)}
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn, params=params)


if st.button("Refresh data"):
    st.cache_data.clear()

try:
    # Slider range: last 1 year up to today
    hi = dt.date.today()
    lo = hi - dt.timedelta(days=365)

    default_start = max(lo, hi - dt.timedelta(days=30))
    start, end = st.slider(
        "Filter by tglspk",
        min_value=lo,
        max_value=hi,
        value=(default_start, hi),
        format="YYYY-MM-DD",
    )

    # ----- Summary table -----
    st.subheader("Summary by cabang")
    summary = load_summary(start, end)
    st.dataframe(summary, width="stretch", hide_index=True)

    # ----- Detail table -----
    st.subheader("Data")
    df = load_data(start, end)
    st.caption(f"{len(df)} rows  |  {start} to {end}")
    if len(df) >= MAX_ROWS:
        st.warning(f"Showing only the latest {MAX_ROWS} rows. Narrow the date range to see everything.")
    st.dataframe(df, width="stretch")
except Exception as e:
    st.error(f"Could not load data: {e}")