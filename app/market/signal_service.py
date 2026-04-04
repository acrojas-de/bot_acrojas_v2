from .signal_engine import build_signal


def build_market_signal(price: float, klines_map: dict) -> dict:
    return build_signal(price, klines_map)