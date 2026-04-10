def run_execution_cycle(state, market_state):

    # 🔥 TEST: cerrar primer trade abierto automáticamente
    if state.open_trades:
        trade = state.open_trades[0]

        closed = state.close_trade(
            trade_id=trade.get("id"),
            exit_price=state.price,
            reason="TEST"
        )

        if closed:
            print("✅ TRADE CERRADO:", closed)
            print("📊 HISTORIAL:", state.trade_history)
            print("📈 STATS:", state.get_stats())