import os
import requests
from flask import Flask, send_from_directory, jsonify, request
from app.binance_client import get_spot_portfolio
from app.bootstrap import bootstrap

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

@app.route("/api/balance")
def api_balance():
    try:
        client, _ = bootstrap()
        portfolio = get_spot_portfolio(client)

        total = sum(float(p.get("value_usdt", 0) or 0) for p in portfolio)

        usdt_free = 0.0
        btc_qty = 0.0

        for item in portfolio:
            if item.get("asset") == "USDT":
                usdt_free = float(item.get("quantity", 0) or 0)
            elif item.get("asset") == "BTC":
                btc_qty = float(item.get("quantity", 0) or 0)

        return jsonify({
            "total_usdt": round(total, 2),
            "usdt_free": round(usdt_free, 2),
            "btc_qty": round(btc_qty, 6),
            "assets": portfolio
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)