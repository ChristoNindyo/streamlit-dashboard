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
def get_date_bounds():
    query = text(
        f"SELECT MIN({DATE_COL}), MAX({DATE_COL}) FROM {TABLE} "
        f"WHERE {DATE_COL} >= '1900-01-01' AND {DATE_COL} <= '2100-12-31'"
    )
    with get_engine().connect() as conn:
        row = conn.execute(query).one()
    return row[0], row[1]


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
    lo, hi = get_date_bounds()

    if lo is None or hi is None:
        st.warning("No dates found in the data.")
    else:
        lo = pd.to_datetime(lo).date()
        hi = pd.to_datetime(hi).date()

        if lo == hi:
            start, end = lo, hi
            st.info(f"All data is on a single date: {lo}")
        else:
            default_start = max(lo, hi - dt.timedelta(days=30))
            start, end = st.slider(
                "Filter by tglspk",
                min_value=lo,
                max_value=hi,
                value=(default_start, hi),
                format="YYYY-MM-DD",
            )

        df = load_data(start, end)
        st.caption(f"{len(df)} rows  |  {start} to {end}")
        if len(df) >= MAX_ROWS:
            st.warning(f"Showing only the latest {MAX_ROWS} rows. Narrow the date range to see everything.")
        st.dataframe(df, width="stretch")
except Exception as e:
    st.error(f"Could not load data: {e}")