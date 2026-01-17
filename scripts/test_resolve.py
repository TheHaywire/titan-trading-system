import MetaTrader5 as mt5

def test_resolve():
    if not mt5.initialize():
        print("Init failed")
        return
        
    roots = ["US500", "US100", "GOLD", "OIL", "BTCUSD"]
    for r in roots:
        # Implementation from weekly_plan_generator.py
        result = None
        if mt5.symbol_select(r, True):
            result = r
        else:
            cash_sym = f"{r}Cash"
            if mt5.symbol_select(cash_sym, True):
                result = cash_sym
        
        print(f"Root: {r} -> Resolved: {result}")
        
    mt5.shutdown()

if __name__ == "__main__":
    test_resolve()
