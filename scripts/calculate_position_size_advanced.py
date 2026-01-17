"""
ADVANCED POSITION SIZE CALCULATOR
Uses Kelly Criterion, Volatility Adjustment, and Risk Limits
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

def calculate_advanced_position_size(symbol, entry, stop_loss, account_risk_pct=0.01):
    """
    Advanced position sizing with multiple factors
    """
    if not mt5.initialize():
        return None
    
    # Get account info
    account = mt5.account_info()
    balance = account.balance
    
    # Get symbol info
    info = mt5.symbol_info(symbol)
    if not info:
        print(f"Symbol {symbol} not found")
        mt5.shutdown()
        return None
    
    # 1. BASE CALCULATION (Standard risk)
    risk_amount = balance * account_risk_pct
    sl_distance = abs(entry - stop_loss)
    
    # Convert to points
    point = info.point
    sl_points = sl_distance / point
    
    # Pip value calculation
    if "JPY" in symbol:
        pip_value = 0.01 * info.trade_contract_size / 100
    else:
        pip_value = 0.0001 * info.trade_contract_size
    
    base_lots = risk_amount / (sl_points * pip_value * point / pip_value)
    
    # 2. VOLATILITY ADJUSTMENT
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 30)
    if rates is not None:
        df = pd.DataFrame(rates)
        
        # Calculate ATR
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        
        current_atr = tr.rolling(14).mean().iloc[-1]
        avg_atr = tr.rolling(14).mean().mean()
        
        volatility_ratio = current_atr / avg_atr
        
        # Adjust size based on volatility
        if volatility_ratio > 1.5:
            volatility_multiplier = 0.5  # Cut size in half during high volatility
            print(f"⚠️ HIGH VOLATILITY: Current ATR is {volatility_ratio:.1f}x normal")
        elif volatility_ratio > 1.2:
            volatility_multiplier = 0.75
            print(f"⚠️ Elevated volatility: {volatility_ratio:.1f}x normal")
        else:
            volatility_multiplier = 1.0
        
        adjusted_lots = base_lots * volatility_multiplier
    else:
        adjusted_lots = base_lots
        volatility_multiplier = 1.0
    
    # 3. KELLY CRITERION (Optional - for reference only)
    # NOTE: Requires win rate and avg R data from historical trades
    # We'll use conservative estimates
    estimated_win_rate = 0.55
    estimated_avg_r = 2.0
    
    kelly_fraction = ((estimated_avg_r * estimated_win_rate) - (1 - estimated_win_rate)) / estimated_avg_r
    half_kelly = kelly_fraction / 2  # Use half-Kelly for safety
    
    kelly_lots = (balance * half_kelly) / (sl_points * pip_value * point / pip_value)
    
    # 4. APPLY CONSTRAINTS
    final_lots = min(adjusted_lots, kelly_lots)  # Take more conservative
    final_lots = round(final_lots, 2)
    
    # Apply symbol limits
    final_lots = max(info.volume_min, min(final_lots, info.volume_max))
    
    # Hard cap at 5 lots (safety)
    final_lots = min(final_lots, 5.0)
    
    # Calculate actual risk
    actual_risk_usd = final_lots * sl_points * pip_value * point / pip_value
    actual_risk_pct = (actual_risk_usd / balance) * 100
    
    # Display results
    print("="*60)
    print("📊 ADVANCED POSITION SIZE CALCULATOR")
    print("="*60)
    print(f"Symbol: {symbol}")
    print(f"Entry: {entry}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Distance: {sl_points:.0f} points")
    print()
    print(f"Account Balance: ${balance:,.2f}")
    print(f"Target Risk: {account_risk_pct*100}%")
    print()
    print("CALCULATIONS:")
    print(f"  Base Lots: {base_lots:.2f}")
    print(f"  Volatility Adj: {volatility_multiplier:.2f}x → {adjusted_lots:.2f} lots")
    print(f"  Kelly Criterion: {kelly_lots:.2f} lots (half-Kelly)")
    print()
    print(f"✅ FINAL POSITION SIZE: {final_lots} lots")
    print(f"💰 Actual Risk: ${actual_risk_usd:,.2f} ({actual_risk_pct:.2f}%)")
    print("="*60)
    
    mt5.shutdown()
    return final_lots

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python calculate_position_size_advanced.py SYMBOL ENTRY STOP_LOSS")
        print("Example: python calculate_position_size_advanced.py GOLD 4600 4550")
    else:
        symbol = sys.argv[1]
        entry = float(sys.argv[2])
        stop_loss = float(sys.argv[3])
        calculate_advanced_position_size(symbol, entry, stop_loss)
