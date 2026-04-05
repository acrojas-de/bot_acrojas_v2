import streamlit as st

from app.bootstrap import bootstrap
from app.binance_client import get_spot_portfolio

st.set_page_config(page_title="Binance Dashboard", layout="wide")

st.title("📊 Dashboard Trading")

client, state = bootstrap()

st.markdown("### 🧾 Cartera Spot (USDT)")

portfolio = get_spot_portfolio(client)

if portfolio:
    st.dataframe(portfolio, use_container_width=True)
else:
    st.info("No hay activos en cartera.")