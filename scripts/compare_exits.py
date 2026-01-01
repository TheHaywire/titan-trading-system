
import sys
import os
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.strategies.book_strategies import BookTechnicalStrategy

def simulate_exits(symbol, strategy, bars=3000):
    """
    Runs a backtest comparing 3 exit methods:
    1. Fixed Target (2R)
    2. Chandelier Exit (Trail High/Low +/- 3ATR)
    3. SMA Trail (Trail 50 SMA)
    """
    # Fetch Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, bars)
    if rates is None or len(rates) < 500:
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate Indicators
    df = strategy.calculate_indicators(df)
    
    # Generate Signals (Optimized with Trend Filter)
    # We re-use logic from mega_backtest here for consistency or verify using strategy class
    # To be precise, let's use the explicit checks locally to ensure we have the 'Use Trend Filter' logic active
    
    df['prev_SMA_50'] = df['SMA_50'].shift(1)
    df['prev_SMA_200'] = df['SMA_200'].shift(1)
    df['prev_RSI'] = df['RSI_14'].shift(1)
    df['prev_close'] = df['close'].shift(1)
    df['prev_BB_Upper'] = df['BB_Upper'].shift(1)
    df['prev_BB_Lower'] = df['BB_Lower'].shift(1)
    
    # Signals
    sig_golden = (df['prev_SMA_50'] <= df['prev_SMA_200']) & (df['SMA_50'] > df['SMA_200'])
    sig_death = (df['prev_SMA_50'] >= df['prev_SMA_200']) & (df['SMA_50'] < df['SMA_200'])
    
    # Trend Filter
    bull_trend = df['close'] > df['SMA_200']
    bear_trend = df['close'] < df['SMA_200']
    
    sig_rsi_buy = (df['prev_RSI'] < 30) & (df['RSI_14'] >= 30) & bull_trend
    sig_rsi_sell = (df['prev_RSI'] > 70) & (df['RSI_14'] <= 70) & bear_trend
    
    sig_bb_buy = (df['prev_close'] <= df['prev_BB_Upper']) & (df['close'] > df['BB_Upper']) & bull_trend
    sig_bb_sell = (df['prev_close'] >= df['prev_BB_Lower']) & (df['close'] < df['BB_Lower']) & bear_trend
    
    signal_mask = sig_golden | sig_death | sig_rsi_buy | sig_rsi_sell | sig_bb_buy | sig_bb_sell
    signal_indices = df.index[signal_mask].tolist()
    
    results = {
        'Fixed': {'wins':0, 'losses':0, 'pips':0.0, 'max_r': 0.0},
        'Chandelier': {'wins':0, 'losses':0, 'pips':0.0, 'max_r': 0.0},
        'SMA_Trail': {'wins':0, 'losses':0, 'pips':0.0, 'max_r': 0.0}
    }
    
    # Simulation Loop
    for idx in signal_indices:
        if idx < 205 or idx > len(df) - 200: continue
        
        row = df.iloc[idx]
        direction = 0
        if sig_golden[idx] or sig_rsi_buy[idx] or sig_bb_buy[idx]: direction = 1
        elif sig_death[idx] or sig_rsi_sell[idx] or sig_bb_sell[idx]: direction = -1
        
        if direction == 0: continue
        
        atr = row['ATR_14']
        if pd.isna(atr) or atr == 0: continue
        
        entry_price = df.iloc[idx+1]['open']
        initial_sl_dist = 2 * atr
        
        # 1. Fixed Target Setup
        fixed_sl = entry_price - initial_sl_dist if direction == 1 else entry_price + initial_sl_dist
        fixed_tp = entry_price + (4 * atr) if direction == 1 else entry_price - (4 * atr)
        
        # 2. Chandelier Setup (3 ATR Trail)
        # 3. SMA Setup (Trail 50 SMA)
        
        outcomes = {'Fixed': None, 'Chandelier': None, 'SMA_Trail': None}
        closed_status = {'Fixed': False, 'Chandelier': False, 'SMA_Trail': False}
        
        # Run bar by bar
        highest_high = entry_price
        lowest_low = entry_price
        
        # State for trails
        chand_sl = fixed_sl # Start with initial risk
        sma_sl = fixed_sl
        
        for j in range(idx+1, len(df)):
            bar = df.iloc[j]
            
            # Update High/Low for Chandelier
            if direction == 1:
                highest_high = max(highest_high, bar['high'])
                chand_sl = max(chand_sl, highest_high - (3 * atr)) # Ratchet up
            else:
                lowest_low = min(lowest_low, bar['low'])
                chand_sl = min(chand_sl, lowest_low + (3 * atr)) # Ratchet down
                
            # Update SMA Trail
            current_sma = bar['SMA_50']
            if not pd.isna(current_sma):
                if direction == 1:
                    # Only move SL up if SMA is above break-even roughly, or logic varies.
                    # Simple rule: If SMA > current SL, move SL to SMA
                    if current_sma > sma_sl: sma_sl = current_sma
                else:
                    if current_sma < sma_sl: sma_sl = current_sma
            
            # CHECK EXITS
            
            # 1. Fixed
            if not closed_status['Fixed']:
                if direction == 1:
                    if bar['low'] <= fixed_sl: 
                        outcomes['Fixed'] = -initial_sl_dist
                        closed_status['Fixed'] = True
                    elif bar['high'] >= fixed_tp:
                        outcomes['Fixed'] = 4 * atr # Capped at 4ATR (2R)
                        closed_status['Fixed'] = True
                else:
                    if bar['high'] >= fixed_sl:
                        outcomes['Fixed'] = -initial_sl_dist
                        closed_status['Fixed'] = True
                    elif bar['low'] <= fixed_tp:
                        outcomes['Fixed'] = 4 * atr
                        closed_status['Fixed'] = True
                        
            # 2. Chandelier
            if not closed_status['Chandelier']:
                if direction == 1:
                    if bar['low'] <= chand_sl:
                        outcomes['Chandelier'] = chand_sl - entry_price
                        closed_status['Chandelier'] = True
                else:
                    if bar['high'] >= chand_sl:
                        outcomes['Chandelier'] = entry_price - chand_sl
                        closed_status['Chandelier'] = True
                        
            # 3. SMA Trail
            if not closed_status['SMA_Trail']:
                if direction == 1:
                    if bar['low'] <= sma_sl:
                        outcomes['SMA_Trail'] = sma_sl - entry_price
                        closed_status['SMA_Trail'] = True
                else:
                    if bar['high'] >= sma_sl:
                        outcomes['SMA_Trail'] = entry_price - sma_sl
                        closed_status['SMA_Trail'] = True
                        
            if all(closed_status.values()):
                break
                
        # Record Results
        # If still open, close at last price
        last_price = df.iloc[-1]['close']
        
        for strat in results.keys():
            res = outcomes[strat]
            if res is None: # Timed out
                if direction == 1: res = last_price - entry_price
                else: res = entry_price - last_price
                
            # Calculate R-Multiple
            r_mult = res / initial_sl_dist
            
            results[strat]['pips'] += res 
            results[strat]['max_r'] = max(results[strat]['max_r'], r_mult)
            
            if res > 0: results[strat]['wins'] += 1
            else: results[strat]['losses'] += 1
            
    return results

def main():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
        
    all_symbols = [s.name for s in mt5.symbols_get()]
    
    # Fuzzy match our targets
    target_roots = ["COCOA", "PALL", "US500", "Spotify", "EliLilly", "GOLD", "XAUUSD"]
    valid_targets = []
    
    for root in target_roots:
        # Find best match
        # Prioritize visible, then matching root
        matches = [s for s in all_symbols if root in s]
        if matches:
            # Pick first for now, or prefer Cash/Spot
            # e.g. US500Cash over US500-MAR26 if possible?
            # Mega Backtest said 'US500Cash' was good.
            best = matches[0]
            valid_targets.append(best)
            
    print(f"Testing on: {valid_targets}")
    
    print(f"{'SYMBOL':<15} | {'STRATEGY':<12} | {'WIN RATE':<8} | {'NET RETURN':<15} | {'MAX R'}")
    print("-" * 80)
    
    strategy = BookTechnicalStrategy()
    
    all_results = []
    
    for sym in valid_targets:
        print(f"Processing {sym}...")
        res = simulate_exits(sym, strategy)
        if not res: 
            print(f"  Skipping {sym} (No Data/Signals)")
            continue
        
        # Check if any signals were actually processed
        total_signals = res['Fixed']['wins'] + res['Fixed']['losses']
        if total_signals == 0:
             print(f"  Skipping {sym} (0 Signals Generated)")
             continue
        
        for strat_name, data in res.items():
            wins = data['wins']
            total = wins + data['losses']
            wr = (wins/total*100) if total > 0 else 0
            net = data['pips']
            max_r = data['max_r']
            
            row = f"{sym:<15} | {strat_name:<12} | {wr:<8.1f}% | {net:<15.2f} | {max_r:.1f}R"
            print(row)
            all_results.append({'Symbol': sym, 'Strategy': strat_name, 'WinRate': wr, 'Net': net, 'MaxR': max_r})
            
        print("-" * 80)
        
    pd.DataFrame(all_results).to_csv("exit_comparison.csv", index=False)
    print("Saved to exit_comparison.csv")
    mt5.shutdown()

if __name__ == "__main__":
    main()
