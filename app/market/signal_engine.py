import pandas as pd

from ..indicators.ema_rsi import ema, rsi
from ..indicators.trap_detector import trap_detector
from ..indicators.market_structure import market_structure, market_state
from ..indicators.liquidity import liquidity_levels, liquidity_target, probable_target
from ..indicators.compression import (
    is_compression,
    is_ema_squeezed,
    breakout_long,
    breakout_short,
    strong_bullish_candle,
    strong_bearish_candle,
    breakout_confirmed,
)


def build_market_signal(price, klines_map):
    return build_signal(price, klines_map)


def interpret(radar):
    if radar["5m"] == "SELL" and radar["15m"] == "BUY" and radar["1h"] == "BUY":
        return "🔧 CORRECCIÓN DENTRO DE TENDENCIA"

    if radar["5m"] == "BUY" and radar["15m"] == "BUY" and radar["1h"] == "BUY" and radar["4h"] == "BUY":
        return "🔥 ALINEACIÓN ALCISTA"

    if radar["5m"] == "SELL" and radar["15m"] == "SELL" and radar["1h"] == "SELL":
        return "⚠️ POSIBLE GIRO BAJISTA"

    return "⚖️ MERCADO INDECISO"


def signal_strength(radar):
    buy_count = list(radar.values()).count("BUY")
    sell_count = list(radar.values()).count("SELL")

    if buy_count >= 4:
        return "💪 BUY FUERTE"

    if sell_count >= 4:
        return "💥 SELL FUERTE"

    if buy_count > sell_count:
        return "📈 BUY MODERADO"

    if sell_count > buy_count:
        return "📉 SELL MODERADO"

    return "⚖️ NEUTRAL"

def rebound_probability(radar, rsi_map):
    if (
        radar["5m"] == "SELL"
        and radar["15m"] == "BUY"
        and radar["1h"] == "BUY"
        and rsi_map["5m"] < 30
    ):
        return "ALTO"

    if radar["5m"] == "SELL" and rsi_map["5m"] < 35:
        return "MEDIO"

    return "BAJO"
    

def klines_to_df(klines):
    df = pd.DataFrame(
        klines,
        columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbbav", "tbqav", "ignore",
        ],
    )

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)

    df["ema21"] = df["close"].ewm(span=21).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    return df


def detect_compression_setup(df):
    if df is None or len(df) < 10:
        return {
            "compression_long": False,
            "compression_short": False,
            "explosion_long": False,
            "explosion_short": False,
            "flag_active": False,
            "flag_long": False,
            "flag_short": False,
            "flag_side": "NONE",
            "setup_type": "NONE",
            "compression": False,
            "ema_squeezed": False,
            "breakout_up": False,
            "breakout_down": False,
            "strong_bullish": False,
            "strong_bearish": False,
            "trend_long": False,
            "trend_short": False,
            "confirm_long": False,
            "confirm_short": False,
            "compression_stage": 0,
            "compression_label": "IDLE",
            "ema50_touch_long": False,
            "ema50_touch_short": False,
        }

    # =========================
    # 🔍 DETECCIÓN BASE
    # =========================
    compression = is_compression(df)
    ema_squeezed = is_ema_squeezed(df)
    long_break = breakout_long(df)
    short_break = breakout_short(df)
    bullish = strong_bullish_candle(df)
    bearish = strong_bearish_candle(df)

    last = df.iloc[-1]

    trend_long = bool(last["ema21"] >= last["ema50"])
    trend_short = bool(last["ema21"] <= last["ema50"])

    # =====================================
    # 🔥 FIRST TOUCH EMA50
    # =====================================
    ema50_touch_long = False
    ema50_touch_short = False

    if len(df) >= 3:
        prev = df.iloc[-2]
        curr = df.iloc[-1]

        if prev["close"] < prev["ema50"] and curr["close"] >= curr["ema50"]:
            ema50_touch_long = True

        if prev["close"] > prev["ema50"] and curr["close"] <= curr["ema50"]:
            ema50_touch_short = True

    # =========================
    # 🚩 DETECTOR DE BANDERA
    # =========================
    flag_long = compression and ema_squeezed and trend_long and not long_break and not short_break
    flag_short = compression and ema_squeezed and trend_short and not long_break and not short_break
    flag_active = flag_long or flag_short

    flag_side = "NONE"
    if flag_long:
        flag_side = "LONG"
    elif flag_short:
        flag_side = "SHORT"

    # =========================
    # 🚀 EXPLOSION ENTRY
    # =========================
    explosion_long = compression and ema_squeezed and long_break and trend_long
    explosion_short = compression and ema_squeezed and short_break and trend_short

    # =========================
    # 🛡️ CONFIRMACIÓN ANTI-FAKE
    # =========================
    confirm_long = breakout_confirmed(df, "LONG")
    confirm_short = breakout_confirmed(df, "SHORT")

    # =========================
    # 🎯 SETUP FINAL CONFIRMADO
    # =========================
    compression_long = (
        compression and ema_squeezed and long_break and trend_long and confirm_long
    )
    compression_short = (
        compression and ema_squeezed and short_break and trend_short and confirm_short
    )

    # Jerarquía:
    # NONE -> EMA50 FIRST TOUCH -> EXPLOSION -> COMPRESSION CONFIRMADA
    setup_type = "NONE"

    if ema50_touch_long:
        setup_type = "EMA50_FIRST_TOUCH_LONG"
    elif ema50_touch_short:
        setup_type = "EMA50_FIRST_TOUCH_SHORT"

    if explosion_long:
        setup_type = "EXPLOSION_LONG"
    elif explosion_short:
        setup_type = "EXPLOSION_SHORT"

    if compression_long:
        setup_type = "COMPRESSION_LONG"
    elif compression_short:
        setup_type = "COMPRESSION_SHORT"

    # =========================
    # 🌡️ TERMÓMETRO DE ESTADO
    # =========================
    compression_stage = 0
    compression_label = "IDLE"

    if flag_active:
        compression_stage = 1
        compression_label = f"FLAG {flag_side}"
    elif compression:
        compression_stage = 1
        compression_label = "COMPRESSION DETECTED"

    if compression and ema_squeezed:
        compression_stage = 2
        compression_label = "SQUEEZE ACTIVE"

    if flag_active:
        compression_stage = 3
        compression_label = f"FLAG READY {flag_side}"
    elif compression and ema_squeezed and (trend_long or trend_short):
        compression_stage = 3
        compression_label = "READY / WATCHING BREAKOUT"

    if long_break or short_break:
        compression_stage = 4
        compression_label = "BREAKOUT TRIGGERED"

    if explosion_long:
        compression_label = "EXPLOSION LONG"
    elif explosion_short:
        compression_label = "EXPLOSION SHORT"

    if compression_long:
        compression_label = "COMPRESSION LONG"
    elif compression_short:
        compression_label = "COMPRESSION SHORT"

    return {
        "compression_long": compression_long,
        "compression_short": compression_short,
        "explosion_long": explosion_long,
        "explosion_short": explosion_short,
        "flag_active": flag_active,
        "flag_long": flag_long,
        "flag_short": flag_short,
        "flag_side": flag_side,
        "setup_type": setup_type,
        "compression": compression,
        "ema_squeezed": ema_squeezed,
        "breakout_up": long_break,
        "breakout_down": short_break,
        "strong_bullish": bullish,
        "strong_bearish": bearish,
        "trend_long": trend_long,
        "trend_short": trend_short,
        "confirm_long": confirm_long,
        "confirm_short": confirm_short,
        "compression_stage": compression_stage,
        "compression_label": compression_label,
        "ema50_touch_long": ema50_touch_long,
        "ema50_touch_short": ema50_touch_short,
    }


def build_signal(price, klines_map):
    radar = {}
    rsi_map = {}
    ema_map = {}

    for tf, klines in klines_map.items():
        closes = [float(k[4]) for k in klines]

        ema21 = ema(closes, 21)[-1]
        ema50 = ema(closes, 50)[-1]
        rsi_val = rsi(closes)

        signal = "BUY" if ema21 > ema50 else "SELL"

        radar[tf] = signal
        rsi_map[tf] = round(rsi_val, 1)
        ema_map[tf] = {
            "ema21": round(ema21, 2),
            "ema50": round(ema50, 2),
            "price": round(closes[-1], 2),
        }

    interpretation = interpret(radar)
    strength = signal_strength(radar)
    rebound = rebound_probability(radar, rsi_map)

    trap = trap_detector(klines_map["5m"])

    structure = market_structure(klines_map["1h"])
    state_market = market_state(rsi_map)

    magnet_up, magnet_down = liquidity_levels(klines_map["1h"])
    target = probable_target(price, radar)
    liq_target = liquidity_target(price, magnet_up, magnet_down)

    df_5m = klines_to_df(klines_map["5m"])
    compression_setup = detect_compression_setup(df_5m)

    print("DEBUG build_signal compression:", compression_setup)

    print("\n=== COMPRESSION DEBUG ===")
    print("setup_type:", compression_setup.get("setup_type"))
    print("flag_active:", compression_setup.get("flag_active"))
    print("flag_side:", compression_setup.get("flag_side"))
    print("compression:", compression_setup.get("compression"))
    print("ema_squeezed:", compression_setup.get("ema_squeezed"))
    print("breakout_up:", compression_setup.get("breakout_up"))
    print("breakout_down:", compression_setup.get("breakout_down"))
    print("explosion_long:", compression_setup.get("explosion_long"))
    print("explosion_short:", compression_setup.get("explosion_short"))
    print("confirm_long:", compression_setup.get("confirm_long"))
    print("confirm_short:", compression_setup.get("confirm_short"))
    print("trend_long:", compression_setup.get("trend_long"))
    print("trend_short:", compression_setup.get("trend_short"))

    return {
        "radar": radar,
        "rsi": rsi_map,
        "ema_map": ema_map,
        "interpretation": interpretation,
        "strength": strength,
        "rebound": rebound,
        "trap": trap,
        "structure": structure,
        "state_market": state_market,
        "magnet_up": magnet_up,
        "magnet_down": magnet_down,
        "target": target,
        "liq_target": liq_target,
        
        "compression": compression_setup,   # ✅ MISMO NIVEL
        "setup_type": compression_setup.get("setup_type", "NONE"),
        }         
         