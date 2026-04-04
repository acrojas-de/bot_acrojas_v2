# =========================================================
# COMPRESSION & BREAKOUT LOGIC
# =========================================================

def is_compression(df, lookback: int = 6, max_range_pct: float = 0.0035) -> bool:
    """
    Detecta compresión de precio (rango estrecho).
    """
    if df is None or len(df) < lookback + 2:
        return False

    recent = df.tail(lookback)
    high = float(recent["high"].max())
    low = float(recent["low"].min())

    if low <= 0:
        return False

    range_pct = (high - low) / low
    return range_pct <= max_range_pct


def is_ema_squeezed(df, threshold_pct: float = 0.0015) -> bool:
    """
    Detecta si EMA21 y EMA50 están muy cerca (embudo real).
    """
    if df is None or len(df) < 3:
        return False

    last = df.iloc[-1]
    ema21 = float(last["ema21"])
    ema50 = float(last["ema50"])

    if ema50 == 0:
        return False

    distance_pct = abs(ema21 - ema50) / ema50
    return distance_pct <= threshold_pct


# =========================================================
# BREAKOUTS
# =========================================================

def breakout_long(df, lookback: int = 6) -> bool:
    """
    Ruptura alcista del rango de compresión.
    """
    if df is None or len(df) < lookback + 1:
        return False

    last = df.iloc[-1]
    prev_range = df.iloc[-(lookback + 1):-1]
    range_high = float(prev_range["high"].max())

    return float(last["close"]) > range_high


def breakout_short(df, lookback: int = 6) -> bool:
    """
    Ruptura bajista del rango de compresión.
    """
    if df is None or len(df) < lookback + 1:
        return False

    last = df.iloc[-1]
    prev_range = df.iloc[-(lookback + 1):-1]
    range_low = float(prev_range["low"].min())

    return float(last["close"]) < range_low


# =========================================================
# CANDLE CONFIRMATION
# =========================================================

def strong_bullish_candle(df, min_body_ratio: float = 0.55) -> bool:
    """
    Vela alcista con cuerpo fuerte.
    """
    if df is None or len(df) < 1:
        return False

    last = df.iloc[-1]
    open_ = float(last["open"])
    close = float(last["close"])
    high = float(last["high"])
    low = float(last["low"])

    total_range = high - low
    if total_range <= 0:
        return False

    body = abs(close - open_)
    return close > open_ and (body / total_range) >= min_body_ratio


def strong_bearish_candle(df, min_body_ratio: float = 0.55) -> bool:
    """
    Vela bajista con cuerpo fuerte.
    """
    if df is None or len(df) < 1:
        return False

    last = df.iloc[-1]
    open_ = float(last["open"])
    close = float(last["close"])
    high = float(last["high"])
    low = float(last["low"])

    total_range = high - low
    if total_range <= 0:
        return False

    body = abs(close - open_)
    return close < open_ and (body / total_range) >= min_body_ratio
    
def breakout_confirmed(df, direction: str, lookback: int = 6) -> bool:
    """
    Confirma que el breakout no es fake:
    - vela rompe
    - siguiente vela mantiene dirección
    """

    if df is None or len(df) < lookback + 2:
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev_range = df.iloc[-(lookback + 2):-2]

    range_high = float(prev_range["high"].max())
    range_low = float(prev_range["low"].min())

    if direction == "LONG":
        return (
            float(prev["close"]) > range_high and
            float(last["close"]) > float(prev["close"])
        )

    elif direction == "SHORT":
        return (
            float(prev["close"]) < range_low and
            float(last["close"]) < float(prev["close"])
        )

    return False