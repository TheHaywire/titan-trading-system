
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import settings
from titan_system.math_core.regression import LinearRegressionChannel
from titan_system.math_core.statistics import StatisticalMetrics
from titan_system.db.database import Database

def scan_market():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
        
    db = Database(settings.db_path)
    symbols = db.get_active_universe(limit=50) # Get top 50
    
    print(f"\n🌍 QUANTITATIVE MARKET SCAN ({len(symbols)} Assets)")
    print(f"{'SYMBOL':<10} {'PRICE':<10} {'Z-SCORE':<8} {'HALF-LIFE':<10} {'STATUS':<15}")
    print("-" * 60)
    
    opportunities = []

    reg = LinearRegressionChannel(period=100)

    for symbol in symbols:
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
            if rates is None or len(rates) < 150:
                continue
                
            df = pd.DataFrame(rates)
            closes = df['close'].values
            
            # 1. Calc Channel & Z-Score
            stats = reg.calculate(closes)
            
            # 2. Calc Half-Life
            expected = stats['slope'] * np.arange(len(closes)) + stats['intercept']
            residuals = closes[-100:] - expected[-100:]
            half_life = StatisticalMetrics.calculate_half_life(residuals)
            
            z = stats['z_score']
            
            status = "NEUTRAL"
            if z > 2.0: status = "🟥 OVERBOUGHT"
            elif z < -2.0: status = "🟩 OVERSOLD"
            elif z > 1.5: status = "🔸 HIGH"
            elif z < -1.5: status = "🔹 LOW"
            
            # Filter for display: Only interesting ones or specific request?
            # Let's show everything sorted by absolute Z score later?
            # For now print as we go if interesting
            
            item = {
                "symbol": symbol,
                "price": closes[-1],
                "z": z,
                "hl": half_life,
                "status": status
            }
            opportunities.append(item)
            
        except Exception as e:
            continue
            
    # Sort by "Extreme-ness" (Abs Z-Score)
    opportunities.sort(key=lambda x: abs(x['z']), reverse=True)
    
    for op in opportunities[:20]: # Show top 20 extremes
        print(f"{op['symbol']:<10} {op['price']:<10.5f} {op['z']:<8.2f} {op['hl']:<10.1f} {op['status']:<15}")

    mt5.shutdown()

if __name__ == "__main__":
    scan_market()
