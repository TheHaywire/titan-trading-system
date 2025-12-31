"""
Regime Classification & Entry Engine
Unifies TE-1, VE-1, ME-1, and LE-1 to output actionable setups.
"""

import pandas as pd
from titan_system.smc.trend_engine import TrendEngine
from titan_system.smc.vwap_engine import VWAPEngine
from titan_system.smc.market_structure import MarketStructure
from titan_system.smc.liquidity import LiquidityEngine
from titan_system.smc.fvg import FVGDetector
from titan_system.smc.momentum_engine import MomentumEngine
from titan_system.smc.volatility_engine import VolatilityEngine

class InstitutionalEngine:
    
    def __init__(self):
        self.trend_engine = TrendEngine()
        self.vwap_engine = VWAPEngine()
        self.ms_engine = MarketStructure()
        self.liq_engine = LiquidityEngine()
        self.fvg_engine = FVGDetector()
        self.mom_engine = MomentumEngine()
        self.vol_engine = VolatilityEngine()
        
    def analyze_symbol(self, df: pd.DataFrame, symbol: str) -> dict:
        """
        Run the full Institutional Classification Stack
        """
        # 1. Trend Analysis (TE-1)
        ema_df = self.trend_engine.calculate_emas(df['close'])
        
        # Volatility Analysis (VE-1)
        vol_data = self.vol_engine.analyze(df)
        atr_expanding = vol_data['regime'] == "HIGH_VOL_EXPANSION"
        
        # Market Structure (MS)
        ms_data = self.ms_engine.analyze(df)
        structure_trend = ms_data['trend'].upper()
        
        trend_data = self.trend_engine.calculate_tss(
            df['close'], ema_df, structure_trend, atr_expanding
        )
        
        # 2. VWAP Analysis (VE-2)
        vwap_data = self.vwap_engine.analyze(df)
        
        # 3. Liquidity (LE-1)
        liq_data = self.liq_engine.analyze(df, symbol)
        
        # 4. FVG Analysis
        fvg_data = self.fvg_engine.analyze(df)
        
        # 5. Momentum Analysis (ME-1)
        mom_data = self.mom_engine.analyze(df)
        
        # 6. Regime Determinator
        regime = self._determine_regime(trend_data, vwap_data, vol_data)
        
        # 7. Setup Detection
        setup = self._detect_setup(regime, trend_data, liq_data, fvg_data, mom_data, vol_data)
        
        return {
            'regime': regime,
            'trend': trend_data,
            'vwap': vwap_data,
            'liquidity': liq_data,
            'fvg': fvg_data,
            'momentum': mom_data,
            'volatility': vol_data,
            'setup': setup
        }
        
    def _determine_regime(self, trend: dict, vwap: dict, vol: dict) -> str:
        """Classify Market Regime"""
        tss = trend['tss']
        vol_regime = vol['regime']
        
        if vol_regime == "LOW_VOL_COMPRESSION":
             return "SQUEEZE_PRE_BREAKOUT"
        
        if tss >= 4:
            return "TREND_STRONG"
        elif tss == 3:
            return "TREND_WEAK"
        elif tss <= 2:
            # Check for Mean Reversion vs Reversal
            if "EXTENSION" in vwap['regime']:
                return "MEAN_REVERSION_POSSIBLE"
            else:
                return "CHOPPY_RANGE"
        return "UNDEFINED"

    def _detect_setup(self, regime: str, trend: dict, liq: dict, fvg: dict, mom: dict, vol: dict) -> list:
        """Detect valid institutional setups"""
        setups = []
        
        # ---------------------------------------------------------
        # 1. TCB (Trend Continuation Break) - The #1 Institutional Setup
        # Requires: Strong Trend, RSI aligned, Wick Rejection / FVG Retest
        # ---------------------------------------------------------
        if "TREND" in regime and trend['tss'] >= 4:
            if trend['bias'] == "BULLISH":
                 if mom['rsi'] > 55: # ME-1 Rule
                     # Check for FVG Retest (Type C Entry)
                     if fvg['retest_opportunities']:
                         for ret in fvg['retest_opportunities']:
                             if ret['fvg']['type'] == 'bullish_fvg':
                                 setups.append({
                                     'name': 'TCB_BULLISH',
                                     'trigger': f"FVG Retest @ {ret['entry_price']:.2f}",
                                     'stop': ret['fvg']['bottom'],
                                     'target': ret['entry_price'] + (ret['entry_price']-ret['fvg']['bottom'])*2
                                 })
        
            elif trend['bias'] == "BEARISH":
                if mom['rsi'] < 45: # ME-1 Rule
                    if fvg['retest_opportunities']:
                         for ret in fvg['retest_opportunities']:
                             if ret['fvg']['type'] == 'bearish_fvg':
                                 setups.append({
                                     'name': 'TCB_BEARISH',
                                     'trigger': f"FVG Retest @ {ret['entry_price']:.2f}",
                                     'stop': ret['fvg']['top'],
                                     'target': ret['entry_price'] - (ret['fvg']['top']-ret['entry_price'])*2
                                 })

        # ---------------------------------------------------------
        # 2. LSR (Liquidity Sweep Reversal) - High Conviction Reversal
        # Requires: External Sweep, Divergence (Optional), Displacement
        # ---------------------------------------------------------
        if liq['sweeps']:
            for sweep in liq['sweeps']:
                if sweep['sweep_type'] == 'bearish_liquidity_grab':
                    # We have a sweep of a Low. This is potentially BULLISH reversal.
                    # Wait, "bearish_liquidity_grab" in my logic was:
                    # "Bearish sweep: low breaks level, close above it" -> This is BULLISH REVERSAL pattern.
                    # Let's fix naming to avoid confusion. Logic: Grabbed liquidity at Low -> Go Long.
                    
                    setups.append({
                        'name': 'LSR_BULLISH',
                        'trigger': f"Sweep of Low @ {sweep['level']:.2f}",
                        'confirmation_needed': 'Displacement + FVG + RSI Divergence',
                        'stop': sweep['level']
                    })
                    
                elif sweep['sweep_type'] == 'bullish_liquidity_grab':
                    # Grabbed High -> Go Short
                    setups.append({
                        'name': 'LSR_BEARISH',
                        'trigger': f"Sweep of High @ {sweep['level']:.2f}",
                        'confirmation_needed': 'Displacement + FVG + RSI Divergence',
                        'stop': sweep['level']
                    })

        # ---------------------------------------------------------
        # 3. MRC (Mean Reversion Collapse)
        # Requires: Low Volatility, VWAP Extension
        # ---------------------------------------------------------
        if regime == "MEAN_REVERSION_POSSIBLE" and vol['regime'] in ["LOW_VOL_COMPRESSION", "NORMAL_VOLATILITY"]:
             # Check VWAP Extension
             if "BULLISH_EXTENSION" in vwap['regime'] and mom['rsi'] > 70:
                 setups.append({
                     'name': 'MRC_SHORT',
                     'trigger': 'VWAP +1sd Extension + Overbought',
                     'target': vwap['vwap']
                 })
             elif "BEARISH_EXTENSION" in vwap['regime'] and mom['rsi'] < 30:
                 setups.append({
                     'name': 'MRC_LONG',
                     'trigger': 'VWAP -1sd Extension + Oversold',
                     'target': vwap['vwap']
                 })

        return setups
