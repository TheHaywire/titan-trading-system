
import sys
import os
import pandas as pd
import MetaTrader5 as mt5

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.strategies.book_strategies import BookTechnicalStrategy

def run_optimization_test():
    print("=" * 80)
    print(" OPTIMIZING FAT TAILS: VALIDATING TREND FILTERS ON TOP PERFORMERS")
    print("=" * 80)
    
    if not mt5.initialize():
        print("MT5 Failed")
        return
        
    # Load Top 20 from previous mega test (assuming file exists, else hardcode a few known winners)
    try:
        df_mega = pd.read_csv("mega_backtest_results.csv")
        top_symbols = df_mega.head(20)['symbol'].tolist()
        print(f"Loaded Top 20 Survivors: {top_symbols}")
    except Exception:
        print("Could not load mega_backtest_results.csv, using default list.")
        top_symbols = ["COCOA", "PALL-MAR26", "GerMid50Cash", "US500Cash", "JP225Cash", "Rheinmetall", "Givaudan"]

    # Initialize Strategies
    strat_raw = BookTechnicalStrategy(use_trend_filter=False)
    strat_filtered = BookTechnicalStrategy(use_trend_filter=True)
    
    results = []
    
    for symbol in top_symbols:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000)
        if rates is None or len(rates) < 500: continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # We will use the calculate_indicators from one, as indicators are same
        df = strat_raw.calculate_indicators(df)
        
        # LOGIC REPLICATION for BACKTEST
        # Filter: Bullish if Price > SMA200. Bearish if Price < SMA200.
        
        # Vectorized simulation
        # Base Signals
        df['prev_SMA_50'] = df['SMA_50'].shift(1)
        df['prev_SMA_200'] = df['SMA_200'].shift(1)
        df['prev_RSI'] = df['RSI_14'].shift(1)
        df['prev_close'] = df['close'].shift(1)
        df['prev_BB_Upper'] = df['BB_Upper'].shift(1)
        df['prev_BB_Lower'] = df['BB_Lower'].shift(1)
        
        # Raw Signals
        sig_golden = (df['prev_SMA_50'] <= df['prev_SMA_200']) & (df['SMA_50'] > df['SMA_200'])
        sig_death = (df['prev_SMA_50'] >= df['prev_SMA_200']) & (df['SMA_50'] < df['SMA_200'])
        sig_rsi_buy = (df['prev_RSI'] < 30) & (df['RSI_14'] >= 30)
        sig_rsi_sell = (df['prev_RSI'] > 70) & (df['RSI_14'] <= 70)
        sig_bb_buy = (df['prev_close'] <= df['prev_BB_Upper']) & (df['close'] > df['BB_Upper'])
        sig_bb_sell = (df['prev_close'] >= df['prev_BB_Lower']) & (df['close'] < df['BB_Lower'])
        
        # Trend Filters
        # Note: We check the current close vs 200 SMA as per the class modification
        trend_bull = df['close'] > df['SMA_200']
        trend_bear = df['close'] < df['SMA_200']
        
        # calculate results for RAW vs FILTERED
        for mode in ['RAW', 'FILTERED']:
            wins = 0
            count = 0
            pips = 0.0
            
            for i in range(205, len(df)-50):
                # Check signals at i
                # Note: We must group them. Golden/Death are exempt from filters usually to avoid circular blocking
                # but RSI/BB are subject to filter.
                
                is_buy = False
                is_sell = False
                
                # Check specifics
                if sig_golden[i]: is_buy = True # Always take trend change
                if sig_death[i]: is_sell = True
                
                if mode == 'RAW':
                    if sig_rsi_buy[i] or sig_bb_buy[i]: is_buy = True
                    if sig_rsi_sell[i] or sig_bb_sell[i]: is_sell = True
                else:
                    if (sig_rsi_buy[i] or sig_bb_buy[i]) and trend_bull[i]: is_buy = True
                    if (sig_rsi_sell[i] or sig_bb_sell[i]) and trend_bear[i]: is_sell = True
                
                direction = 0
                if is_buy: direction = 1
                elif is_sell: direction = -1
                
                if direction == 0: continue
                
                # Execute Trade (ATR Rule)
                atr = df.iloc[i]['ATR_14']
                if pd.isna(atr) or atr == 0: continue
                
                entry = df.iloc[i+1]['open']
                sl = 2 * atr
                tp = 4 * atr
                
                outcome = 0
                res = "TIMEOUT"
                
                for j in range(i+1, i+49):
                    bar = df.iloc[j]
                    if direction == 1:
                        if bar['low'] <= entry - sl:
                            outcome = -sl
                            res = "LOSS"
                            break
                        if bar['high'] >= entry + tp:
                            outcome = tp
                            res = "WIN"
                            break
                    else:
                        if bar['high'] >= entry + sl:
                            outcome = -sl
                            res = "LOSS"
                            break
                        if bar['low'] <= entry - tp:
                            outcome = tp
                            res = "WIN"
                            break
                
                if res == "TIMEOUT":
                    close_price = df.iloc[i+48]['close']
                    outcome = (close_price - entry) * direction
                    
                if "JPY" in symbol: norm_pips = outcome * 100
                elif "XAU" in symbol or "BTC" in symbol: norm_pips = outcome * 10
                else: norm_pips = outcome * 10000
                
                pips += norm_pips
                if norm_pips > 0: wins += 1
                count += 1
                
            win_rate = (wins/count*100) if count > 0 else 0
            expectancy = (pips/count) if count > 0 else 0
            
            results.append({
                'symbol': symbol,
                'mode': mode,
                'signals': count,
                'win_rate': win_rate,
                'net_pips': pips
            })

    # Summary Analysis
    df_res = pd.DataFrame(results)
    
    print("\n" + "="*60)
    print(" COMPARISON: RAW vs TREND FILTERED")
    print("="*60)
    
    # Pivot to compare side by side
    pivot = df_res.pivot(index='symbol', columns='mode', values=['win_rate', 'net_pips', 'signals'])
    print(pivot)
    
    # Aggregate Stats
    avg_raw = df_res[df_res['mode']=='RAW']['win_rate'].mean()
    avg_filt = df_res[df_res['mode']=='FILTERED']['win_rate'].mean()
    
    print(f"\nAverage Win Rate (RAW): {avg_raw:.1f}%")
    print(f"Average Win Rate (FILTERED): {avg_filt:.1f}%")
    
    if avg_filt > avg_raw:
        print("\nSUCCESS: Trend Filtering improved the Strategy!")
    else:
        print("\nRESULT: Trend Filtering did not improve Win Rate significantly on these symbols.")

    mt5.shutdown()

if __name__ == "__main__":
    run_optimization_test()
