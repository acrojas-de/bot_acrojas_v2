import requests


def process_telegram(state):
    return


def send_telegram_message(message: str, token: str, chat_id: str):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
        }

        requests.post(url, data=payload, timeout=10)

    except Exception as e:
        print(f"Error Telegram: {e}")