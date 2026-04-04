class BotState:
    def __init__(self):
        self.symbol = None
        self.price = None

        # señales
        self.signal = None
        self.entry = None
        self.score = None

        # mercado
        self.klines_map = {}

        # trades
        self.open_trades = []
        self.balance = 0.0

        # control
        self.trade_mode = None
        self.allow_entries = True

        # telegram
        self.last_update_id = None
        self.commands = []

        # 🧠 MEMORIA DEL BOT
        self.prev_decision = None
        self.cycles_in_decision = 0
        self.prev_market_state = None
        self.cycles_in_market_state = 0

    def update_market(self, symbol, price, signal, klines_map):
        self.symbol = symbol
        self.price = price
        self.signal = signal
        self.klines_map = klines_map

    def update_commands(self, commands, last_update_id):
        self.commands = commands
        self.last_update_id = last_update_id

    def update_memory(self, decision_data: dict):
        current_decision = decision_data.get("decision")
        current_market_state = decision_data.get("market_state")

        # decisión
        if current_decision == self.prev_decision:
            self.cycles_in_decision += 1
        else:
            self.prev_decision = current_decision
            self.cycles_in_decision = 1

        # estado de mercado
        if current_market_state == self.prev_market_state:
            self.cycles_in_market_state += 1
        else:
            self.prev_market_state = current_market_state
            self.cycles_in_market_state = 1

    def add_trade(self, trade: dict):
        self.open_trades.append(trade)

    def close_trade(self, trade_id: str):
        for trade in self.open_trades:
            if trade.get("id") == trade_id and trade.get("status") == "OPEN":
                trade["status"] = "CLOSED"
                return trade
        return None
        
    def has_open_trade(self, symbol: str, side: str) -> bool:
        for trade in self.open_trades:
            if (
                trade.get("symbol") == symbol
                and trade.get("side") == side
                and trade.get("status") == "OPEN"
            ):
                return True
        return False