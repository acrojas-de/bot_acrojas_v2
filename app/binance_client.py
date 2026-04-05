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
        from datetime import datetime

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
                    trade_time = trade.get("time")

                    if trade_time:
                        formatted_time = datetime.fromtimestamp(trade_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = ""

                    history.append({
                        "time": formatted_time,
                        "symbol": symbol,
                        "side": "BUY" if trade.get("isBuyer") else "SELL",
                        "price": round(price, 6),
                        "qty": round(qty, 6),
                        "quote_qty": round(quote_qty, 2),
                        "commission": trade.get("commission"),
                        "commission_asset": trade.get("commissionAsset"),
                        "order_id": trade.get("orderId"),
                        "is_maker": trade.get("isMaker"),
                    })

            except Exception:
                pass

        history = sorted(history, key=lambda x: x["time"], reverse=True)
        return history

    except Exception as e:
        print(f"Error trade history: {e}")
        return []


def calculate_spot_positions(client):
    """
    Calcula posición Spot real por activo usando historial de trades.
    Devuelve cantidad neta, coste acumulado, precio medio y precio actual.
    """
    try:
        portfolio = get_spot_portfolio(client)

        positions = []

        for item in portfolio:
            asset = item["asset"]

            if asset in ["USDT", "USDC", "BUSD", "FDUSD", "EUR"]:
                continue

            symbol = f"{asset}USDT"

            try:
                trades = client.get_my_trades(symbol=symbol, limit=200)
            except Exception:
                continue

            net_qty = 0.0
            net_cost = 0.0

            for trade in trades:
                qty = float(trade.get("qty", 0) or 0)
                quote_qty = float(trade.get("quoteQty", 0) or 0)

                if trade.get("isBuyer"):
                    net_qty += qty
                    net_cost += quote_qty
                else:
                    net_qty -= qty

                    if net_qty > 0:
                        avg_cost_before = net_cost / (net_qty + qty) if (net_qty + qty) > 0 else 0
                        net_cost -= qty * avg_cost_before
                    else:
                        net_cost = 0.0

            if net_qty <= 0:
                continue

            avg_entry = net_cost / net_qty if net_qty > 0 else 0.0
            current_price = float(item["price"])
            current_value = net_qty * current_price
            pnl_usdt = current_value - net_cost
            pnl_pct = (pnl_usdt / net_cost * 100) if net_cost > 0 else 0.0

            positions.append({
                "asset": asset,
                "quantity": round(net_qty, 6),
                "avg_entry": round(avg_entry, 4),
                "current_price": round(current_price, 4),
                "cost_usdt": round(net_cost, 2),
                "value_usdt": round(current_value, 2),
                "pnl_usdt": round(pnl_usdt, 2),
                "pnl_pct": round(pnl_pct, 2),
            })

        positions = sorted(positions, key=lambda x: x["value_usdt"], reverse=True)
        return positions

    except Exception as e:
        print(f"Error calculate positions: {e}")
        return []
        
def get_spot_alerts(client):
    try:
        positions = calculate_spot_positions(client)
        alerts = []

        for p in positions:
            if p["pnl_pct"] > 50:
                alerts.append(f"🚀 {p['asset']} +{p['pnl_pct']}% | TAKE PROFIT")

            elif p["pnl_pct"] < -20:
                alerts.append(f"⚠️ {p['asset']} {p['pnl_pct']}% | STOP LOSS")

        return alerts

    except Exception as e:
        print(f"Error alerts: {e}")
        return []