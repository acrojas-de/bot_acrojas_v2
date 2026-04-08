import os
import requests
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__)

# 📁 Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "web"))

# =====================================================
# 🏠 HOME
# =====================================================
@app.route("/")
def home():
    return "Bot Acrojas activo 🚀"

# =====================================================
# 🌐 PANEL MICRO NITRITO
# =====================================================
@app.route("/micro")
def micro():
    return send_from_directory(WEB_DIR, "micro_nitrito.html")

# =====================================================
# 💰 PRECIO REAL BINANCE
# =====================================================
@app.route("/price")
def price():
    symbol = "BTCUSDT"
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    try:
        data = requests.get(url, timeout=5).json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 📊 VELAS (KLINES)
# =====================================================
@app.route("/klines")
def klines():
    symbol = "BTCUSDT"
    interval = "1m"
    limit = 5

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    try:
        data = requests.get(url, timeout=5).json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 🚀 RUN SERVER
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)