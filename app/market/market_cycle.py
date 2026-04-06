from app.config import DEFAULT_SYMBOL
from app.market.data_feed import get_symbol_price, build_klines_map
from app.market.signal_service import build_market_signal
from app.market.decision_engine import build_operational_decision


# ==========================
# DEBUG de compresión
# ==========================
def log_signal_summary(signal: dict):
    signal = signal or {}
    compression = signal.get("compression") or {}

    print(
        "\n[COMPRESSION DEBUG] "
        f"setup_type={signal.get('setup_type')} | "
        f"compression={compression.get('compression')} | "
        f"stage={compression.get('compression_stage')} | "
        f"label={compression.get('compression_label')} | "
        f"ema_squeezed={compression.get('ema_squeezed')} | "
        f"breakout_up={compression.get('breakout_up')} | "
        f"breakout_down={compression.get('breakout_down')} | "
        f"trend_long={compression.get('trend_long')} | "
        f"trend_short={compression.get('trend_short')} | "
        f"confirm_long={compression.get('confirm_long')} | "
        f"confirm_short={compression.get('confirm_short')}"
    )


def run_market_cycle(client, state):
    symbol = state.symbol or DEFAULT_SYMBOL

    price = get_symbol_price(client, symbol)
    klines_map = build_klines_map(client, symbol, limit=120)

    # =========================
    # 1. CONSTRUIR SEÑAL
    # =========================
    signal = build_market_signal(price, klines_map) or {}

    # DEBUG señal
    log_signal_summary(signal)

    # =========================
    # 2. DECISIÓN OPERATIVA
    # =========================
    decision_data = build_operational_decision(signal) or {}

    # =========================
    # 3. MEMORIA DEL BOT
    # =========================
    state.update_memory(decision_data)

    # =========================
    # 4. FILTRO DE DISCIPLINA
    #    - mantiene disciplina normal
    #    - NO bloquea rupturas explosivas
    # =========================
    compression = signal.get("compression") or {}
    breakout_up = compression.get("breakout_up", False)
    breakout_down = compression.get("breakout_down", False)

    if not breakout_up and not breakout_down:
        if state.cycles_in_decision < 2 or state.cycles_in_market_state < 2:
            decision_data["decision"] = "ESPERAR"
            decision_data.setdefault("reasons_no", []).append(
                f"Esperando estabilidad (decisión={state.cycles_in_decision}, mercado={state.cycles_in_market_state})"
            )

    # DEBUG decisión final
    print("[DECISION DEBUG]", decision_data)
    print(
        "[MEMORY DEBUG]",
        f"cycles_in_decision={state.cycles_in_decision} | "
        f"cycles_in_market_state={state.cycles_in_market_state}"
    )

    # =========================
    # 5. GUARDAR DECISIÓN EN SIGNAL
    # =========================
    signal["decision_report"] = decision_data

    # =========================
    # 6. ESTADO DEL MERCADO
    # =========================
    market_state = {
        "symbol": symbol,
        "price": price,
        "klines_map": klines_map,
        "signal": signal,
        "decision": decision_data,
    }

    # =========================
    # 7. ACTUALIZAR STATE GLOBAL
    # =========================
    state.update_market(
        symbol=symbol,
        price=price,
        signal=signal,
        klines_map=klines_map,
    )

    return market_state