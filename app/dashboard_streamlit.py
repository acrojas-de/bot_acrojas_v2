import streamlit as st
from app.bootstrap import bootstrap
from app.binance_client import get_spot_portfolio

st.set_page_config(page_title="Panel de Binance", layout="wide")

st.title("📊 Trading en panel de control")
st.markdown("## 🧾 Cartera Spot (USDT)")

client, state = bootstrap()
portfolio = get_spot_portfolio(client)

if portfolio:
    total_usdt = round(sum(p["value_usdt"] for p in portfolio), 2)
    st.metric("Valor total estimado", f"{total_usdt} USDT")
    st.dataframe(portfolio, use_container_width=True)
else:
    st.info("No hay activos en cartera.")