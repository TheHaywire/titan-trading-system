"""
BLACK SWAN TESTER
=================
Historical shock simulator.
Calculates "If it happened today" drawdown for current portfolio.
"""

import MetaTrader5 as mt5
import json

HISTORICAL_SHOCKS = {
    "2015_SNB_Crash": {"CHF": 0.30, "EUR": -0.15},
    "2020_Covid_Gap": {"GOLD": -0.05, "US30": -0.10, "BTC": -0.25},
    "2016_Brexit": {"GBP": -0.10, "EUR": -0.05},
    "2024_Yen_Carry_Unwind": {"JPY": 0.12, "NIKKEI": -0.12}
}

def simulate_shocks():
    if not mt5.initialize():
        return {"error": "MT5 Initialize failed"}
    
    positions = mt5.positions_get()
    if not positions:
        mt5.shutdown()
        return {"status": "No active positions to stress-test."}
    
    account = mt5.account_info()
    balance = account.balance
    
    results = {}
    
    for shock_name, shocks in HISTORICAL_SHOCKS.items():
        potential_loss = 0
        hit_symbols = []
        
        for p in positions:
            symbol = p.symbol.upper()
            # Determine if shock applies to this symbol
            shock_val = 0
            for key, val in shocks.items():
                if key in symbol:
                    shock_val = val
                    break
            
            if shock_val != 0:
                # Calculate pnl impact: (Price * Shock * Direction * Lots * ContractSize)
                # Simplified: profit + (abs_profit * shock) if direction matches
                # Institutional way: Use Delta/Gamma. Simplified for MT5:
                direction = 1 if p.type == 0 else -1
                # estimated_impact = current_value * shock * direction
                # For MT5, price_current * volume * contract_size is not always direct, so we use profit as proxy for distance
                lot_value = p.volume * p.price_open * mt5.symbol_info(p.symbol).trade_contract_size
                impact = lot_value * shock_val * direction
                potential_loss += impact
                hit_symbols.append(p.symbol)

        results[shock_name] = {
            "dollar_impact": round(potential_loss, 2),
            "percent_of_balance": round((potential_loss / balance) * 100, 2),
            "symbols_affected": list(set(hit_symbols))
        }

    mt5.shutdown()
    return {
        "balance": balance,
        "simulations": results,
        "summary": "Stress test complete. Review the % impact for survival analysis."
    }

if __name__ == "__main__":
    print(json.dumps(simulate_shocks(), indent=2))
