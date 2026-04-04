from app.config import ALL_TIMEFRAMES, ACTIVE_TIMEFRAMES


def get_symbol_price(client, symbol: str) -> float:
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def get_klines(client, symbol: str, interval: str, limit: int = 120):
    return client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )


def build_klines_map(client, symbol: str, limit: int = 120) -> dict:
    klines_map = {}

    for tf in ACTIVE_TIMEFRAMES:
        interval = ALL_TIMEFRAMES[tf]
        klines_map[tf] = get_klines(client, symbol, interval, limit=limit)

    return klines_map