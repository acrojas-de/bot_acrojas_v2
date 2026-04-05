import streamlit as st
import pandas as pd

from app.bootstrap import bootstrap
from app.binance_client import (
    get_spot_portfolio,
    get_spot_trade_history,
    calculate_spot_positions,
)


def color_pnl(val):
    try:
        val = float(val)
        if val > 0:
            return "color: #16a34a; font-weight: bold;"
        elif val < 0:
            return "color: #dc2626; font-weight: bold;"
        return ""
    except Exception:
        return ""


def color_numeric_blue(val):
    try:
        float(val)
        return "color: #1d4ed8; font-weight: 600;"
    except Exception:
        return ""


def color_price_current(val):
    try:
        float(val)
        return "color: #ca8a04; font-weight: bold;"
    except Exception:
        return ""


def highlight_pnl_row(row):
    try:
        pnl = float(row["pnl_usdt"])
        if pnl > 0:
            return ["background-color: #f0fdf4;"] * len(row)
        elif pnl < 0:
            return ["background-color: #fef2f2;"] * len(row)
        return [""] * len(row)
    except Exception:
        return [""] * len(row)


def color_side(val):
    try:
        if val == "BUY":
            return "background-color: #dcfce7; color: #166534; font-weight: bold;"
        elif val == "SELL":
            return "background-color: #fee2e2; color: #991b1b; font-weight: bold;"
        return ""
    except Exception:
        return ""


st.set_page_config(page_title="Panel de Binance", layout="wide")

st.title("📊 Trading en panel de control")

client, state = bootstrap()

# ========================
# 💼 CARTERA
# ========================
st.markdown("## 🧾 Cartera Spot (USDT)")

portfolio = get_spot_portfolio(client)

if portfolio:
    total_usdt = round(sum(p["value_usdt"] for p in portfolio), 2)
    st.metric("Valor total estimado", f"{total_usdt} USDT")

    df_portfolio = pd.DataFrame(portfolio)

    styled_portfolio = (
        df_portfolio.style
        .map(color_numeric_blue, subset=["price", "value_usdt"])
    )

    st.write(styled_portfolio)
else:
    st.info("No hay activos en cartera.")

# ========================
# 📜 HISTORIAL
# ========================
st.markdown("## 🧾 Historial Spot reciente")

history = get_spot_trade_history(client)

if history:
    df_history = pd.DataFrame(history)

    styled_history = (
        df_history.style
        .map(color_side, subset=["side"])
        .map(color_numeric_blue, subset=["price", "qty", "quote_qty"])
    )

    st.write(styled_history)
else:
    st.info("No hay historial reciente disponible.")

# ========================
# 💹 POSICIONES
# ========================
st.markdown("## 💹 Posiciones Spot")

positions = calculate_spot_positions(client)

# 💰 resumen global
total_pnl = sum(p["pnl_usdt"] for p in positions) if positions else 0

col1, col2 = st.columns(2)

with col1:
    st.metric("💰 PnL total", f"{round(total_pnl, 2)} USDT")

with col2:
    if total_pnl > 0:
        st.success("🟢 En ganancias")
    elif total_pnl < 0:
        st.error("🔴 En pérdidas")
    else:
        st.info("⚪ Neutral")

# 🚨 alertas
if positions:
    for p in positions:
        if p["pnl_pct"] > 50:
            st.success(f"🚀 {p['asset']} +{p['pnl_pct']}% (TAKE PROFIT?)")
        elif p["pnl_pct"] < -20:
            st.error(f"⚠️ {p['asset']} {p['pnl_pct']}% (STOP LOSS?)")

if positions:
    df_positions = pd.DataFrame(positions)

    top_winner = df_positions.sort_values("pnl_usdt", ascending=False).iloc[0]
    top_loser = df_positions.sort_values("pnl_usdt", ascending=True).iloc[0]

    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            "🏆 Top ganador",
            top_winner["asset"],
            f"{top_winner['pnl_usdt']} USDT ({top_winner['pnl_pct']}%)",
        )

    with col4:
        st.metric(
            "⚠️ Top perdedor",
            top_loser["asset"],
            f"{top_loser['pnl_usdt']} USDT ({top_loser['pnl_pct']}%)",
        )

    styled_positions = (
        df_positions.style
        .apply(highlight_pnl_row, axis=1)
        .map(color_pnl, subset=["pnl_usdt", "pnl_pct"])
        .map(color_numeric_blue, subset=["avg_entry", "cost_usdt", "value_usdt"])
        .map(color_price_current, subset=["current_price"])
    )

    st.write(styled_positions)
else:
    st.info("No hay posiciones calculadas.")
    
# ========================
# 🧠 DEBUG BOT
# ========================
st.markdown("## 🧠 Estado interno del bot")

with st.expander("Ver debug completo", expanded=False):
    st.write("📡 Symbol:", getattr(state, "symbol", None))
    st.write("💰 Precio:", getattr(state, "price", None))
    st.write("📊 Señal:", getattr(state, "signal", None))
    st.write("📈 Tendencia:", getattr(state, "trend", None))
    st.write("🎯 Decisión:", getattr(state, "decision", None))
    st.write("⚙️ Stage:", getattr(state, "stage", None))
    st.write("📉 RSI:", getattr(state, "rsi", None))
    st.write("🧾 Market mode:", getattr(state, "market_mode", None))
    st.write("🧠 Último market_state:", getattr(state, "market_state", None))