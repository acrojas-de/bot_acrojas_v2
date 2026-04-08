import os
import requests
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__)

# 📁 Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "web"))

@app.route("/")
def home():
    return "Bot Acrojas activo 🚀"

@app.route("/micro")
def micro():
    return send_from_directory(WEB_DIR, "micro_nitrito.html")

@app.route("/price")
def price():
    symbol = request.args.get("symbol", "BTCUSDT").upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/klines")
def klines():
    symbol = request.args.get("symbol", "BTCUSDT").upper()
    interval = request.args.get("interval", "1m")
    limit = int(request.args.get("limit", 5))

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)