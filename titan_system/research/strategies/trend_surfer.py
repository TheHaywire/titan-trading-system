import pandas as pd
import vectorbt as vbt
import ta
import logging

class TrendSurferStrategy:
    """
    Trend Following Strategy migrated to Titan v2 Architecture.
    
    Logic:
    - Long: SMA_Fast > SMA_Slow AND RSI < 70 AND ADX > 25
    - Short: SMA_Fast < SMA_Slow AND RSI > 30 AND ADX > 25
    """
    def __init__(self, fast_period=50, slow_period=200, rsi_period=14, adx_threshold=25):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
        self.adx_threshold = adx_threshold
        self.logger = logging.getLogger("Titan.Strategy.TrendSurfer")

    def run_backtest(self, df: pd.DataFrame, initial_capital=10000):
        """
        Run a vectorized backtest using VectorBT.
        """
        if df.empty:
            return None
            
        price = df['close']
        high = df['high']
        low = df['low']
        
        # 1. Indicators (Vectorized)
        sma_fast = vbt.MA.run(price, self.fast_period).ma
        sma_slow = vbt.MA.run(price, self.slow_period).ma
        rsi = vbt.RSI.run(price, window=self.rsi_period).rsi
        
        # ADX is tricky in pure VBT without wrapper, so we use pandas/ta for indicator calculation usually
        # But we can calculate it using pandas apply or ta library on the whole DF first
        # Since vbt accepts pandas/numpy arrays, we can mix.
        
        # Using TA library for ADX (returns Series)
        adx_ind = ta.trend.ADXIndicator(high, low, price, window=14)
        adx = adx_ind.adx()
        
        # 2. Logic arrays
        # Ensure alignment
        trend_up = sma_fast > sma_slow
        trend_down = sma_fast < sma_slow
        strong_trend = adx > self.adx_threshold
        
        entries = trend_up & strong_trend & (rsi < 70) 
        exits = trend_down # Simple exit on trend reversal
        
        # Short logic (if we want shorts)
        short_entries = trend_down & strong_trend & (rsi > 30)
        short_exits = trend_up
        
        # 3. Simulation
        # For simplicity in this demo, we'll just test Longs or Long/Short
        portfolio = vbt.Portfolio.from_signals(
            price, 
            entries, 
            exits, 
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=initial_capital,
            fees=0.0001,
            freq='1h' # Assumption
        )
        
        return portfolio

    def get_signal(self, df: pd.DataFrame) -> dict:
        """
        Get signal for the latest bar (Live Trading).
        Returns: {'order_type': 'BUY'/'SELL'/'HOLD', 'comment': str, 'confidence': float}
        """
        if df is None or len(df) < self.slow_period:
            return {"order_type": "HOLD", "comment": "Not enough data"}

        # Calculate indicators on the DataFrame (Sequential)
        # We only strictly need the last few rows but calculating on passed DF is safer
        df = df.copy()
        
        df['sma_fast'] = ta.trend.sma_indicator(df['close'], window=self.fast_period)
        df['sma_slow'] = ta.trend.sma_indicator(df['close'], window=self.slow_period)
        df['rsi'] = ta.momentum.rsi(df['close'], window=self.rsi_period)
        
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['adx'] = adx_ind.adx()
        
        # Use iloc[-2] (Previous Closed Candle) for confirmed signals
        # iloc[-1] is the current forming candle which changes every tick (Repainting risk)
        curr = df.iloc[-2]
        
        signal = "HOLD"
        reason = ""
        
        # Logic
        if curr['adx'] < self.adx_threshold:
            return {"order_type": "HOLD", "comment": f"Choppy (ADX {curr['adx']:.1f})"}
            
        if curr['sma_fast'] > curr['sma_slow']:
            if curr['rsi'] < 70:
                signal = "BUY"
                reason = "Uptrend + Momentum"
        
        elif curr['sma_fast'] < curr['sma_slow']:
            if curr['rsi'] > 30:
                signal = "SELL"
                reason = "Downtrend + Momentum"
                
        return {
            "order_type": signal,
            "comment": f"{reason} (Confirmed Candle | ADX:{curr['adx']:.1f})",
            "confidence": 0.8
        }

    def analyze_mtf(self, symbol: str, data_dict: dict) -> dict:
        """
        Analyzes a symbol across multiple timeframes.
        data_dict: {'H4': df, 'H1': df}
        """
        h4_df = data_dict.get('H4')
        h1_df = data_dict.get('H1')
        
        if h4_df is None or h1_df is None:
            return {"score": 0, "order_type": "HOLD", "comment": "Missing MTF data"}

        # --- CALCULATE FACTORS ---
        
        # 1. H4 Master Trend (30%)
        h4_sma_fast = ta.trend.sma_indicator(h4_df['close'], window=self.fast_period)
        h4_sma_slow = ta.trend.sma_indicator(h4_df['close'], window=self.slow_period)
        
        h4_up = h4_sma_fast.iloc[-2] > h4_sma_slow.iloc[-2]
        h4_down = h4_sma_fast.iloc[-2] < h4_sma_slow.iloc[-2]
        
        f_trend = 30 if (h4_up or h4_down) else 0 # Simple existence check
        
        # 2. H1 Signal (30%)
        h1_packet = self.get_signal(h1_df)
        h1_signal = h1_packet.get('order_type')
        f_signal = 30 if h1_signal in ["BUY", "SELL"] else 0
        
        # 3. Dynamic Power (ADX) (20%)
        h1_adx = ta.trend.ADXIndicator(h1_df['high'], h1_df['low'], h1_df['close']).adx().iloc[-2]
        f_power = 20 if h1_adx > self.adx_threshold else 0
        
        # 4. Momentum (RSI) (20%)
        h1_rsi = ta.momentum.RSIIndicator(h1_df['close']).rsi().iloc[-2]
        f_momentum = 0
        if h1_signal == "BUY" and h1_rsi > 50 and h1_rsi < 70: f_momentum = 20
        elif h1_signal == "SELL" and h1_rsi < 50 and h1_rsi > 30: f_momentum = 20

        # --- FINAL SCORE & ALIGNMENT ---
        total_score = f_trend + f_signal + f_power + f_momentum
        
        # 5. Volatility Context Filter (New: Proactive Assumption Checker)
        # We check if the current hour is historically a 'Death Zone' or if current speed is too low
        current_hour = h1_df.index[-1].hour
        is_death_zone = (current_hour == 23) # Hardcoded based on our Context Audit data for GOLD
        
        # 6. Exhaustion Guard (New: Quantile Analysis)
        from titan_system.research.auditor import TitanAuditor
        auditor = TitanAuditor(symbol)
        quantile_info = auditor.get_quantile_rank(h1_df)
        is_exhausted = quantile_info['percentile'] > 97 or quantile_info['percentile'] < 3
        
        if is_death_zone:
            total_score = total_score * 0.3 # Heavy penalty for trading in the Death Zone
            reason = "DEATH ZONE: Low Volume/Range detected historically (23:00 UTC)"
        elif is_exhausted:
            total_score = total_score * 0.4 # Penalty for buying the absolute top / selling bottom
            reason = f"EXHAUSTION GUARD: Move is in {quantile_info['percentile']:.1f}th percentile (Extreme)"
        elif h1_adx < 20:
             total_score = total_score * 0.7
             reason = f"Weak Trend Intensity (ADX: {h1_adx:.1f})"
        else:
            reason = h1_packet.get('comment', "Setup Active")

        # Alignment check: Is H1 signal actually in the direction of H4?
        alignment = False
        if h4_up and h1_signal == "BUY": alignment = True
        elif h4_down and h1_signal == "SELL": alignment = True
        
        if not alignment and h1_signal in ["BUY", "SELL"]:
            total_score = total_score * 0.5 # Penalty for counter-trend
            reason = f"Counter-Trend Conflict (H4 {'UP' if h4_up else 'DOWN'} vs H1 {h1_signal})"
        elif h1_signal == "HOLD":
            reason = "Waiting for H1 Setup"
        else:
            reason = h1_packet.get('comment', "Setup Active")

        # --- DECISION CHECKLIST ---
        checklist = [
            f"[{'X' if f_trend > 0 else ' '}] H4 Trend ({'UP' if h4_up else 'DOWN'})",
            f"[{'X' if f_signal > 0 else ' '}] H1 Trigger ({h1_signal})",
            f"[{'X' if f_power > 0 else ' '}] Trend Power (ADX: {h1_adx:.1f})",
            f"[{'X' if f_momentum > 0 else ' '}] Momentum (RSI: {h1_rsi:.1f})"
        ]

        return {
            "symbol": symbol,
            "score": total_score,
            "order_type": h1_signal if (alignment and total_score >= 80) else "HOLD",
            "comment": reason,
            "checklist": checklist,
            "meta": {
                "h4_bias": "UP" if h4_up else "DOWN",
                "h1_signal": h1_signal,
                "score_breakdown": {
                    "trend": f_trend,
                    "signal": f_signal,
                    "power": f_power,
                    "momentum": f_momentum
                }
            }
        }
