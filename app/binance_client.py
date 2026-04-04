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