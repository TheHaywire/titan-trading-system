
import sys
import os
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.strategies.book_strategies import BookTechnicalStrategy

def run_test():
    print("=" * 70)
    print("TESTING BOOK STRATEGIES: MA Cross, RSI, Bollinger")
    print("=" * 70)
    
    if not mt5.initialize():
        print(f"MT5 Initialization Failed: {mt5.last_error()}")
        return

    strategy = BookTechnicalStrategy()
    
    # Symbols to test
    # Note: Using symbols likely to be in Market Watch
    symbols = ["GOLD", "EURUSD", "BTCUSD", "US100"] 
    
    timeframe = mt5.TIMEFRAME_H1
    bars = 1000
    
    overall_stats = {
        'signals': 0,
        'wins': 0,
        'losses': 0,
        'pips': 0.0
    }

    for symbol in symbols:
        print(f"\n--- Analyzing {symbol} (H1) ---")
        
        # Check if symbol exists
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"  Symbol {symbol} not found or not enabled.")
            continue
            
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        
        if rates is None or len(rates) < 250:
            print(f"  Insufficient data for {symbol}.")
            continue
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Run Backtest Loop
        # We walk forward bar by bar to simulate live signals
        
        symbol_signals = 0
        symbol_wins = 0
        symbol_losses = 0
        symbol_pips = 0.0
        
        # Pre-calc indicators for speed (the strategy class allows full df calc)
        # But to simulate "at that moment", we really just need to know if a signal fired at index i
        
        # Let's use the analyze method which does the logic on the full df
        # But we need to verify outcomes.
        
        # To verify outcomes properly without lookahead bias during signal GENERATION:
        # The strategy.analyze() method uses the *entire* dataframe to generate signals.
        # It internally checks if a crossover occurred at the *end*.
        # To backtest, we can't just call analyze(full_df) once because we want PnL.
        # Actually we CAN call analyze(full_df) to get ALL signals that occurred in history,
        # then iterate through them to check the result. 
        # The indicators are past-independent (SMA at index 100 doesn't depend on index 101).
        
        # Get all signals in history
        # We wrap this in a loop to ensure we aren't peeking, but technically SMA calculation is safe.
        
        df_indicators = strategy.calculate_indicators(df)
        
        print(f"  Data loaded: {len(df)} candles.")
        
        start_index = 205 # Allow for 200 SMA + buffer
        
        for i in range(start_index, len(df) - 1): # Scan up to end
            curr = df_indicators.iloc[i]
            prev = df_indicators.iloc[i-1]
            
            signal_type = None
            direction = 0
            
            # Re-implementing logic checks here to iterate through history efficiently
            # 1. Golden Cross
            if prev['SMA_50'] <= prev['SMA_200'] and curr['SMA_50'] > curr['SMA_200']:
                signal_type = "MA_Golden_Cross"
                direction = 1
                
            # 2. Death Cross
            elif prev['SMA_50'] >= prev['SMA_200'] and curr['SMA_50'] < curr['SMA_200']:
                signal_type = "MA_Death_Cross"
                direction = -1
                
            # 3. RSI Oversold Buy
            elif prev['RSI_14'] < 30 and curr['RSI_14'] >= 30:
                signal_type = "RSI_Oversold_Buy"
                direction = 1
                
            # 4. RSI Overbought Sell
            elif prev['RSI_14'] > 70 and curr['RSI_14'] <= 70:
                signal_type = "RSI_Overbought_Sell"
                direction = -1
                
            # 5. BB Breakout Buy
            elif prev['close'] <= prev['BB_Upper'] and curr['close'] > curr['BB_Upper']:
                signal_type = "BB_Breakout_Buy"
                direction = 1
                
            # 6. BB Breakout Sell
            elif prev['close'] >= prev['BB_Lower'] and curr['close'] < curr['BB_Lower']:
                signal_type = "BB_Breakout_Sell"
                direction = -1
            
            if signal_type:
                # Expert Execution: Use ATR for Stop Loss and Take Profit
                # Stop Loss = 2 * ATR
                # Take Profit = 4 * ATR (2:1 Reward:Risk)
                
                entry_price = df.iloc[i+1]['open'] # Enter on next open
                atr = curr['ATR_14']
                
                if pd.isna(atr) or atr == 0:
                    continue

                stop_distance = 2 * atr
                target_distance = 4 * atr
                
                if direction == 1: # BUY
                    sl_price = entry_price - stop_distance
                    tp_price = entry_price + target_distance
                else: # SELL
                    sl_price = entry_price + stop_distance
                    tp_price = entry_price - target_distance
                
                # Simulate Trade Lifecycle
                # Scan future bars to see what hit first: SL or TP
                # Cap max hold time at 48 bars (2 days)
                
                outcome_pips = 0
                trade_result = "TIMEOUT"
                
                for j in range(i+1, min(len(df), i+49)):
                    bar = df.iloc[j]
                    
                    if direction == 1: # Long
                        if bar['low'] <= sl_price:
                            outcome_pips = -stop_distance
                            trade_result = "LOSS"
                            break
                        if bar['high'] >= tp_price:
                            outcome_pips = target_distance
                            trade_result = "WIN"
                            break
                    else: # Short
                        if bar['high'] >= sl_price:
                            outcome_pips = -stop_distance
                            trade_result = "LOSS"
                            break
                        if bar['low'] <= tp_price:
                            outcome_pips = target_distance
                            trade_result = "WIN"
                            break
                            
                # If timeout, close at close of last bar
                if trade_result == "TIMEOUT":
                    last_bar = df.iloc[min(len(df)-1, i+49)]
                    diff = (last_bar['close'] - entry_price) * direction
                    outcome_pips = diff
                    
                    if outcome_pips > 0:
                        trade_result = "WIN"
                    else:
                        trade_result = "LOSS"

                # Normalize to pips
                # ATR is in price units, so outcome_pips is in price units
                
                if "JPY" in symbol:
                    pips = outcome_pips * 100
                elif "XAU" in symbol or "BTC" in symbol or "US100" in symbol:
                    pips = outcome_pips * 10 
                else:
                    pips = outcome_pips * 10000
                
                if pips > 0:
                    symbol_wins += 1
                else:
                    symbol_losses += 1
                    
                symbol_pips += pips
                symbol_signals += 1

        
        win_rate = 0
        if symbol_signals > 0:
            win_rate = (symbol_wins / symbol_signals) * 100
            
        print(f"  Results: {symbol_signals} signals")
        print(f"  Win Rate: {win_rate:.1f}% ({symbol_wins}/{symbol_losses})")
        print(f"  Net Pips: {symbol_pips:.1f}")
        
        overall_stats['signals'] += symbol_signals
        overall_stats['wins'] += symbol_wins
        overall_stats['losses'] += symbol_losses
        overall_stats['pips'] += symbol_pips

    print("\n" + "=" * 30)
    print("OVERALL BOOK STRATEGY PERFORMANCE")
    print("=" * 30)
    
    total_wr = 0
    if overall_stats['signals'] > 0:
        total_wr = (overall_stats['wins'] / overall_stats['signals']) * 100
        
    print(f"Total Signals: {overall_stats['signals']}")
    print(f"Total Win Rate: {total_wr:.1f}%")
    print(f"Total Net Pips: {overall_stats['pips']:.1f}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_test()
