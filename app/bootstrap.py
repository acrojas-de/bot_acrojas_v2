from binance.client import Client
from app.state import BotState
from app import config

def bootstrap():
    print("🚀 Iniciando bot_acrojas_v2...")

    client = Client(config.API_KEY, config.API_SECRET)
    state = BotState()

    return client, state