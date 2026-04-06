from .signal_engine import build_signal


def build_market_signal(price: float, klines_map: dict) -> dict:
    signal = build_signal(price, klines_map) or {}

    # 🧪 DEBUG FORZADO (temporal)
    #signal["compression"] = {
    #    "compression_stage": 3,
    #    "compression_label": "DEBUG MODE",
    #    "trend_long": True,
    #   "trend_short": False,
    #   "breakout_up": True,
    #   "breakout_down": False,
    #   "confirm_long": True,
    #   "confirm_short": False,
    }

#signal["setup_type"] = "COMPRESSION_LONG"

    return signal