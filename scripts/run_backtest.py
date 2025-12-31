
import sys
import os
import argparse
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Path Setup
sys.path.append(os.getcwd())
from titan_system.core.execution import MT5Execution
from config.settings import settings

# Import Strategies
from titan_system.strategies.institutional_gold import InstitutionalGoldStrategy
from titan_system.strategies.liquidity_hunter import LiquidityHunterStrategy
from titan_system.strategies.mean_reversion import MeanReversionStrategy

STRATEGIES = {
    "InstitutionalGold": InstitutionalGoldStrategy,
    "LiquidityHunter": LiquidityHunterStrategy,
    "MeanReversion": MeanReversionStrategy
}

def load_data(symbol, timeframe, days=30):
    """Loads data from MT5."""
    if not mt5.initialize():
        print("❌ MT5 Init failed")
        return None
        
    utc_from = datetime.now() - timedelta(days=days)
    rates = mt5.copy_rates_from(symbol, timeframe, datetime.now(), days * 24 * 4) # Approx bars
    
    if rates is None: return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    return df

def run_backtest(strategy_name, symbol, timeframe_str, days=30):
    print(f"🧪 Running Backtest: {strategy_name} on {symbol} ({days} days)...")
    
    # 1. Setup Strategy
    strat_class = STRATEGIES.get(strategy_name)
    if not strat_class:
        print(f"❌ Unknown Strategy: {strategy_name}")
        return
        
    strategy = strat_class(config={})
    
    # 2. Get Data
    tf_map = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
    df = load_data(symbol, tf_map.get(timeframe_str, mt5.TIMEFRAME_H1), days)
    
    if df is None or df.empty:
        print("❌ No Data Found")
        return

    print(f"📊 Data Loaded: {len(df)} candles")
    
    # 3. Simulate Walk-Forward Loop
    initial_balance = 10000.0
    balance = initial_balance
    equity_curve = [balance]
    trades = []
    
    # Simple loop simulation (Not vectorized for realistic logic testing)
    # Start from index 100 to allow indicators to warm up
    for i in range(100, len(df)):
        window = df.iloc[i-100:i+1].copy() # Pass window to simulate live
        # Fix: Reset index for strategy internal logic if needed
        
        signal = strategy.analyze(symbol, window)
        
        if signal and signal.get('signal') in ['BUY', 'SELL']:
            # Assume Execution check (Limit Orders not simulated effectively here, assuming Market)
            entry_price = window.iloc[-1]['close']
            sl = signal.get('stop_loss')
            tp = signal.get('take_profit')
            
            # Simple Trade Outcome Simulation (Look forward)
            # Find next candle hitting SL or TP
            future = df.iloc[i+1:i+100] # Look ahead 100 bars
            outcome = "TIMEOUT"
            pnl = 0
            
            for j, future_candle in future.iterrows():
                if signal['signal'] == 'BUY':
                    if future_candle['low'] <= sl:
                        outcome = "SL"
                        pnl = -100 # Fixed $100 Risk
                        break
                    elif future_candle['high'] >= tp:
                        outcome = "TP"
                         # Reward calc:
                        dist_sl = abs(entry_price - sl)
                        dist_tp = abs(tp - entry_price)
                        rr = dist_tp / dist_sl
                        pnl = 100 * rr
                        break
                else: # SELL
                    if future_candle['high'] >= sl:
                        outcome = "SL"
                        pnl = -100
                        break
                    elif future_candle['low'] <= tp:
                        outcome = "TP"
                        dist_sl = abs(sl - entry_price)
                        dist_tp = abs(entry_price - tp)
                        rr = dist_tp / dist_sl
                        pnl = 100 * rr
                        break
            
            trade = {
                "entry_time": window.iloc[-1]['time'],
                "type": signal['signal'],
                "price": entry_price,
                "outcome": outcome,
                "pnl": pnl
            }
            trades.append(trade)
            balance += pnl
    
    # 4. Results
    print("\n📈 Results:")
    print(f"Final Balance: ${balance:.2f} ({(balance-initial_balance)/initial_balance*100:.2f}%)")
    print(f"Total Trades: {len(trades)}")
    
    if trades:
        wins = len([t for t in trades if t['pnl'] > 0])
        win_rate = (wins / len(trades)) * 100
        print(f"Win Rate: {win_rate:.2f}%")
        
    return trades

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, required=True, help="Strategy Name")
    parser.add_argument("--symbol", type=str, default="XAUUSD")
    parser.add_argument("--tf", type=str, default="H1")
    parser.add_argument("--days", type=int, default=30)
    
    args = parser.parse_args()
    run_backtest(args.strategy, args.symbol, args.tf, args.days)
