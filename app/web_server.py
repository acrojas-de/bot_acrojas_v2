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
    symbol = request.args.get("symbol")

    if not symbol or symbol in ["undefined", "null", "None", ""]:
        symbol = "BTCUSDT"

    symbol = symbol.upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        if "price" not in data:
            return jsonify({
                "symbol": symbol,
                "price": None,
                "error": "Precio no disponible"
            }), 200

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "symbol": symbol,
            "price": None,
            "error": str(e)
        }), 200


@app.route("/klines")
def klines():
    symbol = request.args.get("symbol")
    if not symbol or symbol in ["undefined", "null", "None", ""]:
        symbol = "BTCUSDT"
    symbol = symbol.upper()

    interval = request.args.get("interval", "1m")
    limit = int(request.args.get("limit", 5))

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return jsonify(r.json()), 200
    except Exception as e:
        return jsonify([]), 200


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
        }), 200

    except Exception as e:
        return jsonify({
            "total_usdt": 0.0,
            "usdt_free": 0.0,
            "btc_qty": 0.0,
            "assets": [],
            "error": str(e)
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False, use_reloader=False)