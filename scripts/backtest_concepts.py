"""
BACKTEST ALL 9 BOOKS CONCEPTS
==============================
Test each concept on historical data to validate performance.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import List

@dataclass
class Trade:
    entry_time: datetime
    exit_time: datetime
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    profit_pips: float
    reason: str
    score: int

class BacktestEngine:
    def __init__(self):
        self.trades = []
        
    def initialize_mt5(self):
        if not mt5.initialize():
            print(f"❌ MT5 init failed: {mt5.last_error()}")
            return False
        print("✅ MT5 Connected")
        return True
    
    def get_historical_data(self, symbol, days=30):
        """Get historical data for backtesting"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, days * 96)  # 96 M15 bars per day
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def calculate_indicators(self, df):
        """Calculate all indicators"""
        # EMA
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
        
        # Momentum
        df['MOM'] = df['close'].pct_change(5) * 100
        
        # Volume
        df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
        df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)
        
        # ATR
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        # ADX
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        atr_adx = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr_adx)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr_adx)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX'] = dx.rolling(14).mean()
        
        return df
    
    def backtest_baseline(self, df, symbol):
        """Baseline: Simple RSI/EMA strategy"""
        print("\n📊 BASELINE: Simple RSI + EMA")
        trades = []
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Simple RSI extremes
            if curr['RSI'] < 20:
                direction = "BUY"
                score = 90
                reason = "RSI oversold"
            elif curr['RSI'] > 80:
                direction = "SELL"
                score = 90
                reason = "RSI overbought"
            else:
                continue
            
            # Simulate trade
            entry_price = curr['close']
            
            # Exit after 20 bars or TP/SL
            info = mt5.symbol_info(symbol)
            point = info.point if info else 0.0001
            
            sl_distance = 500 * point
            tp_distance = 1000 * point
            
            if direction == "BUY":
                sl = entry_price - sl_distance
                tp = entry_price + tp_distance
            else:
                sl = entry_price + sl_distance
                tp = entry_price - tp_distance
            
            # Look for exit
            exit_idx = None
            exit_price = None
            
            for j in range(i+1, min(i+50, len(df))):
                bar = df.iloc[j]
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['high'] >= tp:
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if bar['high'] >= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['low'] <= tp:
                        exit_price = tp
                        exit_idx = j
                        break
            
            if exit_idx is None:
                continue
            
            profit_pips = (exit_price - entry_price) / point if direction == "BUY" else (entry_price - exit_price) / point
            
            trades.append(Trade(
                entry_time=curr['time'],
                exit_time=df.iloc[exit_idx]['time'],
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                profit_pips=profit_pips,
                reason=reason,
                score=score
            ))
        
        return trades
    
    def backtest_with_vpa(self, df, symbol):
        """Add Volume Price Analysis filter"""
        print("\n📊 WITH VPA: Volume confirmation")
        trades = []
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            
            # VPA filter: Skip low volume
            if curr['VOL_RATIO'] < 0.8:
                continue
            
            # Boost score for high volume
            vol_boost = 10 if curr['VOL_RATIO'] > 1.5 else 0
            
            # RSI signals
            if curr['RSI'] < 20:
                direction = "BUY"
                score = 90 + vol_boost
                reason = "RSI + VPA"
            elif curr['RSI'] > 80:
                direction = "SELL"
                score = 90 + vol_boost
                reason = "RSI + VPA"
            else:
                continue
            
            # Same exit logic as baseline
            entry_price = curr['close']
            info = mt5.symbol_info(symbol)
            point = info.point if info else 0.0001
            sl_distance = 500 * point
            tp_distance = 1000 * point
            
            if direction == "BUY":
                sl = entry_price - sl_distance
                tp = entry_price + tp_distance
            else:
                sl = entry_price + sl_distance
                tp = entry_price - tp_distance
            
            exit_idx = None
            exit_price = None
            
            for j in range(i+1, min(i+50, len(df))):
                bar = df.iloc[j]
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['high'] >= tp:
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if bar['high'] >= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['low'] <= tp:
                        exit_price = tp
                        exit_idx = j
                        break
            
            if exit_idx is None:
                continue
            
            profit_pips = (exit_price - entry_price) / point if direction == "BUY" else (entry_price - exit_price) / point
            
            trades.append(Trade(
                entry_time=curr['time'],
                exit_time=df.iloc[exit_idx]['time'],
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                profit_pips=profit_pips,
                reason=reason,
                score=score
            ))
        
        return trades
    
    def backtest_with_adx(self, df, symbol):
        """Add ADX trend filter"""
        print("\n📊 WITH ADX: Trend filter")
        trades = []
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            
            # VPA filter
            if curr['VOL_RATIO'] < 0.8:
                continue
            
            # ADX filter: Only strong trends
            if curr['ADX'] < 20:
                continue
            
            adx_boost = 10 if curr['ADX'] > 30 else 0
            vol_boost = 10 if curr['VOL_RATIO'] > 1.5 else 0
            
            if curr['RSI'] < 20:
                direction = "BUY"
                score = 90 + vol_boost + adx_boost
                reason = "RSI + VPA + ADX"
            elif curr['RSI'] > 80:
                direction = "SELL"
                score = 90 + vol_boost + adx_boost
                reason = "RSI + VPA + ADX"
            else:
                continue
            
            # Exit logic
            entry_price = curr['close']
            info = mt5.symbol_info(symbol)
            point = info.point if info else 0.0001
            sl_distance = 500 * point
            tp_distance = 1000 * point
            
            if direction == "BUY":
                sl = entry_price - sl_distance
                tp = entry_price + tp_distance
            else:
                sl = entry_price + sl_distance
                tp = entry_price - tp_distance
            
            exit_idx = None
            exit_price = None
            
            for j in range(i+1, min(i+50, len(df))):
                bar = df.iloc[j]
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['high'] >= tp:
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if bar['high'] >= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['low'] <= tp:
                        exit_price = tp
                        exit_idx = j
                        break
            
            if exit_idx is None:
                continue
            
            profit_pips = (exit_price - entry_price) / point if direction == "BUY" else (entry_price - exit_price) / point
            
            trades.append(Trade(
                entry_time=curr['time'],
                exit_time=df.iloc[exit_idx]['time'],
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                profit_pips=profit_pips,
                reason=reason,
                score=score
            ))
        
        return trades
    
    def analyze_results(self, trades, label):
        """Analyze backtest results"""
        if not trades:
            print(f"❌ {label}: No trades\n")
            return
        
        wins = [t for t in trades if t.profit_pips > 0]
        losses = [t for t in trades if t.profit_pips <= 0]
        
        total_trades = len(trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = np.mean([t.profit_pips for t in wins]) if wins else 0
        avg_loss = np.mean([t.profit_pips for t in losses]) if losses else 0
        
        total_pips = sum(t.profit_pips for t in trades)
        avg_pips = total_pips / total_trades if total_trades > 0 else 0
        
        expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)
        
        print(f"\n{'='*60}")
        print(f"📊 {label}")
        print(f"{'='*60}")
        print(f"Total trades: {total_trades}")
        print(f"Wins: {win_count} ({win_rate:.1f}%)")
        print(f"Losses: {loss_count}")
        print(f"Avg win: {avg_win:.1f} pips")
        print(f"Avg loss: {avg_loss:.1f} pips")
        print(f"Total: {total_pips:.1f} pips")
        print(f"Avg per trade: {avg_pips:.1f} pips")
        print(f"Expectancy: {expectancy:.2f} pips")
        
        if avg_loss != 0:
            profit_factor = abs(avg_win * win_count / (avg_loss * loss_count))
            print(f"Profit Factor: {profit_factor:.2f}")
        
        print(f"{'='*60}\n")
        
        return {
            'total': total_trades,
            'win_rate': win_rate,
            'expectancy': expectancy,
            'total_pips': total_pips
        }

def main():
    print("\n🚀 BACKTESTING ALL 9 BOOKS CONCEPTS")
    print("Testing on 30 days of historical data...\n")
    
    engine = BacktestEngine()
    
    if not engine.initialize_mt5():
        return
    
    symbol = "EURUSD"
    
    # Get data
    print(f"📥 Loading {symbol} historical data...")
    df = engine.get_historical_data(symbol, days=30)
    
    if df is None:
        print("❌ No data available")
        return
    
    print(f"✅ Loaded {len(df)} bars")
    
    # Calculate indicators
    print("📊 Calculating indicators...")
    df = engine.calculate_indicators(df)
    
    # Run backtests
    results = {}
    
    # 1. Baseline
    baseline_trades = engine.backtest_baseline(df, symbol)
    results['baseline'] = engine.analyze_results(baseline_trades, "BASELINE: Simple RSI")
    
    # 2. With VPA
    vpa_trades = engine.backtest_with_vpa(df, symbol)
    results['vpa'] = engine.analyze_results(vpa_trades, "WITH VPA: Volume Filter")
    
    # 3. With ADX
    adx_trades = engine.backtest_with_adx(df, symbol)
    results['adx'] = engine.analyze_results(adx_trades, "WITH ADX: Trend + Volume")
    
    # Comparison
    print("\n" + "="*60)
    print("📊 COMPARISON")
    print("="*60)
    
    if results.get('baseline'):
        base_wr = results['baseline']['win_rate']
        base_exp = results['baseline']['expectancy']
        
        if results.get('vpa'):
            vpa_wr = results['vpa']['win_rate']
            vpa_exp = results['vpa']['expectancy']
            print(f"VPA Impact: Win rate {base_wr:.1f}% → {vpa_wr:.1f}% ({vpa_wr-base_wr:+.1f}%)")
            print(f"            Expectancy {base_exp:.2f} → {vpa_exp:.2f} ({vpa_exp-base_exp:+.2f})")
        
        if results.get('adx'):
            adx_wr = results['adx']['win_rate']
            adx_exp = results['adx']['expectancy']
            print(f"ADX Impact: Win rate {base_wr:.1f}% → {adx_wr:.1f}% ({adx_wr-base_wr:+.1f}%)")
            print(f"            Expectancy {base_exp:.2f} → {adx_exp:.2f} ({adx_exp-base_exp:+.2f})")
    
    print("="*60)
    
    mt5.shutdown()
    print("\n✅ BACKTEST COMPLETE")

if __name__ == "__main__":
    main()
