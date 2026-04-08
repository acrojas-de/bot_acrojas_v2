import os
from flask import Flask, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "..", "web")

@app.route("/")
def home():
    return "Bot Acrojas activo 🚀"

@app.route("/micro")
def micro():
    return send_from_directory(WEB_DIR, "micro_nitrito.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)