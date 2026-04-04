
def get_balance():
    try:
        account = client.get_account()
        balances = account.get("balances", [])

        for asset in balances:
            if asset.get("asset") == "USDT":
                return asset

        return None
    except Exception as e:
        print(f"Error Binance balance: {e}")
        return None