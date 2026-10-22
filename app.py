import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="My First Dashboard", layout="wide")
st.title("My First Dashboard")

PRODUCTS = ["Product A", "Product B", "Product C"]

# ----- Sidebar (filters) -----
st.sidebar.header("Filters")
days = st.sidebar.slider("Number of days", min_value=7, max_value=90, value=30)
selected = st.sidebar.multiselect("Products", PRODUCTS, default=PRODUCTS)

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()


# ----- Dummy data -----
@st.cache_data
def make_data(days):
    rng = np.random.default_rng()
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    data = {"date": dates}
    for name in PRODUCTS:
        data[name] = 100 + rng.normal(0, 5, days).cumsum()
    return pd.DataFrame(data).set_index("date").round(1)


df = make_data(days)

# ----- Main page -----
if not selected:
    st.warning("Please select at least one product in the sidebar.")
else:
    st.subheader("Sales trend")
    st.line_chart(df[selected])

    st.subheader("Data table")
    st.dataframe(df[selected])
