"""
Clean Alpha Registry
Removes illiquid symbols from alpha_registry.json
"""
import MetaTrader5 as mt5
import json

mt5.initialize()

# Load current alpha registry
with open('config/alpha_registry.json', 'r') as f:
    registry = json.load(f)

print(f"Original alphas: {len(registry['alphas'])}")

# Filter only liquid symbols (spread < 100)
liquid_alphas = []
illiquid_removed = []

for alpha in registry['alphas']:
    symbol = alpha['symbol']
    info = mt5.symbol_info(symbol)
    
    if info:
        spread = info.spread
        if spread < 100:
            alpha['spread'] = spread  # Add spread info
            liquid_alphas.append(alpha)
        else:
            illiquid_removed.append(f"{symbol} (spread={spread})")
    else:
        illiquid_removed.append(f"{symbol} (NOT FOUND)")

print(f"\nLiquid alphas kept: {len(liquid_alphas)}")
print(f"Illiquid removed: {len(illiquid_removed)}")

if illiquid_removed:
    print("\nRemoved symbols:")
    for s in illiquid_removed[:20]:
        print(f"  ❌ {s}")
    if len(illiquid_removed) > 20:
        print(f"  ... and {len(illiquid_removed) - 20} more")

# Save cleaned registry
registry['alphas'] = liquid_alphas
registry['last_updated'] = '2026-01-16'
registry['note'] = 'Cleaned: removed illiquid symbols (spread >= 100)'

with open('config/alpha_registry.json', 'w') as f:
    json.dump(registry, f, indent=4)

print(f"\n✅ Saved cleaned alpha_registry.json with {len(liquid_alphas)} liquid alphas")

# Show remaining alphas
print("\n=== TOP 10 REMAINING ALPHAS ===")
for alpha in liquid_alphas[:10]:
    print(f"  {alpha['symbol']} | {alpha['strategy']} | {alpha['tf']} | Sharpe: {alpha['metrics']['sharpe']} | Spread: {alpha.get('spread', 'N/A')}")

mt5.shutdown()
