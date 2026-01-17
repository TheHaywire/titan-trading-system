"""
COMPLETE ENTRY SIGNAL GENERATOR
================================
Combines ALL features (basic + advanced) to generate:
1. Breakout entries
2. Pullback entries
3. Mean reversion entries
4. Scalping entries
5. Position sizing for each
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

from titan_system.features.quant_features import QuantFeatureEngine
from titan_system.features.advanced_features import AdvancedQuantEngine


@dataclass
class EntrySignal:
    """Trade entry signal with all details."""
    entry_type: str  # BREAKOUT, PULLBACK, REVERSION, SCALP
    direction: str   # LONG or SHORT
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size_multiplier: float
    reasoning: List[str]
    risk_reward: float


class UniversalEntryGenerator:
    """Generates ALL types of entry signals based on market conditions."""
    
    @staticmethod
    def analyze_market_state(basic_features: pd.Series, advanced_features: pd.Series) -> Dict:
        """Determine current market state."""
        state = {}
        
        # Trend state
        hurst = basic_features.get('hurst', 0.5)
        roc_20 = basic_features.get('roc_20', 0)
        kalman_trend = advanced_features.get('kalman_trend', basic_features.get('close', 0))
        close = basic_features.get('close', 0)
        
        if hurst > 0.55 and abs(roc_20) > 1:
            state['trend_state'] = 'TRENDING'
            state['trend_direction'] = 'UP' if roc_20 > 0 else 'DOWN'
        elif hurst < 0.45:
            state['trend_state'] = 'MEAN_REVERTING'
            state['trend_direction'] = 'NEUTRAL'
        else:
            state['trend_state'] = 'RANGING'
            state['trend_direction'] = 'UP' if close > kalman_trend else 'DOWN'
        
        # Volatility state
        vol_regime = basic_features.get('vol_regime', 'MEDIUM')
        state['volatility'] = vol_regime
        
        # Momentum state
        accel = basic_features.get('price_accel', 0)
        autocorr = basic_features.get('return_autocorr', 0)
        state['momentum_building'] = accel > 0
        state['momentum_persistent'] = autocorr > 0.2
        
        # Mean reversion state
        bbp = basic_features.get('bb_percentile', 0.5)
        zscore = basic_features.get('zscore_to_ma', 0)
        state['oversold'] = bbp < 0.2 or zscore < -1.5
        state['overbought'] = bbp > 0.8 or zscore > 1.5
        
        # HMM regime
        hmm = int(advanced_features.get('hmm_regime', 1))
        state['hmm_regime'] = hmm
        
        # Order flow
        vol_imb = advanced_features.get('volume_imbalance', 0.5)
        state['buying_pressure'] = vol_imb > 0.6
        state['selling_pressure'] = vol_imb < 0.4
        
        return state
    
    @staticmethod
    def generate_breakout_entry(state: Dict, basic: pd.Series, advanced: pd.Series, 
                               df: pd.DataFrame) -> EntrySignal:
        """
        BREAKOUT ENTRY
        When: Trending market + momentum building + breakout above resistance
        """
        close = basic['close']
        atr = basic.get('atr', close * 0.01)
        hurst = basic['hurst']
        roc_20 = basic['roc_20']
        accel = basic['price_accel']
        vol_regime = state['volatility']
        
        # Recent high/low
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        
        reasoning = []
        confidence = 0
        
        # Check conditions for LONG breakout
        if state['trend_state'] == 'TRENDING' and state['trend_direction'] == 'UP':
            if close >= recent_high * 0.999:  # At or near breakout
                confidence += 30
                reasoning.append(f"Price at 20-bar high (${recent_high:.2f})")
            
            if state['momentum_building']:
                confidence += 20
                reasoning.append(f"Momentum accelerating ({accel:+.2f})")
            
            if state['buying_pressure']:
                confidence += 20
                reasoning.append("Strong buying pressure")
            
            if hurst > 0.6:
                confidence += 15
                reasoning.append(f"Strong trend (Hurst={hurst:.2f})")
            
            if vol_regime != 'HIGH':
                confidence += 15
                reasoning.append(f"Volatility OK ({vol_regime})")
            
            if confidence >= 50:
                # Calculate entry parameters
                entry = recent_high + atr * 0.1  # Enter above high
                stop = recent_low - atr * 0.2
                tp1 = entry + (entry - stop) * 1.5
                tp2 = entry + (entry - stop) * 3.0
                
                size_mult = 1.0 if vol_regime == 'MEDIUM' else (0.75 if vol_regime == 'HIGH' else 1.25)
                
                return EntrySignal(
                    entry_type="BREAKOUT",
                    direction="LONG",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=size_mult,
                    reasoning=reasoning,
                    risk_reward=(tp2 - entry) / (entry - stop)
                )
        
        # Check SHORT breakout
        elif state['trend_state'] == 'TRENDING' and state['trend_direction'] == 'DOWN':
            if close <= recent_low * 1.001:
                confidence += 30
                reasoning.append(f"Price at 20-bar low (${recent_low:.2f})")
            
            if state['momentum_building']:
                confidence += 20
                reasoning.append(f"Downside acceleration ({accel:+.2f})")
            
            if state['selling_pressure']:
                confidence += 20
                reasoning.append("Strong selling pressure")
            
            if hurst > 0.6:
                confidence += 15
                reasoning.append(f"Strong trend (Hurst={hurst:.2f})")
            
            if vol_regime != 'HIGH':
                confidence += 15
                reasoning.append(f"Volatility OK ({vol_regime})")
            
            if confidence >= 50:
                entry = recent_low - atr * 0.1
                stop = recent_high + atr * 0.2
                tp1 = entry - (stop - entry) * 1.5
                tp2 = entry - (stop - entry) * 3.0
                
                size_mult = 1.0 if vol_regime == 'MEDIUM' else (0.75 if vol_regime == 'HIGH' else 1.25)
                
                return EntrySignal(
                    entry_type="BREAKOUT",
                    direction="SHORT",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=size_mult,
                    reasoning=reasoning,
                    risk_reward=(entry - tp2) / (stop - entry)
                )
        
        return None
    
    @staticmethod
    def generate_pullback_entry(state: Dict, basic: pd.Series, advanced: pd.Series,
                               df: pd.DataFrame) -> EntrySignal:
        """
        PULLBACK ENTRY
        When: Uptrend + price pulls back to Kalman trend or key MA
        """
        close = basic['close']
        atr = basic.get('atr', close * 0.01)
        kalman = advanced['kalman_trend']
        ema_50 = basic.get('ema_50', close)
        bbp = basic['bb_percentile']
        hurst = basic['hurst']
        
        reasoning = []
        confidence = 0
        
        # LONG pullback in uptrend
        if state['trend_direction'] == 'UP' and hurst > 0.5:
            # Price pulled back to support
            at_kalman = abs(close - kalman) / kalman < 0.01
            at_ema = abs(close - ema_50) / ema_50 < 0.01
            bb_low = bbp < 0.4
            
            if at_kalman or at_ema:
                confidence += 30
                reasoning.append(f"Pullback to support (Kalman ${kalman:.2f})")
            
            if bb_low:
                confidence += 15
                reasoning.append(f"BB percentile {bbp:.2f} - oversold in uptrend")
            
            if state['buying_pressure']:
                confidence += 25
                reasoning.append("Buying pressure appearing")
            
            if state['momentum_persistent']:
                confidence += 20
                reasoning.append("Uptrend still intact")
            
            if state['volatility'] == 'LOW':
                confidence += 10
                reasoning.append("Low volatility - good for pullback entries")
            
            if confidence >= 50:
                entry = close
                stop = kalman - atr * 1.0
                tp1 = entry + (entry - stop) * 2.0
                tp2 = entry + (entry - stop) * 4.0
                
                return EntrySignal(
                    entry_type="PULLBACK",
                    direction="LONG",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=1.0,
                    reasoning=reasoning,
                    risk_reward=(tp2 - entry) / (entry - stop)
                )
        
        # SHORT pullback in downtrend
        elif state['trend_direction'] == 'DOWN' and hurst > 0.5:
            at_kalman = abs(close - kalman) / kalman < 0.01
            at_ema = abs(close - ema_50) / ema_50 < 0.01
            bb_high = bbp > 0.6
            
            if at_kalman or at_ema:
                confidence += 30
                reasoning.append(f"Rally to resistance (Kalman ${kalman:.2f})")
            
            if bb_high:
                confidence += 15
                reasoning.append(f"BB percentile {bbp:.2f} - overbought in downtrend")
            
            if state['selling_pressure']:
                confidence += 25
                reasoning.append("Selling pressure resuming")
            
            if state['momentum_persistent']:
                confidence += 20
                reasoning.append("Downtrend still intact")
            
            if confidence >= 50:
                entry = close
                stop = kalman + atr * 1.0
                tp1 = entry - (stop - entry) * 2.0
                tp2 = entry - (stop - entry) * 4.0
                
                return EntrySignal(
                    entry_type="PULLBACK",
                    direction="SHORT",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=1.0,
                    reasoning=reasoning,
                    risk_reward=(entry - tp2) / (stop - entry)
                )
        
        return None
    
    @staticmethod
    def generate_reversion_entry(state: Dict, basic: pd.Series, advanced: pd.Series,
                                df: pd.DataFrame) -> EntrySignal:
        """
        MEAN REVERSION ENTRY
        When: Mean-reverting market + extreme BBP + VWAP deviation
        """
        close = basic['close']
        atr = basic.get('atr', close * 0.01)
        bbp = basic['bb_percentile']
        rsi_pct = basic['rsi_percentile']
        zscore = basic['zscore_to_ma']
        vwap_dev = advanced['vwap_deviation']
        hurst = basic['hurst']
        
        reasoning = []
        confidence = 0
        
        # LONG reversion (buy dips)
        if state['oversold'] or bbp < 0.15:
            confidence += 25
            reasoning.append(f"Oversold: BB={bbp:.2f}, Z={zscore:.2f}")
            
            if rsi_pct < 30:
                confidence += 20
                reasoning.append(f"RSI percentile {rsi_pct:.0f}th - historically low")
            
            if vwap_dev < -0.5:
                confidence += 20
                reasoning.append(f"Below VWAP by {abs(vwap_dev):.2f}% - magnet effect")
            
            if hurst < 0.5:
                confidence += 20
                reasoning.append(f"Mean-reverting environment (H={hurst:.2f})")
            
            if state['hmm_regime'] == 0:
                confidence += 15
                reasoning.append("HMM: Low vol reversion regime")
            
            if confidence >= 60:
                entry = close
                stop = close - atr * 0.75  # Tight stop for reversion
                tp1 = close + atr * 1.0  # Quick profit
                tp2 = close + atr * 1.5
                
                return EntrySignal(
                    entry_type="REVERSION",
                    direction="LONG",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=1.0,
                    reasoning=reasoning,
                    risk_reward=(tp2 - entry) / (entry - stop)
                )
        
        # SHORT reversion (sell rallies)
        elif state['overbought'] or bbp > 0.85:
            confidence += 25
            reasoning.append(f"Overbought: BB={bbp:.2f}, Z={zscore:.2f}")
            
            if rsi_pct > 70:
                confidence += 20
                reasoning.append(f"RSI percentile {rsi_pct:.0f}th - historically high")
            
            if vwap_dev > 0.5:
                confidence += 20
                reasoning.append(f"Above VWAP by {vwap_dev:.2f}% - pullback likely")
            
            if hurst < 0.5:
                confidence += 20
                reasoning.append(f"Mean-reverting environment (H={hurst:.2f})")
            
            if state['hmm_regime'] == 0:
                confidence += 15
                reasoning.append("HMM: Low vol reversion regime")
            
            if confidence >= 60:
                entry = close
                stop = close + atr * 0.75
                tp1 = close - atr * 1.0
                tp2 = close - atr * 1.5
                
                return EntrySignal(
                    entry_type="REVERSION",
                    direction="SHORT",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=1.0,
                    reasoning=reasoning,
                    risk_reward=(entry - tp2) / (stop - entry)
                )
        
        return None
    
    @staticmethod
    def generate_scalp_entry(state: Dict, basic: pd.Series, advanced: pd.Series,
                            df: pd.DataFrame) -> EntrySignal:
        """
        SCALP ENTRY
        When: VWAP deviation + volume imbalance + quick profits
        """
        close = basic['close']
        atr = basic.get('atr', close * 0.01)
        vwap_dev = advanced['vwap_deviation']
        vol_imb = advanced['volume_imbalance']
        
        reasoning = []
        confidence = 0
        
        # LONG scalp
        if vwap_dev < -0.3 and vol_imb > 0.55:
            confidence += 40
            reasoning.append(f"Below VWAP ({vwap_dev:.2f}%), buying appearing")
            
            if state['volatility'] == 'LOW':
                confidence += 30
                reasoning.append("Low vol - good for scalping")
            
            if state['buying_pressure']:
                confidence += 30
                reasoning.append(f"Strong buying (imbalance {vol_imb:.2f})")
            
            if confidence >= 70:
                entry = close
                stop = close - atr * 0.4  # Very tight stop
                tp1 = close + atr * 0.5   # Quick profit
                tp2 = close + atr * 0.8
                
                return EntrySignal(
                    entry_type="SCALP",
                    direction="LONG",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=0.75,  # Smaller size for scalping
                    reasoning=reasoning,
                    risk_reward=(tp2 - entry) / (entry - stop)
                )
        
        # SHORT scalp
        elif vwap_dev > 0.3 and vol_imb < 0.45:
            confidence += 40
            reasoning.append(f"Above VWAP ({vwap_dev:.2f}%), selling appearing")
            
            if state['volatility'] == 'LOW':
                confidence += 30
                reasoning.append("Low vol - good for scalping")
            
            if state['selling_pressure']:
                confidence += 30
                reasoning.append(f"Strong selling (imbalance {vol_imb:.2f})")
            
            if confidence >= 70:
                entry = close
                stop = close + atr * 0.4
                tp1 = close - atr * 0.5
                tp2 = close - atr * 0.8
                
                return EntrySignal(
                    entry_type="SCALP",
                    direction="SHORT",
                    confidence=confidence,
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    position_size_multiplier=0.75,
                    reasoning=reasoning,
                    risk_reward=(entry - tp2) / (stop - entry)
                )
        
        return None
    
    @classmethod
    def generate_all_entries(cls, df: pd.DataFrame, basic_features: pd.DataFrame,
                            advanced_features: pd.DataFrame) -> List[EntrySignal]:
        """Generate ALL possible entry signals."""
        basic_latest = basic_features.iloc[-1]
        advanced_latest = advanced_features.iloc[-1]
        
        # Analyze market state
        state = cls.analyze_market_state(basic_latest, advanced_latest)
        
        signals = []
        
        # Try each entry type
        breakout = cls.generate_breakout_entry(state, basic_latest, advanced_latest, df)
        if breakout:
            signals.append(breakout)
        
        pullback = cls.generate_pullback_entry(state, basic_latest, advanced_latest, df)
        if pullback:
            signals.append(pullback)
        
        reversion = cls.generate_reversion_entry(state, basic_latest, advanced_latest, df)
        if reversion:
            signals.append(reversion)
        
        scalp = cls.generate_scalp_entry(state, basic_latest, advanced_latest, df)
        if scalp:
            signals.append(scalp)
        
        # Sort by confidence
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals, state


def display_entry_signals(symbol: str, signals: List[EntrySignal], state: Dict):
    """Display all entry signals beautifully."""
    print("\n" + "="*80)
    print(f"COMPLETE ENTRY ANALYSIS: {symbol}")
    print("="*80)
    
    print(f"\nMARKET STATE:")
    print(f"  Trend: {state['trend_state']} ({state['trend_direction']})")
    print(f"  Volatility: {state['volatility']}")
    print(f"  Momentum Building: {'Yes' if state['momentum_building'] else 'No'}")
    print(f"  Buying Pressure: {'Yes' if state['buying_pressure'] else 'No'}")
    print(f"  Selling Pressure: {'Yes' if state['selling_pressure'] else 'No'}")
    
    if not signals:
        print(f"\n  >> NO QUALITY SETUPS AVAILABLE <<")
        print(f"  Wait for better conditions.")
        return
    
    print(f"\n{'='*80}")
    print(f"AVAILABLE ENTRY SETUPS ({len(signals)} found)")
    print(f"{'='*80}")
    
    for i, sig in enumerate(signals, 1):
        print(f"\n[{i}] {sig.entry_type} {sig.direction} - Confidence: {sig.confidence:.0f}/100")
        print(f"{'='*80}")
        
        print(f"Entry:  ${sig.entry_price:.2f}")
        print(f"Stop:   ${sig.stop_loss:.2f}")
        print(f"TP1:    ${sig.take_profit_1:.2f}  (50% exit)")
        print(f"TP2:    ${sig.take_profit_2:.2f}  (final exit)")
        print(f"R:R:    1:{sig.risk_reward:.1f}")
        print(f"Size:   {sig.position_size_multiplier:.2f}x base")
        
        print(f"\nReasoning:")
        for reason in sig.reasoning:
            print(f"  ✓ {reason}")
        
        # Trade management guidance
        print(f"\nTrade Management:")
        if sig.entry_type == "BREAKOUT":
            print(f"  1. Enter on breakout confirmation")
            print(f"  2. Take 50% at TP1 ({sig.risk_reward/2:.1f}R)")
            print(f"  3. Trail stop to breakeven")
            print(f"  4. Trail remaining 50% with Kalman line")
        elif sig.entry_type == "PULLBACK":
            print(f"  1. Enter at current price or better")
            print(f"  2. Take 50% at TP1 (2R), move stop to BE")
            print(f"  3. Let remaining run to TP2 (4R)")
        elif sig.entry_type == "REVERSION":
            print(f"  1. Enter immediately")
            print(f"  2. Take 75% at TP1 - QUICK profits")
            print(f"  3. Let 25% run to TP2 or close on reversal")
        elif sig.entry_type == "SCALP":
            print(f"  1. Enter immediately, tight stop")
            print(f"  2. Take 100% at TP1 - don't be greedy")


# MAIN EXECUTION
if __name__ == "__main__":
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 init failed")
        exit()
    
    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 500)
    mt5.shutdown()
    
    if rates is None:
        print("Data fetch failed")
        exit()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    print(f"Analyzing {symbol} H1...")
    print(f"Latest: {df['time'].iloc[-1]}")
    print(f"Close: ${df['close'].iloc[-1]:.2f}")
    
    # Compute features
    basic_features = QuantFeatureEngine.compute_all(df)
    
    returns = df['close'].pct_change()
    universe_returns = {'EUR': returns, 'GBP': returns}
    
    advanced_features = AdvancedQuantEngine.compute_all_advanced(
        df,
        universe_returns=universe_returns,
        market_returns=returns
    )
    
    # Generate entries
    signals, state = UniversalEntryGenerator.generate_all_entries(
        df, basic_features, advanced_features
    )
    
    # Display
    display_entry_signals(symbol, signals, state)
    
    print(f"\n" + "="*80)
    print(f"Use the HIGHEST confidence signal for your next trade!")
    print(f"="*80)
