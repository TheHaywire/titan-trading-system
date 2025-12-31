import pandas as pd
import MetaTrader5 as mt5
import logging
import numpy as np
from typing import Dict, Any, Optional
from titan_system.strategies.base import BaseStrategy
from titan_system.smc.institutional_engine import InstitutionalEngine

logger = logging.getLogger("Titan.Strategy.InstitutionalGold")

class InstitutionalGoldStrategy(BaseStrategy):
    """
    The Crown Jewel Strategy for XAUUSD (GOLD).
    
    Architecture:
    1. Strategic Layer (H4): Determines Directional Bias.
    2. Tactical Layer (H1): Identifies Liquidity Pools & Zones.
    3. Execution Layer (M15): Triggers entries based on Setup + Momentum.
    
    This strategy encapsulates the logic previously found in 'titan_master_loop.py'
    but integrates it safely into the Titan Core Engine.
    """
    
    def __init__(self, config: Dict):
        super().__init__("InstitutionalGold", config)
        self.engine = InstitutionalEngine()
        self.execution_client = config.get('execution_client') # Must be injected
        
        # Cache for Higher Timeframes to avoid spamming API
        self.h4_cache = {'time': 0, 'bias': 'NEUTRAL', 'data': None}
        self.h1_cache = {'time': 0, 'zones': [], 'data': None}
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main Analysis Loop.
        'data' provided by Engine is typically H1. 
        We will fetch H4 and M15 manually if needed.
        """
        if symbol != "GOLD" and symbol != "XAUUSD":
             return {"signal": "HOLD", "reason": "Strategy only for GOLD"}
             
        # 1. Update Strategic Bias (H4) - Every 4 hours or on init
        self._update_strategic_layer(symbol)
        
        # 2. Update Tactical Zones (H1) - Every hour
        self._update_tactical_layer(symbol)
        
        # 3. Execution Logic (M15) - Runs every cycle (M1/M5)
        return self._run_execution_layer(symbol)

    def _update_strategic_layer(self, symbol):
        """Fetches H4 data to determine directional bias."""
        try:
            # Check if we need to update (simple time check or if cache empty)
            # In a real system, we'd check candle timestamps. For now, just run it.
            # Optimization: Only run expensive fetch if we strictly need to.
            
            if not self.execution_client:
                logger.error("Execution Client not injected into Strategy!")
                return

            rates = self.execution_client.get_data(symbol, mt5.TIMEFRAME_H4, 200)
            if rates is not None:
                res = self.engine.analyze_symbol(rates, symbol)
                self.h4_cache['bias'] = res['trend']['bias']
                self.h4_cache['regime'] = res['regime']
                # logger.info(f"[Institutional] H4 Bias: {self.h4_cache['bias']}")
        except Exception as e:
            logger.error(f"H4 Update Failed: {e}")

    def _update_tactical_layer(self, symbol):
        """Fetches H1 data to find liquidity zones."""
        try:
            rates = self.execution_client.get_data(symbol, mt5.TIMEFRAME_H1, 200)
            if rates is not None:
                res = self.engine.analyze_symbol(rates, symbol)
                
                # Extract Zones
                zones = []
                if res['liquidity']['sessions']['prev_day_high']:
                    zones.append(('RESISTANCE', res['liquidity']['sessions']['prev_day_high']))
                if res['liquidity']['sessions']['prev_day_low']:
                    zones.append(('SUPPORT', res['liquidity']['sessions']['prev_day_low']))
                
                self.h1_cache['zones'] = zones
        except Exception as e:
            logger.error(f"H1 Update Failed: {e}")

    def _run_execution_layer(self, symbol) -> Dict[str, Any]:
        """Fetches M15 data to identify immediate triggers aligned with Bias."""
        try:
            # We use M15 for the trigger similar to the original script
            rates = self.execution_client.get_data(symbol, mt5.TIMEFRAME_M15, 100)
            if rates is None: 
                return {"signal": "HOLD", "reason": "No M15 Data"}
                
            res = self.engine.analyze_symbol(rates, symbol)
            
            current_price = rates['close'].iloc[-1]
            mom = res['momentum']
            bias = self.h4_cache['bias']
            
            signal = "HOLD"
            reason = "Wait"
            confidence = 0.0
            
            # --- LOGIC PORTED FROM TITAN MASTER LOOP ---
            
            # 1. Proximity Check (Are we near a H1 Zone?)
            near_zone = False
            active_zone_price = 0
            for z_type, level in self.h1_cache['zones']:
                if abs(current_price - level) < 2.0: # 20 pips/points tolerance
                    near_zone = True
                    active_zone_price = level

            # 3. AI / Machine Learning Layer
            # Calculate features for AI (Last 200 bars processed in RAM)
            # Need strict alignment with training features!
            
            # Convert MT5 Rates to Polars for Feature Engine
            pdf = pd.DataFrame(rates)
            pdf['time'] = pd.to_datetime(pdf['time'], unit='s')
            import polars as pl
            # Clean up logic
            pl_df = pl.from_pandas(pdf)
            
            # 1. Ensure Model is Loaded to check input size
            if not hasattr(self, 'ai_model') or self.ai_model is None:
                 from titan_system.core.neural_strategy import NeuralStrategy
                 import os
                 model_path = "titan_system/ai/models/best_brain.json"
                 if os.path.exists(model_path):
                     self.ai_model = NeuralStrategy.load(model_path)
                     logger.info(f"🧠 AI Brain Loaded (Inputs: {self.ai_model.input_size})")
                 else:
                     self.ai_model = None

            # 2. Match Feature Engine to Model Version
            f_version = "v1"
            if self.ai_model and self.ai_model.input_size > 4:
                f_version = "v2"
                
            from titan_system.ai.features import compute_features
            _, feature_matrix = compute_features(pl_df, version=f_version)
            
            if self.ai_model and feature_matrix.shape[0] > 0:
                # Get the latest feature row
                latest_features = feature_matrix[-1]
                
                # Get Prediction
                probs = self.ai_model.forward(latest_features) # Returns [Buy, Sell, Hold] probs
                    ai_action = np.argmax(probs)
                    ai_conf = probs[ai_action]
                    
                    # LOG the AI "Thinking"
                    logger.info(f"🧠 AI Prediction: {['BUY', 'SELL', 'HOLD'][ai_action]} ({ai_conf*100:.1f}%)")
                    
                    # 4. Hybrid Logic (AI + Rule Base)
                    # Implementation: Use AI as the Trigger if High Confidence (>70%)
                    if ai_conf > 0.7:
                         if ai_action == 0: # BUY
                             signal = "BUY"
                             reason = f"AI Alpha Trigger (Conf: {ai_conf:.2f})"
                             confidence = ai_conf
                         elif ai_action == 1: # SELL
                             signal = "SELL"
                             reason = f"AI Alpha Trigger (Conf: {ai_conf:.2f})"
                             confidence = ai_conf
            
            # Fallback to Legacy Logic if AI is unsure (HOLD) or not loaded
            if signal == "HOLD":
                # ... (Existing RSI Logic below) ...
                if (bias == "BEARISH" or bias == "NEUTRAL") and mom['rsi'] > 75:
                     signal = "SELL"
                     reason = f"Bearish Bias + RSI Overbought ({mom['rsi']:.1f})"
                     confidence = 0.85
                
                elif (bias == "BULLISH" or bias == "NEUTRAL") and mom['rsi'] < 25:
                     signal = "BUY"
                     reason = f"Bullish Bias + RSI Oversold ({mom['rsi']:.1f})"
                     confidence = 0.85
            
            # 3. Liquidity Sweep Logic (LSR) - High Quality
            # If we swept a PDH/PDL and closed back inside
            if res['setup']:
                for s in res['setup']:
                    if s['name'] == 'LSR_BEARISH' and (bias == 'BEARISH' or bias == 'NEUTRAL'):
                        signal = "SELL"
                        reason = "Liquidity Sweep Reversal (Bearish)"
                        confidence = 0.95
                    elif s['name'] == 'LSR_BULLISH' and (bias == 'BULLISH' or bias == 'NEUTRAL'):
                        signal = "BUY"
                        reason = "Liquidity Sweep Reversal (Bullish)"
                        confidence = 0.95
            
            return {
                "signal": signal,
                "reason": reason,
                "confidence": confidence,
                "metrics": {
                    "rsi": round(mom['rsi'], 2), 
                    "bias": bias,
                    "zones": len(self.h1_cache['zones'])
                }
            }

        except Exception as e:
            logger.error(f"Execution Logic Failed: {e}")
            return {"signal": "HOLD", "reason": "Error"}
