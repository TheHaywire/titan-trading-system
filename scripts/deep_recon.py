import MetaTrader5 as mt5
import pandas as pd
import json
import os
from datetime import datetime

# Setup
if not mt5.initialize():
    print(f"FAILED to initialize MT5: {mt5.last_error()}")
    exit()

def serialize_symbol(info):
    """Convert MT5 SymbolInfo object to dictionary"""
    return {
        "symbol": info.name,
        "path": info.path,
        "currency_base": info.currency_base,
        "currency_profit": info.currency_profit,
        "digits": info.digits,
        "spread": info.spread,
        "calc_mode": info.trade_calc_mode, # Forex, Futures, CFD, etc.
        "trade_mode": info.trade_mode,
        "start_time": info.start_time,
        "expiration_time": info.expiration_time,
        "min_lot": info.volume_min,
        "max_lot": info.volume_max,
        "step_lot": info.volume_step,
        "pips_stops_level": info.trade_stops_level, 
        "contract_size": info.trade_contract_size,
        "margin_initial": info.margin_initial,
        "margin_maintenance": info.margin_maintenance,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "swap_mode": info.swap_mode,
        "point": info.point,
        "tick_value": info.trade_tick_value,
        "tick_size": info.trade_tick_size
    }

print("--- [AGENT 1: INFRASTRUCTURE RECON] ---")
term_info = mt5.terminal_info()
print(f"Terminal: {term_info.name} | Path: {term_info.path}")
print(f"Broker/Company: {term_info.company}")
print(f"Connected: {term_info.connected}")
print(f"Ping: {term_info.ping_last / 1000} ms")

print("\n--- [AGENT 2: ACCOUNTANT & RISK] ---")
acc_info = mt5.account_info()
print(f"Login: {acc_info.login}")
print(f"Server: {acc_info.server}")
print(f"Currency: {acc_info.currency}")
print(f"Leverage: 1:{acc_info.leverage}")
print(f"Balance: {acc_info.balance}")
print(f"Equity: {acc_info.equity}")
print(f"Margin Level: {acc_info.margin_level}%")
print(f"Trade Allowed: {acc_info.trade_allowed}")
print(f"ExpertHandle Allowed: {acc_info.trade_expert}")
print(f"Limit Orders: {acc_info.limit_orders}")

print("\n--- [AGENT 3: MARKET CARTOGRAPHER] ---")
print("Scanning Market Watch...")
all_symbols = mt5.symbols_get()
print(f"Total Symbols on Server: {len(all_symbols)}")

# Categorize
categories = {}
full_specs = []

count = 0 
for s in all_symbols:
    # Organize by 'Path' (e.g., Forex\Major, CFD\Indices)
    path_parts = s.path.split("\\")
    root = path_parts[0]
    
    if root not in categories:
        categories[root] = 0
    categories[root] += 1
    
    # Deep extraction for CSV
    full_specs.append(serialize_symbol(s))
    
    count += 1

print("\nAsset Breakdown:")
for cat, cnt in categories.items():
    print(f"  - {cat}: {cnt} instruments")

# Save detailed specs
df = pd.DataFrame(full_specs)
os.makedirs("docs/recon", exist_ok=True)
df.to_csv("docs/recon/BROKER_MASTER_UNIVERSE.csv", index=False)
print(f"\n[SUCCESS] Full specification of {len(df)} assets saved to docs/recon/BROKER_MASTER_UNIVERSE.csv")

# Quick Analysis of 'Fat Tail' Candidates (Agent 4)
print("\n--- [AGENT 4: QUANT SCREENER] ---")
# Filter for Gold
gold = next((x for x in full_specs if "Gold" in x['path'] or "XAU" in x['symbol']), None)
if gold:
    print(f"GOLD FOUND: {gold['symbol']}")
    print(f"  > Contract Size: {gold['contract_size']}")
    print(f"  > Min Lot: {gold['min_lot']}")
    print(f"  > Tick Value ($): {gold['tick_value']}") 
else:
    print("WARNING: Gold symbol not easily identified.")

mt5.shutdown()
