import time
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from app.binance_client import get_balance, get_spot_portfolio

from app.bootstrap import bootstrap
from app.market.market_cycle import run_market_cycle
from app.execution.trade_service import (
    execute_trade,
    manage_open_trades,
    close_trade_manually,
)

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Bot Acrojas", layout="wide")

st.title("bot_acrojas_v2 🚀")

st.markdown(
    '[Abrir MICRO NITRITO 🚀](http://localhost:3000/micro',
    unsafe_allow_html=True
)

st_autorefresh(interval=15000, key="bot_refresh")

HISTORY_FILE = Path("trade_history.json")

st.markdown("""
<style>
.block-container {
    padding-top: 0.2rem;
    padding-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    text-align:center;
    margin-bottom:6px;
    line-height:1.1;
">
    <div style="font-size:32px; font-weight:800;">
        ₿ Bot Acrojas
    </div>
    <div style="font-size:14px; color:#888;">
        Contexto · permiso · ejecución
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# HELPERS
# =========================================================
def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def save_history(trades: list) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(trades, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass


def calc_trade_pnl(trade: dict, current_price) -> float:
    entry = float(trade.get("entry_price", 0) or 0)
    qty = float(trade.get("quantity", 0) or 0)
    side = trade.get("side", "N/A")
    status = trade.get("status", "N/A")

    if status == "CLOSED" and trade.get("pnl") is not None:
        try:
            return float(trade.get("pnl", 0) or 0)
        except Exception:
            return 0.0

    if current_price is None:
        current_price = entry

    if side == "LONG":
        return (float(current_price) - entry) * qty
    return (entry - float(current_price)) * qty


def render_trade_card(trade: dict, current_price) -> None:
    side = trade.get("side", "N/A")
    status = trade.get("status", "N/A")
    symbol = trade.get("symbol", "N/A")
    entry = float(trade.get("entry_price", 0) or 0)
    qty = float(trade.get("quantity", 0) or 0)
    trade_time = (
        trade.get("opened_at")
        or trade.get("timestamp")
        or trade.get("time")
        or "N/A"
    )

    pnl = calc_trade_pnl(trade, current_price)

    pnl_color = "#00c853" if pnl >= 0 else "#ff1744"
    bg_color = "rgba(0, 200, 83, 0.10)" if pnl >= 0 else "rgba(255, 23, 68, 0.10)"
    side_bg = "#00c853" if side == "LONG" else "#ff1744"
    status_bg = "#00c853" if status == "OPEN" else "#616161"
    signo = "+" if pnl >= 0 else ""

    html = (
        f'<div style="background:{bg_color}; border-left:6px solid {pnl_color}; '
        f'padding:14px 16px; border-radius:14px; margin-bottom:12px; '
        f'box-shadow:0 2px 8px rgba(0,0,0,0.10);">'

        f'<div style="font-size:28px; font-weight:800; color:{pnl_color}; line-height:1.1;">'
        f'{signo}{pnl:.2f} USDT'
        f'</div>'

        f'<div style="margin-top:8px; display:flex; gap:8px; align-items:center; flex-wrap:wrap;">'
        f'<span style="background:{status_bg}; color:#ffffff; padding:3px 8px; '
        f'border-radius:999px; font-size:12px; font-weight:800;">{status}</span>'
        f'<span style="background:{side_bg}; color:#ffffff; padding:3px 8px; '
        f'border-radius:999px; font-size:12px; font-weight:800;">{side}</span>'
        f'<span style="color:#111827; font-size:14px; font-weight:700;">{symbol}</span>'
        f'</div>'

        f'<div style="font-size:13px; color:#111827; margin-top:8px; font-weight:600;">'
        f'Entrada: {entry} · Cantidad: {qty} · {trade_time}'
        f'</div>'

        f'</div>'
    )

    try:
        st.html(html)
    except AttributeError:
        st.markdown(html, unsafe_allow_html=True)


# =========================================================
# STATE
# =========================================================
if "client" not in st.session_state or "state" not in st.session_state:
    client, state = bootstrap()
    st.session_state.client = client
    st.session_state.state = state

client = st.session_state.client
state = st.session_state.state

trade_mode_key = "trade_market_mode"
if trade_mode_key not in st.session_state:
    st.session_state[trade_mode_key] = "SPOT"

market_mode = st.session_state[trade_mode_key]

saved_trades = load_history()
if saved_trades:
    state.open_trades = saved_trades


# =========================================================
# MAIN
# =========================================================
try:
    market_cycle_result = run_market_cycle(client, state)

    if isinstance(market_cycle_result, dict):
        if "signal" in market_cycle_result and market_cycle_result["signal"]:
            state.signal = market_cycle_result["signal"]
        state.market_cycle_result = market_cycle_result

    signal = getattr(state, "signal", {}) or {}
    strength = signal.get("strength", "N/A")

    decision = signal.get("decision_report", {}) or {}
    decision_text = decision.get("decision", "N/A")

    # =========================
    # 🧠 CÁLCULO COMPRESIÓN
    # =========================
    compression = signal.get("compression", {})

    stage = compression.get("compression_stage", 0)
    label = compression.get("compression_label", "IDLE")
    setup_type_signal = signal.get("setup_type", "NONE")

    trend_long = compression.get("trend_long", False)
    trend_short = compression.get("trend_short", False)
    breakout_up = compression.get("breakout_up", False)
    breakout_down = compression.get("breakout_down", False)

    if trend_long:
        bias = "LARGO"
    elif trend_short:
        bias = "CORTO"
    else:
        bias = "NEUTRAL"

    if breakout_up:
        trigger_status = "RUPTURA ALCISTA"
    elif breakout_down:
        trigger_status = "RUPTURA BAJISTA"
    else:
        trigger_status = "PENDIENTE"

    label_map = {
        "IDLE": "Sin compresión",
        "COMPRESSION DETECTED": "Compresión detectada",
        "SQUEEZE ACTIVE": "Embudo activo",
        "READY / WATCHING BREAKOUT": "Listo, esperando ruptura",
        "BREAKOUT TRIGGERED": "Ruptura activada",
        "COMPRESSION LONG": "Long confirmado",
        "COMPRESSION SHORT": "Short confirmado",
        "EXPLOSION LONG": "Explosión long",
        "EXPLOSION SHORT": "Explosión short",
    }
    pretty_label = label_map.get(label, label)
    progress_value = min(stage / 4, 1.0)

    blink = int(time.time()) % 2 == 0

    permit_long = decision_text == "OPERAR LONG"
    permit_short = decision_text == "OPERAR SHORT"
    watch_long = decision_text == "VIGILAR LONG"
    watch_short = decision_text == "VIGILAR SHORT"

    # 🔥 BLOQUEO FINO POR COMPRESIÓN
    allow_early_long = (
        stage >= 3
        and bias == "LARGO"
        and breakout_up
        and compression.get("confirm_long", False)
        and setup_type_signal in ["COMPRESSION_LONG", "EXPLOSION_LONG", "EMA50_FIRST_TOUCH_LONG"]
        and market_mode == "SPOT"
    )

    allow_early_short = (
        stage >= 3
        and bias == "CORTO"
        and breakout_down
        and compression.get("confirm_short", False)
        and setup_type_signal in ["COMPRESSION_SHORT", "EXPLOSION_SHORT", "EMA50_FIRST_TOUCH_SHORT"]
        and market_mode == "FUTURES"
    )

    if stage < 4 and not allow_early_long and not allow_early_short:
        permit_long = False
        permit_short = False

    if permit_long:
        action_arrow = "⬆️" if blink else ""
        action_label = "LISTO PARA LONG"
        action_color = "#00c853"
    elif permit_short:
        action_arrow = "⬇️" if blink else ""
        action_label = "LISTO PARA SHORT"
        action_color = "#ff1744"
    elif watch_long:
        action_arrow = "↗️"
        action_label = "VIGILAR LONG"
        action_color = "#f9a825"
    elif watch_short:
        action_arrow = "↘️"
        action_label = "VIGILAR SHORT"
        action_color = "#f9a825"
    else:
        action_arrow = ""
        action_label = "SIN PERMISO DE ENTRADA"
        action_color = "#9e9e9e"

    if market_mode == "SPOT" and permit_short:
        action_arrow = ""
        action_label = "SHORT BLOQUEADO EN SPOT"
        action_color = "#9e9e9e"

    market_state = decision.get("market_state", "N/A")
    setup_type = decision.get("setup_type", "N/A")
    reasons_yes = decision.get("reasons_yes", [])
    reasons_no = decision.get("reasons_no", [])

    setup = "NO TRADE"

    ema_map = signal.get("ema_map", {})
    rsi_map = signal.get("rsi", {})

    tf = "5m"
    ema21 = ema_map.get(tf, {}).get("ema21")
    ema50 = ema_map.get(tf, {}).get("ema50")
    rsi_5m = rsi_map.get(tf)

    if ema21 is not None and ema50 is not None and rsi_5m is not None:
        if ema21 > ema50 and rsi_5m < 70:
            setup = "POSIBLE LONG"
        elif ema21 < ema50 and rsi_5m > 30:
            setup = "POSIBLE SHORT"

    # =========================================================
    # BLOQUE 1 · HERO CENTRAL
    # =========================================================
    if "BUY" in str(strength):
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #0f9d58, #34a853);
                padding: 10px;
                border-radius: 16px;
                text-align: center;
                color: white;
                font-size: 20px;
                font-weight: 800;
                margin-bottom: 12px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            ">
                BUY FUERTE · {strength}
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif "SELL" in str(strength):
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #c62828, #e53935);
                padding: 10px;
                border-radius: 16px;
                text-align: center;
                color: white;
                font-size: 20px;
                font-weight: 800;
                margin-bottom: 12px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            ">
                SELL FUERTE · {strength}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #f9a825, #fbc02d);
                padding: 10px;
                border-radius: 20px;
                text-align: center;
                color: #222;
                font-size: 20px;
                font-weight: 800;
                margin-bottom: 12px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            ">
                NEUTRAL · {strength}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="text-align:center; margin: 0px 0 2px 0; line-height:1;">
            <div style="font-size:20px; font-weight:800;">{decision_text}</div>
            <div style="font-size:11px; color:#888;">{market_state} · {setup_type} · {state.cycles_in_decision} ciclos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="
            background: {action_color};
            padding: 10px;
            border-radius: 12px;
            text-align: center;
            color: white;
            font-size: 22px;
            font-weight: 800;
            margin: 8px auto 8px auto;
            box-shadow: 0 3px 10px rgba(0,0,0,0.16);
        ">
            {action_arrow} {action_label}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =========================================================
    # BLOQUE · CUENTA BINANCE
    # =========================================================
    st.markdown("### 💰 Cuenta Binance")

    try:
        balances = get_balance(client)
        portfolio = get_spot_portfolio(client)

        # -------- RESUMEN RÁPIDO --------
        total_usdt = 0.0
        usdt_free = 0.0
        btc_qty = 0.0

        if portfolio:
            total_usdt = sum(float(item.get("value_usdt", 0) or 0) for item in portfolio)

            for item in portfolio:
                if item.get("asset") == "USDT":
                    usdt_free = float(item.get("quantity", 0) or 0)
                if item.get("asset") == "BTC":
                    btc_qty = float(item.get("quantity", 0) or 0)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Valor total cartera", f"{total_usdt:.2f} USDT")

        with c2:
            st.metric("USDT disponible", f"{usdt_free:.2f}")

        with c3:
            st.metric("BTC en cartera", f"{btc_qty:.6f}")

        # -------- BALANCES CRUDOS --------
        with st.expander("Ver balances disponibles"):
            if balances:
                for b in balances:
                    st.write(
                        f"{b['asset']}: free={float(b['free']):.8f} | locked={float(b['locked']):.8f}"
                    )
            else:
                st.warning("No se encontraron balances disponibles en la cuenta.")

        # -------- CARTERA VALORADA --------
        st.markdown("#### 📊 Cartera Spot valorada en USDT")

        if portfolio:
            portfolio_df = pd.DataFrame(portfolio)
            st.dataframe(portfolio_df, width="stretch", hide_index=True)
        else:
            st.info("No hay activos valorables en cartera Spot.")

    except Exception as e:
        st.error(f"Error obteniendo balance/cartera de Binance: {e}")

    # =========================================================
    # BLOQUE 2 · CONTEXTO RÁPIDO
    # =========================================================
    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            font-size:20px;
            font-weight:600;
            margin: 2px auto 6px auto;
            gap:12px;
            flex-wrap:wrap;
        ">
            <span>Activo: {state.symbol or 'N/A'}</span>
            <span>Estado: {market_state}</span>
            <span>Precio: {round(state.price, 2) if state.price is not None else 'N/A'}</span>
            <span>Configuración: {setup}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =========================================================
    # BLOQUE 3 · GRÁFICO OPERATIVO
    # =========================================================
    st.markdown("### Acción del precio en 5m")
    st.caption("Velas + EMA21 + EMA50 + zonas + permiso de acción")

    klines = client.get_klines(symbol=state.symbol or "BTCUSDT", interval="5m", limit=100)

    df = pd.DataFrame(
        klines,
        columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbbav", "tbqav", "ignore",
        ],
    )

    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)

    df["ema21"] = df["close"].ewm(span=21).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    manage_open_trades(state, state.price, df)

    auto_key = f"auto_mode_{state.symbol or 'default'}"
    if auto_key not in st.session_state:
        st.session_state[auto_key] = False

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Precio",
        )
    )
    fig.add_trace(go.Scatter(x=df["time"], y=df["ema21"], name="EMA21"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["ema50"], name="EMA50"))

    high_zone = df["high"].tail(20).max()
    low_zone = df["low"].tail(20).min()
    mid_zone = (high_zone + low_zone) / 2
    current_price_chart = df["close"].iloc[-1]

    fig.add_hline(y=high_zone, line_dash="dash", line_width=1)
    fig.add_hline(y=mid_zone, line_dash="dot", line_width=1)
    fig.add_hline(y=low_zone, line_dash="dash", line_width=1)

    x_led = df["time"].iloc[-1]

    near_high = current_price_chart >= high_zone * 0.995
    near_low = current_price_chart <= low_zone * 1.005
    in_middle = not near_high and not near_low

    rsi_5m_chart = signal.get("rsi", {}).get("5m")

    red_active = near_high
    red_confirm = (
        near_high and
        rsi_5m_chart is not None and
        rsi_5m_chart > 65 and
        decision_text != "OPERAR LONG"
    )

    if red_confirm:
        red_led = "🔴" if blink else "⚫"
    else:
        red_led = "🔴" if red_active else "⚫"

    green_active = near_low
    green_confirm = (
        near_low and
        rsi_5m_chart is not None and
        rsi_5m_chart < 35 and
        decision_text != "OPERAR SHORT"
    )

    if green_confirm:
        green_led = "🟢" if blink else "⚫"
    else:
        green_led = "🟢" if green_active else "⚫"

    amber_led = "🟡" if in_middle else "⚫"

    fig.add_annotation(x=x_led, y=high_zone, text=red_led, showarrow=False, xshift=35)
    fig.add_annotation(x=x_led, y=mid_zone, text=amber_led, showarrow=False, xshift=35)
    fig.add_annotation(x=x_led, y=low_zone, text=green_led, showarrow=False, xshift=35)

    fig.add_annotation(
        x=x_led, y=low_zone, text="ZONA LONG",
        showarrow=False, xshift=-70,
        font=dict(size=15, color="green"),
    )
    fig.add_annotation(
        x=x_led, y=high_zone, text="ZONA SHORT",
        showarrow=False, xshift=-70,
        font=dict(size=15, color="red"),
    )

    if permit_long:
        fig.add_annotation(
            x=x_led, y=current_price_chart,
            text="⬆️" if blink else "",
            showarrow=False, xshift=70,
            font=dict(size=28),
        )
    elif permit_short:
        fig.add_annotation(
            x=x_led, y=current_price_chart,
            text="⬇️" if blink else "",
            showarrow=False, xshift=70,
            font=dict(size=28),
        )
    elif watch_long:
        fig.add_annotation(
            x=x_led, y=current_price_chart,
            text="↗️", showarrow=False, xshift=70,
            font=dict(size=24),
        )
    elif watch_short:
        fig.add_annotation(
            x=x_led, y=current_price_chart,
            text="↘️", showarrow=False, xshift=70,
            font=dict(size=24),
        )

    fig.update_layout(
        height=360,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch")

    # =========================================================
    # BLOQUE 4 · CONTROLES DE EJECUCIÓN
    # =========================================================
    exec1, exec2, exec3 = st.columns([1, 1, 1])

    market_mode = st.radio(
        "⚙️ Modo de mercado",
        ["SPOT", "FUTURES"],
        horizontal=True,
        key="trade_market_mode",
    )

    execution_mode = st.radio(
        "🧪 Modo de ejecución",
        ["SIMULATED", "REAL"],
        horizontal=True,
        key="execution_mode",
    )

    st.caption(f"Modo mercado: {market_mode} · Modo ejecución: {execution_mode}")

    if execution_mode == "REAL":
        st.error("⚠️ MODO REAL ACTIVADO — revisa bien antes de lanzar órdenes")

    with exec1:
        auto_mode = st.toggle("AUTO", value=st.session_state[auto_key], key=auto_key)

    with exec2:
        manual_long = st.button("🚀 Ejecutar LONG", width="stretch", disabled=False)

    with exec3:
        short_disabled = (market_mode == "SPOT") or (not permit_short)
        manual_short = st.button("🔻 Ejecutar SHORT", width="stretch", disabled=short_disabled)

    if market_mode == "SPOT":
        st.info("🟢 Modo SPOT activo: solo operaciones LONG (compra real). SHORT estará disponible en FUTURES.")

    open_positions = [t for t in state.open_trades if t.get("status") == "OPEN"]
    has_open_position = len(open_positions) > 0

    changed_history = False

    if manual_long:
        state.trade_mode = "MANUAL"
        result = execute_trade(
            client,
            state,
            side="LONG",
            market_mode=market_mode,
            execution_mode=execution_mode,  # 👈 AÑADIR
            klines_df=df,
        )
        if result["ok"]:
            st.success(result["message"])
            changed_history = True
        else:
            st.warning(result["message"])

    if manual_short:
        state.trade_mode = "MANUAL"
        result = execute_trade(
            client,
            state,
            side="SHORT",
            market_mode=market_mode,
            execution_mode=execution_mode,
            klines_df=df,
        )
        
        if result["ok"]:
            st.success(result["message"])
            changed_history = True
        else:
            st.warning(result["message"])

    if auto_mode and permit_long and stage >= 3 and market_mode == "SPOT":
        state.trade_mode = "AUTO"
        result = execute_trade(
            client,
            state,
            side="LONG",
            market_mode=market_mode,
            execution_mode=execution_mode,
            klines_df=df,
        )
        
        if result["ok"]:
            st.warning(f"AUTO LONG: {result['message']}")
            changed_history = True
        else:
            st.warning(result["message"])

    if auto_mode and permit_short and stage >= 3 and market_mode == "FUTURES":
        state.trade_mode = "AUTO"
        result = execute_trade(
            client,
            state,
            side="SHORT",
            market_mode=market_mode,
            execution_mode=execution_mode,
            klines_df=df,
        )
        
        if result["ok"]:
            st.warning(f"AUTO SHORT: {result['message']}")
            changed_history = True
        else:
            st.warning(result["message"])

    if changed_history:
        save_history(state.open_trades)

    st.divider()

    # =========================================================
    # BLOQUE 4.1 · PANEL DE COMPRESIÓN
    # =========================================================
    st.markdown("### 🧠 Compresión")

    st.progress(progress_value, text=pretty_label)

    if stage == 3:
        st.warning(f"🧠 Compresión avanzada ({bias}) — posible ruptura inminente")

    if stage == 3 and bias == "SHORT":
        st.caption("📉 Probabilidad mayor de ruptura bajista")
    elif stage == 3 and bias == "LONG":
        st.caption("📈 Probabilidad mayor de ruptura alcista")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estado", pretty_label)
    col2.metric("Sesgo", bias)
    col3.metric("Disparo", trigger_status)
    col4.metric("Setup compresión", setup_type_signal)

    if setup_type_signal == "COMPRESSION_LONG":
        st.success("🔥 Setup de compresión LONG confirmado")
    elif setup_type_signal == "COMPRESSION_SHORT":
        st.error("🔥 Setup de compresión SHORT confirmado")
    elif stage in [2, 3] and setup_type_signal == "NONE":
        st.warning("🟡 Compresión activa: vigilando ruptura")
    else:
        st.info("⚪ Sin compresión relevante")

    if stage < 4 and not allow_early_long and not allow_early_short:
        st.info("⏳ Esperando breakout confirmado (sin entradas aún)")
    elif allow_early_long:
        st.success("🚀 Entrada anticipada LONG permitida por ruptura confirmada")
    elif allow_early_short:
        st.warning("🚀 Entrada anticipada SHORT permitida por ruptura confirmada")

    with st.expander("Ver detalle técnico de compresión"):
        st.write(f"Compression: {compression.get('compression')}")
        st.write(f"EMA squeezed: {compression.get('ema_squeezed')}")
        st.write(f"Breakout up: {compression.get('breakout_up')}")
        st.write(f"Breakout down: {compression.get('breakout_down')}")
        st.write(f"Trend long: {compression.get('trend_long')}")
        st.write(f"Trend short: {compression.get('trend_short')}")
        st.write(f"Strong bullish: {compression.get('strong_bullish')}")
        st.write(f"Strong bearish: {compression.get('strong_bearish')}")
        st.write(f"Confirm long: {compression.get('confirm_long')}")
        st.write(f"Confirm short: {compression.get('confirm_short')}")
        st.write(f"EMA50 touch long: {compression.get('ema50_touch_long')}")
        st.write(f"EMA50 touch short: {compression.get('ema50_touch_short')}")

    st.divider()

    # =========================================================
    # BLOQUE 4.5 · ESTADO RÁPIDO DEL BOT
    # =========================================================
    st.markdown("### 🧠 Estado rápido del bot")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Modo", market_mode)

    with c2:
        st.metric("Decisión", decision_text)

    with c3:
        st.metric("Stage", stage)

    with c4:
        st.metric("Sesgo", bias)

    c5, c6 = st.columns(2)

    with c5:
        if permit_long:
            st.success("✅ LONG permitido")
        else:
            st.error("⛔ LONG bloqueado")

    with c6:
        if market_mode == "SPOT":
            st.info("ℹ️ SHORT no disponible en SPOT")
        elif permit_short:
            st.success("✅ SHORT permitido")
        else:
            st.error("⛔ SHORT bloqueado")

    if decision_text == "OPERAR LONG":
        st.success("🟢 Contexto favorable para LONG")
    elif decision_text == "OPERAR SHORT":
        st.error("🔴 Contexto favorable para SHORT")
    elif "VIGILAR" in str(decision_text):
        st.warning(f"🟡 {decision_text}")
    else:
        st.info("⚪ Sin entrada válida por ahora")

    # =========================================================
    # BLOQUE 5 · POSICIÓN ACTUAL
    # =========================================================
    st.markdown("### Posición actual")

    open_positions = [t for t in state.open_trades if t.get("status") == "OPEN"]

    if open_positions:
        for trade in open_positions:
            entry = float(trade.get("entry_price", 0) or 0)
            qty = float(trade.get("quantity", 0) or 0)
            side = trade.get("side", "N/A")
            current_price = float(state.price) if state.price is not None else entry

            if side == "LONG":
                pnl = (current_price - entry) * qty
            else:
                pnl = (entry - current_price) * qty

            signo = "+" if pnl >= 0 else ""
            pnl_color = "#00c853" if pnl >= 0 else "#ff1744"
            side_color = "#00c853" if side == "LONG" else "#ff1744"

            st.markdown(
                f"<div style='font-size:32px; font-weight:800; color:{pnl_color}; margin:0 0 10px 0;'>{signo}{pnl:.2f} USDT</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div style="
                    background:#111827;
                    padding:10px 14px;
                    border-radius:12px;
                    color:white;
                    font-size:14px;
                    font-weight:600;
                    margin-bottom:8px;
                    display:flex;
                    justify-content:space-between;
                    gap:12px;
                    flex-wrap:wrap;
                    border-left:6px solid {side_color};
                ">
                    <span><b>{side}</b></span>
                    <span>Símbolo: {trade.get('symbol', 'N/A')}</span>
                    <span>Cantidad: {qty}</span>
                    <span>Entrada: {entry}</span>
                    <span>SL: {trade.get('stop_loss', 'N/A')}</span>
                    <span>TP: {trade.get('take_profit', 'N/A')}</span>
                    <span>Preparación: {trade.get('setup_type', 'N/A')}</span>
                    <span>Modo: {trade.get('signal_origin', 'N/A')}</span>
                    <span>Estado: {trade.get('status', 'N/A')}</span>
                    <span>ID: {trade.get('id', 'N/A')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            button_key = f"close_{trade.get('id', '')}"
            if st.button(
                f"🛑 Cerrar {trade.get('side', 'TRADE')} {trade.get('symbol', '')}",
                key=button_key,
                width="stretch"
            ):
                result = close_trade_manually(trade, state.price)
                if result["ok"]:
                    st.success(result["message"])
                    save_history(state.open_trades)
                    st.rerun()
                else:
                    st.warning(result["message"])

            st.markdown("---")
    else:
        st.info("No hay posición abierta.")

    st.divider()

    # =========================================================
    # BLOQUE 6 · HISTORIAL DE OPERACIONES
    # =========================================================
    st.markdown("### Historial de operaciones")

    if state.open_trades:
        for trade in reversed(state.open_trades):
            render_trade_card(trade, state.price)
    else:
        st.info("Todavía no hay historial de operaciones.")

    st.divider()

    # =========================================================
    # BLOQUE 7 · ANÁLISIS SECUNDARIO
    # =========================================================
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### A favor")
        if reasons_yes:
            for r in reasons_yes:
                st.write(f"- {r}")
        else:
            st.write("Nada destacable")

    with col_b:
        st.markdown("### En contra")
        if reasons_no:
            for r in reasons_no:
                st.write(f"- {r}")
        else:
            st.write("Sin objeciones")

    st.divider()

    st.markdown("### Lectura rápida del mercado")
    st.caption("Resumen simplificado para ayudarte a decidir con claridad")
    quick1, quick2, quick3, quick4 = st.columns(4)

    with quick1:
        st.write(f"Rebote: {signal.get('rebound', 'N/A')}")

    with quick2:
        trap = signal.get("trap", {})
        trap_flag = trap.get("trap", False) if isinstance(trap, dict) else False
        st.write(f"Trampa: {'Sí' if trap_flag else 'No'}")

    with quick3:
        structure = signal.get("structure", {})
        tendencia = structure.get("Tendencia") if isinstance(structure, dict) else structure
        st.write(f"Estructura: {tendencia or 'N/A'}")

    with quick4:
        st.write(f"Objetivo: {signal.get('target', 'N/A')}")

    st.divider()

    st.markdown("### Confirmación por timeframes")
    st.caption("Visión multi-temporal para validar si la señal tiene apoyo")

    radar = signal.get("radar", {})
    rsi = signal.get("rsi", {})
    ema_map = signal.get("ema_map", {})

    if radar:
        timeframe_order = {"1m": 1, "5m": 2, "15m": 3, "1h": 4, "4h": 5, "1D": 6}

        rows = []
        for tf_name, sig in radar.items():
            rows.append(
                {
                    "Timeframe": tf_name,
                    "Señal": sig,
                    "RSI": rsi.get(tf_name, "N/A"),
                    "EMA21": ema_map.get(tf_name, {}).get("ema21", "N/A"),
                    "EMA50": ema_map.get(tf_name, {}).get("ema50", "N/A"),
                }
            )

        radar_df = pd.DataFrame(rows)
        radar_df["order"] = radar_df["Timeframe"].map(timeframe_order)
        radar_df = radar_df.sort_values("order").drop(columns=["order"])

        st.dataframe(radar_df, width="stretch", hide_index=True)
    else:
        st.info("Sin radar todavía.")

    st.divider()

    with st.expander("Datos técnicos completos (debug)"):
        st.json(signal)

except Exception as e:
    st.error(f"Error consultando Binance: {e}")