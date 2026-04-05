import time
import traceback

from app.bootstrap import bootstrap
from app.market.market_cycle import run_market_cycle
from app.execution.execution_cycle import run_execution_cycle
from app.telegram.telegram_service import process_telegram, send_telegram_message
from app.binance_client import get_spot_alerts
from app.config import TELEGRAM_TOKEN, CHAT_ID


def main():
    client, state = bootstrap()

    # Mensaje de prueba al arrancar
    send_telegram_message(
        message="✅ TEST TELEGRAM DESDE APP.MAIN",
        token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID
    )

    while True:
        try:
            print("🧠 loop activo", state.symbol, state.price)

            process_telegram(state)
            market_state = run_market_cycle(client, state)
            print("📈 market_state:", market_state)
            print("📦 state.signal:", state.signal)

            run_execution_cycle(state, market_state)

            # 🚨 Alertas Spot a Telegram
            alerts = get_spot_alerts(client)

            for alert in alerts:
                send_telegram_message(
                    message=alert,
                    token=TELEGRAM_TOKEN,
                    chat_id=CHAT_ID
                )

            time.sleep(100)

        except Exception as e:
            print("❌ Error en main loop:")
            traceback.print_exc()
            time.sleep(2)


if __name__ == "__main__":
    main()