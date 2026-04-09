from datetime import datetime
from app.binance_client import place_market_order
import uuid


def calculate_smart_stop(side: str, klines_df, buffer_pct: float = 0.0015) -> float:
    """
    Stop basado en estructura simple:
    LONG  -> por debajo del último swing low
    SHORT -> por encima del último swing high
    """
    if klines_df is None or len(klines_df) < 10:
        raise ValueError("No hay suficientes velas para calcular el stop inteligente")

    if side == "LONG":
        swing_low = float(klines_df["low"].rolling(10).min().iloc[-2])
        stop_loss = swing_low * (1 - buffer_pct)
    elif side == "SHORT":
        swing_high = float(klines_df["high"].rolling(10).max().iloc[-2])
        stop_loss = swing_high * (1 + buffer_pct)
    else:
        raise ValueError("side debe ser LONG o SHORT")

    return round(stop_loss, 2)


def calculate_take_profit(
    entry_price: float,
    stop_loss: float,
    side: str,
    klines_df,
    rr: float = 2.0,
) -> float:
    """
    Take profit híbrido:
    mezcla RR fijo con estructura cercana.
    """
    if rr <= 0:
        raise ValueError("rr debe ser mayor que 0")

    risk = abs(entry_price - stop_loss)

    if risk == 0:
        raise ValueError("El riesgo calculado es 0; no se puede calcular TP")

    if klines_df is None or len(klines_df) < 20:
        raise ValueError("No hay suficientes velas para calcular el take profit")

    if side == "LONG":
        tp_rr = entry_price + (risk * rr)
        resistance = float(klines_df["high"].rolling(20).max().iloc[-2])
        take_profit = min(tp_rr, resistance)
    elif side == "SHORT":
        tp_rr = entry_price - (risk * rr)
        support = float(klines_df["low"].rolling(20).min().iloc[-2])
        take_profit = max(tp_rr, support)
    else:
        raise ValueError("side debe ser LONG o SHORT")

    return round(take_profit, 2)


def build_trade_record(
    symbol: str,
    side: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    quantity: float,
    mode: str = "SIMULATED",
) -> dict:
    """
    Construye el registro interno del trade.
    """
    risk_per_unit = abs(entry_price - stop_loss)

    return {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "entry_price": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "risk_per_unit": round(risk_per_unit, 2),
        "rr": round(abs(take_profit - entry_price) / abs(entry_price - stop_loss), 2),
        "status": "OPEN",
        "setup_type": "N/A",
        "signal_origin": "MANUAL",
        "mode": mode,
    }


def execute_trade(
    client,
    state,
    side: str,
    market_mode: str = "SPOT",
    execution_mode: str = "SIMULATED",
    klines_df=None,
    quantity: float = 0.0001,
    rr: float = 2.0,
    buffer_pct: float = 0.0015,
) -> dict:
    """
    Prepara un trade simulado, calcula entrada/SL/TP y lo guarda en memoria.
    """
    if state is None:
        raise ValueError("state no puede ser None")

    if not state.symbol:
        raise ValueError("No hay símbolo activo en state")

    if state.price is None:
        raise ValueError("No hay precio activo en state")

    if quantity <= 0:
        raise ValueError("quantity debe ser mayor que 0")

    if market_mode == "SPOT" and side == "SHORT":
        return {
            "ok": False,
            "message": "SHORT no está disponible en modo SPOT.",
            "trade": None,
        }

    if market_mode == "FUTURES":
        # De momento lo tratamos igual que SPOT (simulado)
        pass

    symbol = state.symbol
    entry_price = float(state.price)

    if (
        getattr(state, "trade_mode", None) == "AUTO"
        and hasattr(state, "has_open_trade")
        and state.has_open_trade(symbol, side)
    ):
        return {
            "ok": False,
            "message": f"Ya existe una posición OPEN en {symbol} para {side}",
            "trade": None,
        }

    stop_loss = calculate_smart_stop(
        side=side,
        klines_df=klines_df,
        buffer_pct=buffer_pct,
    )

    take_profit = calculate_take_profit(
        entry_price=entry_price,
        stop_loss=stop_loss,
        side=side,
        klines_df=klines_df,
        rr=rr,
    )

    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    rr_real = reward / risk if risk > 0 else 0

    if getattr(state, "trade_mode", None) == "AUTO":
        if rr_real < 1.2:
            return {
                "ok": False,
                "message": f"Trade AUTO rechazado por RR insuficiente ({rr_real:.2f})",
                "trade": None,
            }
    else:
        if rr_real < 1.0:
            return {
                "ok": False,
                "message": f"Trade MANUAL rechazado por RR insuficiente ({rr_real:.2f})",
                "trade": None,
            }

    trade = build_trade_record(
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        quantity=quantity,
        mode=execution_mode,
    )
    
    # ========================================================
    # 🚀 EJECUCIÓN REAL EN BINANCE
    # ========================================================
    if execution_mode == "REAL":
        side_binance = "BUY" if side == "LONG" else "SELL"

        order = place_market_order(
            client=client,
            symbol=symbol,
            side=side_binance,
            quantity=quantity,
        )

        if not order:
            return {
                "ok": False,
                "message": "Error ejecutando orden real en Binance",
                "trade": None,
            }

        trade["binance_order"] = order
        trade["status"] = "FILLED"

    trade["setup_type"] = (
        state.signal.get("decision_report", {}).get("setup_type", "N/A")
        if getattr(state, "signal", None)
        else "N/A"
    )

    trade["signal_origin"] = "AUTO" if getattr(state, "trade_mode", None) == "AUTO" else "MANUAL"
    trade["market_mode"] = market_mode

    if hasattr(state, "add_trade") and callable(state.add_trade):
        state.add_trade(trade)
    elif hasattr(state, "open_trades"):
        state.open_trades.append(trade)

    return {
        "ok": True,
        "message": (
            f"{side} preparado en {symbol} | "
            f"modo={market_mode} | "
            f"qty={quantity} | "
            f"entrada={entry_price:.2f} | "
            f"SL={stop_loss:.2f} | "
            f"TP={take_profit:.2f}"
        ),
        "trade": trade,
    }


def manage_open_trades(state, current_price, klines_df):
    if not hasattr(state, "open_trades"):
        return

    for trade in state.open_trades:
        if trade["status"] != "OPEN":
            continue

        entry = trade["entry_price"]
        sl = trade["stop_loss"]
        tp = trade["take_profit"]
        side = trade["side"]

        risk = abs(entry - sl)

        if risk == 0:
            continue

        if side == "LONG":
            profit = current_price - entry
        else:
            profit = entry - current_price

        if profit >= risk:
            if side == "LONG" and trade["stop_loss"] < entry:
                trade["stop_loss"] = entry
            elif side == "SHORT" and trade["stop_loss"] > entry:
                trade["stop_loss"] = entry
                
        if side == "LONG":
            if profit >= risk * 2:
                trade["stop_loss"] = round(max(trade["stop_loss"], entry + (risk * 1)), 2)

            if profit >= risk * 3:
                trade["stop_loss"] = round(max(trade["stop_loss"], entry + (risk * 2)), 2)

        elif side == "SHORT":
            if profit >= risk * 2:
                trade["stop_loss"] = round(min(trade["stop_loss"], entry - (risk * 1)), 2)

            if profit >= risk * 3:
                trade["stop_loss"] = round(min(trade["stop_loss"], entry - (risk * 2)), 2)

        if side == "LONG" and current_price <= trade["stop_loss"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (trade["stop_loss"] - entry) * trade["quantity"]

        elif side == "SHORT" and current_price >= trade["stop_loss"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (entry - trade["stop_loss"]) * trade["quantity"]

        elif side == "LONG" and current_price >= tp:
            trade["status"] = "CLOSED"
            trade["pnl"] = (tp - entry) * trade["quantity"]

        elif side == "SHORT" and current_price <= tp:
            trade["status"] = "CLOSED"
            trade["pnl"] = (entry - tp) * trade["quantity"]


def close_trade_manually(trade: dict, current_price: float) -> dict:
    """
    Cierra manualmente un trade OPEN al precio actual.
    """
    if trade.get("status") != "OPEN":
        return {
            "ok": False,
            "message": "El trade ya está cerrado",
            "trade": trade,
        }

    entry = float(trade.get("entry_price", 0) or 0)
    qty = float(trade.get("quantity", 0) or 0)
    side = trade.get("side", "N/A")

    if current_price is None:
        current_price = entry

    current_price = float(current_price)

    if side == "LONG":
        pnl = (current_price - entry) * qty
    elif side == "SHORT":
        pnl = (entry - current_price) * qty
    else:
        return {
            "ok": False,
            "message": "side inválido en el trade",
            "trade": trade,
        }

    trade["status"] = "CLOSED"
    trade["pnl"] = round(pnl, 2)
    trade["close_price"] = round(current_price, 2)
    trade["close_reason"] = "MANUAL"
    trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "ok": True,
        "message": (
            f"Trade cerrado manualmente | "
            f"{side} {trade.get('symbol', 'N/A')} | "
            f"salida={current_price:.2f} | "
            f"PnL={pnl:.2f}"
        ),
        "trade": trade,
    }