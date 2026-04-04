from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DEFAULT_SYMBOL = "BTCUSDT"
SYMBOL = "BTCUSDT"

ALL_TIMEFRAMES = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1D": Client.KLINE_INTERVAL_1DAY,
    "1W": Client.KLINE_INTERVAL_1WEEK
}

ACTIVE_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1D"]