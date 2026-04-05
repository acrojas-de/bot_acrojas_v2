import streamlit as st
from app.bootstrap import bootstrap

from app.binance_client import (
    get_spot_portfolio,
    get_spot_trade_history,
    calculate_spot_positions,
)

st.set_page_config(page_title="Panel de Binance", layout="wide")

st.title("📊 Trading en panel de control")

# 👉 CREAS CLIENT AQUÍ
client, state = bootstrap()

# ========================
# 💼 CARTERA
# ========================
st.markdown("## 🧾 Cartera Spot (USDT)")

portfolio = get_spot_portfolio(client)

if portfolio:
    total_usdt = round(sum(p["value_usdt"] for p in portfolio), 2)
    st.metric("Valor total estimado", f"{total_usdt} USDT")
    st.dataframe(portfolio, use_container_width=True)
else:
    st.info("No hay activos en cartera.")

# ========================
# 📜 HISTORIAL
# ========================
st.markdown("## 🧾 Historial Spot reciente")

history = get_spot_trade_history(client)

if history:
    st.dataframe(history, use_container_width=True)
else:
    st.info("No hay historial reciente disponible.")

# ========================
# 💹 POSICIONES (AQUÍ VA)
# ========================
st.markdown("## 💹 Posiciones Spot")

positions = calculate_spot_positions(client)

if positions:
    st.dataframe(positions, use_container_width=True)
else:
    st.info("No hay posiciones calculadas.")