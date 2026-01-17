"""
CAPACITY ANALYZER
=================
Institutional liquidity analysis. 
Forecasts slippage and calculates "Institutional Capacity" via LOB.
"""

import MetaTrader5 as mt5
import pandas as pd
import json

def analyze_capacity(symbol="GOLD", target_volume=10.0):
    if not mt5.initialize():
        return {"error": "MT5 Initialize failed"}
    
    # Check if symbol is available and selected
    selected = mt5.symbol_select(symbol, True)
    if not selected:
        mt5.shutdown()
        return {"error": f"Symbol {symbol} not found or could not be selected."}
    
    # Get Market Depth (Must have Market Depth subscription or broker support)
    items = mt5.market_book_get(symbol)
    
    if items is None:
        mt5.shutdown()
        return {
            "symbol": symbol,
            "status": "No LOB Data (Check Broker Support)",
            "warning": "High-fidelity TCA requires market depth data."
        }
    
    # Process Order Book
    book = pd.DataFrame(list(items), columns=items[0]._asdict().keys())
    
    # Type 1 = Sell (Asks), Type 2 = Buy (Bids)
    asks = book[book['type'] == 1].sort_values(by='price')
    bids = book[book['type'] == 2].sort_values(by='price', ascending=False)
    
    def calculate_slippage(df, volume):
        cumulative_vol = 0
        weighted_price = 0
        for _, row in df.iterrows():
            needed = volume - cumulative_vol
            take = min(needed, row['volume'])
            weighted_price += take * row['price']
            cumulative_vol += take
            if cumulative_vol >= volume:
                break
        
        if cumulative_vol < volume:
            return None, None # Not enough liquidity
        
        avg_price = weighted_price / volume
        slippage = abs(avg_price - df.iloc[0]['price'])
        return avg_price, slippage

    best_ask = asks.iloc[0]['price']
    best_bid = bids.iloc[0]['price']
    mid_price = (best_ask + best_bid) / 2
    
    buy_price, buy_slippage = calculate_slippage(asks, target_volume)
    sell_price, sell_slippage = calculate_slippage(bids, target_volume)
    
    report = {
        "symbol": symbol,
        "target_volume": target_volume,
        "mid_price": mid_price,
        "liquidity": {
            "buy_avg_price": buy_price,
            "buy_slippage_pips": buy_slippage * 100 if buy_slippage else "Insufficient Liquidity",
            "sell_avg_price": sell_price,
            "sell_slippage_pips": sell_slippage * 100 if sell_slippage else "Insufficient Liquidity"
        },
        "verdict": "Healthy" if (buy_slippage or 0) < (mid_price * 0.0001) else "High Impact"
    }
    
    mt5.shutdown()
    return report

if __name__ == "__main__":
    # Test with standard retail volume vs institutional volume
    print("--- RETAIL (1.0 Lot) ---")
    print(json.dumps(analyze_capacity("GOLD", 1.0), indent=2))
    print("\n--- INSTITUTIONAL (50.0 Lots) ---")
    print(json.dumps(analyze_capacity("GOLD", 50.0), indent=2))
