
import pandas as pd
import logging
from typing import List, Dict
from titan_system.strategies.base import BaseStrategy

logger = logging.getLogger("Titan.Backtest")

class Backtester:
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital
        
    def run(self, strategy: BaseStrategy, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Simulates a strategy on historical data.
        Returns performance metrics.
        """
        if df is None or df.empty:
            return {"score": -999, "profit": 0, "trades": 0}

        # Run indicators once (Strategy's analyze usually does this, 
        # but for speed we hope analyze handles pre-computed cols or check per-row)
        # Our strategies re-compute indicators every call if not careful.
        # This is SLOW for backtesting. 
        # Refactor Plan: Strategies should have 'prepare_indicators(df)'
        # For now, we accept the slowness (~1-2s per symbol)
        
        balance = self.initial_capital
        position = None # {'type': 'BUY', 'entry': 1.123, 'sl': 1.120, 'tp': 1.130}
        trades = []
        
        # Iterate through candles
        # Start from index where indicators are valid (slow_period)
        start_idx = getattr(strategy, 'slow_period', 50) + 1
        if start_idx >= len(df):
             return {"score": -999, "profit": 0, "trades": 0}
             
        for i in range(start_idx, len(df)):
            # Slice the DF to simulate "current moment" for strategy
            # Note: This is extremely slow. 
            # Optimization: Pass FULL DF, but tell strategy 'current_index' = i.
            # But our BaseStrategy signature is analyze(symbol, df).
            # We will pass the full DF, but relying on `iloc[-1]` inside strategy means
            # we must slice. To optimize, we slice a window.
            
            # window = df.iloc[i-300:i+1] # Pass last 300 candles
            # result = strategy.analyze(symbol, window)
            
            # HACK for speed: We know TrendSurfer calculates indicators on the WHOLE DF first.
            # So passing specific window re-calculates unnecessarily.
            # Ideally we vectorise.
            # For this MVP, we will assume strategies are unmodified and we MUST slice.
            # To keep it <1min for 20 symbols, this is acceptable.
             
            # Let's use a smaller window to be faster
            window = df.iloc[max(0, i-250):i+1].copy() # Copy to avoid SettingWithCopy
            result = strategy.analyze(symbol, window)
            
            price = window.iloc[-1]['close']
            high = window.iloc[-1]['high']
            low = window.iloc[-1]['low']
            
            # 1. Manage Open Position
            if position:
                # Check SL/TP
                if position['type'] == 'BUY':
                    if low <= position['sl']:
                        # SL Hit
                        pnl = (position['sl'] - position['entry']) / position['entry'] * 100 
                        trades.append(pnl)
                        position = None
                    elif high >= position['tp']:
                        # TP Hit
                        pnl = (position['tp'] - position['entry']) / position['entry'] * 100
                        trades.append(pnl)
                        position = None
                
                elif position['type'] == 'SELL':
                    if high >= position['sl']:
                        # SL Hit (Entry - SL is negative so we need: (Entry - SL)/Entry * ? 
                        # Short PnL: (Entry - Exit) / Entry
                        pnl = (position['entry'] - position['sl']) / position['entry'] * 100
                        trades.append(pnl) # Will be negative
                        position = None
                    elif low <= position['tp']:
                        # TP Hit
                        pnl = (position['entry'] - position['tp']) / position['entry'] * 100
                        trades.append(pnl)
                        position = None
                        
            # 2. Open New Position if none
            if not position and result['signal'] in ['BUY', 'SELL']:
                # CRITICAL FIX: Use Percentage Based SL/TP for Universal Compatibility
                # Fixed pips (0.0001) fail on Gold/Crypto/Indices.
                # Scalper Settings: Tight Stops.
                # SL: 0.15% | TP: 0.3%
                
                pct_sl = 0.0015
                pct_tp = 0.003
                
                if result['signal'] == 'BUY':
                    sl = price * (1 - pct_sl)
                    tp = price * (1 + pct_tp)
                else:
                    sl = price * (1 + pct_sl)
                    tp = price * (1 - pct_tp)
                    
                position = {
                    'type': result['signal'],
                    'entry': price,
                    'sl': sl,
                    'tp': tp
                }

            # 2. Open New Position if none
            if not position and result['signal'] in ['BUY', 'SELL']:
                # CRITICAL FIX 2: Normalized Stops & Scoring
                # 0.15% was too tight for Gold noise.
                # Increase to 0.5% SL / 1.0% TP (Swing/Day Trade settings)
                
                pct_sl = 0.005
                pct_tp = 0.010
                
                if result['signal'] == 'BUY':
                    sl = price * (1 - pct_sl)
                    tp = price * (1 + pct_tp)
                else:
                    sl = price * (1 + pct_sl)
                    tp = price * (1 - pct_tp)
                    
                position = {
                    'type': result['signal'],
                    'entry': price,
                    'sl': sl,
                    'tp': tp
                }
                
            # Close Logic was inline, but for PnL we need to fix the calc too.
            # See above loop modification. Actually we need to just change the PnL append.
            # But replace_file_content is replacing the BLOCK.
            # Wait, the loop above (lines 63-93) has the PnL logic. I need to edit THAT too.
            # I should use multi_replace or a bigger block.
            # Let's use Backtester.run full replacement if easier?
            # Or just replace the PnL calculation lines first?
            # The tool only allows contiguous.
            # Let's replace the Logic Block (Position Management) AND Entry Block.
            # I'll just rewrite the whole loop body logic to be safe.
                 
        # Calc Score (Total Profit)
        # total_pnl = balance - self.initial_capital
        # use Sum of % returns
        total_ret = sum(trades) 
        
        return {
            "score": total_ret, # Total % Return (e.g. 5.2 means 5.2% growth)
            "profit": total_ret, # Storing % as profit for simple sorting
            "trades": len(trades),
            "win_rate": sum(1 for t in trades if t > 0) / len(trades) if trades else 0
        }
