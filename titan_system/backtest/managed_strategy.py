import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy

class ManagedStrategy(BaseStrategy):
    """
    A wrapper strategy that adds Tiered De-Risking logic to any base strategy.
    
    Tiers:
    - Tier 1: Profit > 0.5R -> Move SL to 50% of initial risk.
    - Tier 2: Profit > 0.8R -> Move SL to Entry + Buffer.
    - Tier 3: Profit > 1.2R -> Trail SL (ATR-based).
    """
    
    def __init__(self, base_strategy: BaseStrategy):
        super().__init__(name=f"Managed_{base_strategy.name}", params=base_strategy.params)
        self.base_strategy = base_strategy
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.base_strategy.calculate_indicators(df)
        
    def analyze(self, df: pd.DataFrame) -> dict:
        signal = self.base_strategy.analyze(df)
        if signal:
            # Store initial risk in signal to be put in position dict
            entry = signal.get('entry_price', df.iloc[-1]['close'])
            sl = signal.get('stop_loss')
            if sl:
                signal['initial_risk'] = abs(entry - sl)
                signal['max_favorable_pips'] = 0.0
            return signal
        return None
        
    def check_exit(self, df: pd.DataFrame, position: dict) -> str:
        current = df.iloc[-1]
        entry_price = position['entry_price']
        direction = position['direction']
        
        # Calculate current pips and potential MFE
        if direction == 'BUY':
            current_pips = current['close'] - entry_price
            high_pips = current['high'] - entry_price
            position['max_favorable_pips'] = max(position.get('max_favorable_pips', 0), high_pips)
        else:
            current_pips = entry_price - current['close']
            low_pips = entry_price - current['low']
            position['max_favorable_pips'] = max(position.get('max_favorable_pips', 0), low_pips)
            
        # Initial Risk (distance to original SL)
        # We need to ensure engine stores initial_risk when opening position
        # If not, we calculate it from original sl if available
        if 'initial_risk' not in position:
            position['initial_risk'] = abs(entry_price - position['sl']) if position['sl'] else 0.001
            
        initial_risk = position['initial_risk']
        mfe = position['max_favorable_pips']
        r_multiple = mfe / initial_risk if initial_risk > 0 else 0
        
        # --- TIERED DE-RISKING LOGIC ---
        old_sl = position['sl']
        
        # Tier 3: Trail at 1.2R
        if r_multiple >= 1.2:
            atr = current.get('atr', initial_risk / 2)
            if direction == 'BUY':
                trail_sl = current['close'] - (atr * 1.5)
                if trail_sl > position['sl']:
                    position['sl'] = trail_sl
            else:
                trail_sl = current['close'] + (atr * 1.5)
                if trail_sl < position['sl'] or position['sl'] == 0:
                    position['sl'] = trail_sl
                    
        # Tier 2: Break-Even at 0.8R
        elif r_multiple >= 0.8:
            buffer = 5 * 0.0001 # 5 pips
            if direction == 'BUY':
                be_sl = entry_price + buffer
                if be_sl > position['sl']:
                    position['sl'] = be_sl
            else:
                be_sl = entry_price - buffer
                if be_sl < position['sl'] or position['sl'] == 0:
                    position['sl'] = be_sl
                    
        # Tier 1: Reduce Risk at 0.5R
        elif r_multiple >= 0.5:
            if direction == 'BUY':
                reduced_sl = entry_price - (initial_risk * 0.5)
                if reduced_sl > position['sl']:
                    position['sl'] = reduced_sl
            else:
                reduced_sl = entry_price + (initial_risk * 0.5)
                if reduced_sl < position['sl'] or position['sl'] == 0:
                    position['sl'] = reduced_sl

        # Now check if we hit the (potentially updated) SL/TP
        return self.base_strategy.check_exit(df, position)
