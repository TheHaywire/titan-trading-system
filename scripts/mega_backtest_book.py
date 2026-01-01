
import sys
import os
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.strategies.book_strategies import BookTechnicalStrategy

def fast_backtest_symbol(symbol, strategy, timeframe=mt5.TIMEFRAME_H1, bars=1000):
    """
    Runs a fast backtest on a single symbol.
    Returns dict with stats.
    """
    # Fetch Data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) < 500:
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate Indicators
    try:
        df = strategy.calculate_indicators(df)
    except Exception as e:
        return None

    # Vectorized Signal Generation (Fast)
    # create shift columns
    df['prev_SMA_50'] = df['SMA_50'].shift(1)
    df['prev_SMA_200'] = df['SMA_200'].shift(1)
    df['prev_RSI'] = df['RSI_14'].shift(1)
    df['prev_close'] = df['close'].shift(1)
    df['prev_BB_Upper'] = df['BB_Upper'].shift(1)
    df['prev_BB_Lower'] = df['BB_Lower'].shift(1)

    # Define Signals
    # 1. Golden Cross
    sig_golden = (df['prev_SMA_50'] <= df['prev_SMA_200']) & (df['SMA_50'] > df['SMA_200'])
    
    # 2. Death Cross
    sig_death = (df['prev_SMA_50'] >= df['prev_SMA_200']) & (df['SMA_50'] < df['SMA_200'])
    
    # 3. RSI Oversold Buy
    sig_rsi_buy = (df['prev_RSI'] < 30) & (df['RSI_14'] >= 30)
    
    # 4. RSI Overbought Sell
    sig_rsi_sell = (df['prev_RSI'] > 70) & (df['RSI_14'] <= 70)
    
    # 5. BB Breakout Buy
    sig_bb_buy = (df['prev_close'] <= df['prev_BB_Upper']) & (df['close'] > df['BB_Upper'])
    
    # 6. BB Breakout Sell
    sig_bb_sell = (df['prev_close'] >= df['prev_BB_Lower']) & (df['close'] < df['BB_Lower'])

    # Combine
    # We will run a loop only on candles where ANY signal is true
    # This optimizes speed significantly
    
    signal_mask = sig_golden | sig_death | sig_rsi_buy | sig_rsi_sell | sig_bb_buy | sig_bb_sell
    signal_indices = df.index[signal_mask].tolist()
    
    wins = 0
    losses = 0
    total_pips = 0.0
    signal_count = 0
    
    if not signal_indices:
        return {
            'symbol': symbol,
            'signals': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'net_pips': 0,
            'expectancy': 0
        }

    # Iterate through signals
    # Skip first 205 bars (warmup)
    for idx in signal_indices:
        if idx < 205 or idx > len(df) - 50:
            continue
            
        row = df.iloc[idx]
        direction = 0
        
        # Determine Direction
        if sig_golden[idx] or sig_rsi_buy[idx] or sig_bb_buy[idx]:
            direction = 1
        elif sig_death[idx] or sig_rsi_sell[idx] or sig_bb_sell[idx]:
            direction = -1
            
        if direction == 0: continue
        
        # Trade Logic (ATR Based)
        atr = row['ATR_14']
        if pd.isna(atr) or atr == 0: continue
        
        entry_price = df.iloc[idx+1]['open'] # Next Open
        sl_dist = 2 * atr
        tp_dist = 4 * atr
        
        sl_price = entry_price - sl_dist if direction == 1 else entry_price + sl_dist
        tp_price = entry_price + tp_dist if direction == 1 else entry_price - tp_dist
        
        # Check outcome in next 48 bars
        outcome = 0 
        result = "TIMEOUT"
        
        # Mini loop for outcome
        # We can optimize this by using vector search but a small loop of 48 is fast enough
        end_scan = min(len(df), idx + 49)
        
        for j in range(idx+1, end_scan):
            bar = df.iloc[j]
            if direction == 1:
                if bar['low'] <= sl_price:
                    outcome = -sl_dist
                    result = "LOSS"
                    break
                if bar['high'] >= tp_price:
                    outcome = tp_dist
                    result = "WIN"
                    break
            else:
                if bar['high'] >= sl_price:
                    outcome = -sl_dist
                    result = "LOSS"
                    break
                if bar['low'] <= tp_price:
                    outcome = tp_dist
                    result = "WIN"
                    break
        
        if result == "TIMEOUT":
            last_close = df.iloc[end_scan-1]['close']
            outcome = (last_close - entry_price) * direction
        
        # Normalize Pips
        if "JPY" in symbol:
            pips = outcome * 100
        elif "XAU" in symbol or "BTC" in symbol or "US100" in symbol or "SPX" in symbol:
             pips = outcome * 10
        else:
            pips = outcome * 10000
            
        total_pips += pips
        if pips > 0: wins += 1
        else: losses += 1
        signal_count += 1

    win_rate = (wins / signal_count * 100) if signal_count > 0 else 0
    expectancy = (total_pips / signal_count) if signal_count > 0 else 0
    
    return {
        'symbol': symbol,
        'signals': signal_count,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'net_pips': total_pips,
        'expectancy': expectancy
    }

def main():
    print("="*80)
    print(" MEGA BACKTEST: RUNNING BOOK STRATEGIES ON FULL UNIVERSE")
    print("="*80)
    
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
        
    all_symbols = mt5.symbols_get()
    
    # Categorize to Prioritize
    # We want to run the liquid stuff first
    
    majors = []
    indices = []
    crypto = []
    commodities = []
    stocks = []
    others = []
    
    for s in all_symbols:
        n = s.name
        if not s.visible and s.trade_mode == 0: continue
        
        if "XAU" in n or "GOLD" in n or "OIL" in n or "SILVER" in n:
             commodities.append(n)
        elif "BTC" in n or "ETH" in n or "XRP" in n:
             crypto.append(n)
        elif "US500" in n or "JP225" in n or "GER40" in n or "US30" in n:
             indices.append(n)
        elif "USD" in n or "EUR" in n or "JPY" in n:
             majors.append(n)
        elif "." in n or len(n) < 6: # Heuristic for stocks
             stocks.append(n)
        else:
             others.append(n)
             
    # Execution Order: Commodities -> Majors -> Indices -> Crypto -> Others -> Stocks
    # Stocks are numerous and slow, effectively "tail"
    
    execution_list = commodities + majors + indices + crypto + others + stocks
    # Remove duplicates
    execution_list = list(dict.fromkeys(execution_list))
    
    print(f"Prioritized {len(execution_list)} symbols.")
    
    strategy = BookTechnicalStrategy()
    results = []
    
    start_time = time.time()
    
    output_file = "mega_backtest_results.csv"
    
    for i, symbol in enumerate(execution_list):
        res = fast_backtest_symbol(symbol, strategy)
        if res:
            results.append(res)
            
        if i % 10 == 0 and i > 0:
            print(f"Processed {i}/{len(execution_list)} symbols... ({len(results)} valid)")
            # Incremental Save
            pd.DataFrame(results).to_csv(output_file, index=False)
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nCompleted in {duration:.1f} seconds.")
    print(f"Successfully tested {len(results)} symbols.")
    
    # Final Save
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res.sort_values('expectancy', ascending=False, inplace=True)
        df_res.to_csv(output_file, index=False)
        
        print(f"Saved results to {output_file}")
        
        # Top 10
        print("\nTOP 10 PERFORMERS (By Expectancy):")
        print(df_res.head(10)[['symbol', 'win_rate', 'expectancy', 'signals']].to_string(index=False))
        
        # Bottom 10
        print("\nBOTTOM 10 PERFORMERS:")
        print(df_res.tail(10)[['symbol', 'win_rate', 'expectancy', 'signals']].to_string(index=False))

    mt5.shutdown()

if __name__ == "__main__":
    main()
