def get_balance(client):
    try:
        account = client.get_account()
        balances = account.get("balances", [])

        result = []

        for asset in balances:
            free = float(asset.get("free", 0) or 0)
            locked = float(asset.get("locked", 0) or 0)

            if free > 0 or locked > 0:
                result.append({
                    "asset": asset.get("asset"),
                    "free": free,
                    "locked": locked
                })

        return result

    except Exception as e:
        print(f"Error Binance balance: {e}")
        return []
        
# ================================
# 👉 💼 MI CARTERA
# ================================
        
def get_spot_portfolio(client):
    """
    Cartera Spot con valoración en USDT
    """
    try:
        balances = get_balance(client)
        portfolio = []

        for asset_data in balances:
            symbol = asset_data["asset"]
            total = asset_data["free"] + asset_data["locked"]

            price = 0.0
            value = 0.0

            if symbol in ["USDT", "USDC", "BUSD", "FDUSD"]:
                price = 1.0
                value = total

            elif symbol == "EUR":
                try:
                    ticker = client.get_symbol_ticker(symbol="EURUSDT")
                    price = float(ticker["price"])
                    value = total * price
                except Exception:
                    pass

            else:
                pair = f"{symbol}USDT"
                try:
                    ticker = client.get_symbol_ticker(symbol=pair)
                    price = float(ticker["price"])
                    value = total * price
                except Exception:
                    pass

            rounded_value = round(value, 2)

            if rounded_value > 0:
                portfolio.append({
                    "asset": symbol,
                    "quantity": round(total, 6),
                    "price": round(price, 4),
                    "value_usdt": rounded_value,
                })

        portfolio = sorted(portfolio, key=lambda x: x["value_usdt"], reverse=True)
        return portfolio

    except Exception as e:
        print(f"Error portfolio: {e}")
        return []


def get_spot_trade_history(client, symbols=None, limit=50):
    """
    Devuelve historial Spot reciente de Binance.
    Si symbols=None, intenta con los activos de la cartera.
    """
    try:
        history = []

        if symbols is None:
            portfolio = get_spot_portfolio(client)
            symbols = [
                f"{item['asset']}USDT"
                for item in portfolio
                if item["asset"] not in ["USDT", "USDC", "BUSD", "FDUSD", "EUR"]
            ]

        for symbol in symbols:
            try:
                trades = client.get_my_trades(symbol=symbol, limit=limit)

                for trade in trades:
                    qty = float(trade.get("qty", 0) or 0)
                    price = float(trade.get("price", 0) or 0)
                    quote_qty = float(trade.get("quoteQty", 0) or 0)

                    history.append({
                        "symbol": symbol,
                        "order_id": trade.get("orderId"),
                        "price": round(price, 6),
                        "qty": round(qty, 6),
                        "quote_qty": round(quote_qty, 2),
                        "commission": trade.get("commission"),
                        "commission_asset": trade.get("commissionAsset"),
                        "is_buyer": trade.get("isBuyer"),
                        "is_maker": trade.get("isMaker"),
                        "time": trade.get("time"),
                    })

            except Exception:
                pass

        history = sorted(history, key=lambda x: x["time"], reverse=True)
        return history

    except Exception as e:
        print(f"Error trade history: {e}")
        return []
