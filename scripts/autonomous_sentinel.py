"""
Titan Autonomous Sentinel
=========================
The core orchestrator for fully autonomous trading. 
Implements the multi-layered "Intelligence Funnel" designed by 
the Strategy Council.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.comprehensive_intel import ComprehensiveIntel
from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.pattern_intelligence import PatternMiner
from titan_system.core.news_intelligence import NewsIntelligence
from titan_system.core.alpha_feedback import AlphaFeedback
from titan_system.core.execution import MT5Execution
from titan_system.core.feature_engine import FeatureEngine
from titan_system.core.risk_manager import RiskManager
from titan_system.core import gemini_usage as usage
from scripts import ai_professional_analyst as ai_analyst

# Configuration
SYMBOLS_TO_TRACK = ["GOLD", "BTCUSD", "US100Cash", "US30Cash", "EURUSD", "GBPUSD"]
SCAN_INTERVAL_MINUTES = 15
MIN_ALPHA_EFFICIENCY = 4.0   
MIN_CONFIDENCE = 0.70        
AUTO_EXECUTE = True          
RISK_PER_TRADE = 1.0         # 1.0% risk per unit

class MockConfig:
    def __init__(self):
        self.mt5_login = None
        self.mt5_password = None
        self.mt5_server = None
        self.MAX_SLIPPAGE_POINTS = 20

class AutonomousSentinel:
    """Orchestrates the autonomous trading funnel."""
    
    def __init__(self):
        self.intel = ComprehensiveIntel()
        self.news = NewsIntelligence()
        self.feedback = AlphaFeedback()
        self.execution = MT5Execution(MockConfig())
        self.execution.connect()
        self.risk = RiskManager(self.execution)
        print("🛡️ Titan Autonomous Sentinel Initialized")

    def run_funnel(self):
        """Execute one full scan of all symbols through the intelligence funnel."""
        if self.risk.is_circuit_breaker_tripped():
            print("🛑 TRADING HALTED: Daily Circuit Breaker is ACTIVE.")
            return

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Starting Autonomous Scan...")
        
        # Ensure MT5 is connected
        if not self.execution.connected:
            self.execution.connect()
        
        # Refresh news once per scan
        print("  → Refreshing News Intelligence...")
        self.news.refresh_all()
        
        candidates = []
        
        for symbol in SYMBOLS_TO_TRACK:
            print(f"\n  📡 Analyzing {symbol}...")
            
            # --- LAYER 1 & 2: Market Property & Regime Filter ---
            try:
                detector = RegimeDetector(symbol)
                regime_data = detector.detect_regime()
                
                regime = regime_data['regime']
                alpha = regime_data['institutional']['alpha_efficiency']
                
                print(f"    - Regime: {regime} (Conf: {regime_data['confidence']})")
                print(f"    - Alpha Efficiency: {alpha}x")

                # --- LAYER 2.5: Deep Pattern Identification ---
                df_h1 = detector.get_market_data(count=300) # Increased for feature calculation
                if df_h1 is None or len(df_h1) < 100:
                    print(f"    ❌ REJECTED: Insufficient historical data ({len(df_h1) if df_h1 is not None else 0} bars)")
                    continue
                    
                try:
                    miner = PatternMiner(df_h1)
                    patterns = miner.get_all_patterns()
                except Exception as pe:
                    print(f"    ⚠️ PatternMiner Error: {pe}")
                    patterns = {"liquidity": {"pattern": "NONE"}, "physics": {"rejection": "NONE"}}

                try:
                    # --- NEW: Institutional Feature Engine ---
                    # Fetch live metadata for the engine
                    s_info = mt5.symbol_info(symbol)
                    spread = s_info.spread if s_info else 0
                    
                    news_check = self.news.pre_trade_news_check(symbol)
                    news_min = news_check.get('minutes_to_event', 999)
                        
                    engine = FeatureEngine(df_h1)
                    
                    # --- NEW: Institutional Macro Layer ---
                    # Correlate with S&P 500 (Risk Sentiment) and EURUSD (Dollar Proxy)
                    # --- NEW: Institutional Macro Layer & MTF Hologram ---
                    # Correlate with S&P 500 (Risk Sentiment) and EURUSD (Dollar Proxy)
                    sp500_df = detector.get_market_data(symbol="US500Cash", count=100)
                    eurusd_df = detector.get_market_data(symbol="EURUSD", count=100)
                    
                    # MTF Holographic Scan (M15, H1, H4)
                    quant_features = {}
                    timeframes = {
                        "m15": mt5.TIMEFRAME_M15,
                        "h1": mt5.TIMEFRAME_H1,
                        "h4": mt5.TIMEFRAME_H4
                    }
                    
                    for tf_name, tf_const in timeframes.items():
                        # Fetch data for this timeframe
                        df_tf = detector.get_market_data(timeframe=tf_const, count=300)
                        if df_tf is None or len(df_tf) < 100:
                            continue
                            
                        # Run Engine
                        eng = FeatureEngine(df_tf)
                        eng.add_macro_correlation(sp500_df, "sp500") # Add macro to all TFs
                        eng.add_macro_correlation(eurusd_df, "dxy")
                        
                        lev_feats = eng.get_latest_features(symbol=symbol, spread_points=spread, news_minutes=news_min)
                        
                        # Prefix keys (e.g. 'h4_hurst')
                        for k, v in lev_feats.items():
                            if k in ["spread_points", "news_proximity", "open_positions"]: 
                                quant_features[k] = v # Keep globals as is
                            else:
                                quant_features[f"{tf_name}_{k}"] = v
                                
                    # Set primary H1 features as 'baseline' (no prefix) for compatibility if needed, 
                    # or just rely on explicit prefixes. Let's keep H1 as baseline too for legacy checks.
                    if "h1_hurst" in quant_features:
                         quant_features["hurst"] = quant_features["h1_hurst"] # For scaling logic compat
                    
                except Exception as fe:
                    print(f"    ⚠️ FeatureEngine Error: {fe}")
                    quant_features = {}
                
                liquidity = patterns.get('liquidity', {}).get('pattern', 'NONE')
                physics = patterns.get('physics', {}).get('rejection', 'NONE')
                
                if liquidity != "NONE":
                    print(f"    🌟 PATTERN DETECTED: {liquidity}")
                
                print(f"    - Momentum (ROC20): {quant_features.get('roc_20', 0)}")
                print(f"    - Volatility (Z-Score): {quant_features.get('vol_z', 0)}")
                
                if alpha < MIN_ALPHA_EFFICIENCY:
                    reason = f"Low Alpha Efficiency ({alpha}x < {MIN_ALPHA_EFFICIENCY}x)"
                    print(f"    ❌ REJECTED: {reason}")
                    self.feedback.log_decision({
                        "symbol": symbol, "decision": "NO", "model": "SENTINEL_L1",
                        "regime": regime, "confidence": regime_data['confidence'],
                        "reasoning": reason, "alpha_score": alpha, 
                        "market_data": {**regime_data, "patterns": patterns}
                    })
                    continue
                    
                if "NEUTRAL" in regime or "UNKNOWN" in regime:
                    reason = "Weak Market Regime"
                    print(f"    ❌ REJECTED: {reason}")
                    self.feedback.log_decision({
                        "symbol": symbol, "decision": "NO", "model": "SENTINEL_L2",
                        "regime": regime, "confidence": regime_data['confidence'],
                        "reasoning": reason, "alpha_score": alpha, 
                        "market_data": {**regime_data, "patterns": patterns}
                    })
                    continue
                
                # --- LAYER 3: News Sentiment Alignment ---
                news_bias = self.news.get_symbol_bias_from_news(symbol)
                bias = news_bias['bias']
                
                print(f"    - News Bias: {bias} ({news_bias['confidence']}% confidence)")
                
                # Deterministic Alignment Rules
                aligned = False
                if "BULLISH" in regime and bias == "BULLISH": aligned = True
                if "BEARISH" in regime and bias == "BEARISH": aligned = True
                if bias == "MIXED" or bias == "NEUTRAL": aligned = False # Strict in news
                
                if not aligned:
                    reason = f"News/Regime Mismatch ({bias} vs {regime})"
                    print(f"    ❌ REJECTED: {reason}")
                    self.feedback.log_decision({
                        "symbol": symbol, "decision": "NO", "model": "SENTINEL_L3",
                        "regime": regime, "confidence": regime_data['confidence'],
                        "reasoning": reason, "alpha_score": alpha, 
                        "market_data": {**regime_data, "patterns": patterns}
                    })
                    continue
                
                print(f"    ✅ LAYER 1-3 PASSED: High-conviction candidate found!")
                candidates.append({
                    "symbol": symbol,
                    "regime_data": regime_data,
                    "news_data": news_bias,
                    "patterns": patterns,
                    "quant_features": quant_features
                })
                
            except Exception as e:
                print(f"    ⚠️ Error analyzing {symbol}: {e}")
                continue

        # --- LAYER 4: Gemini Execution Gate ---
        for candidate in candidates:
            symbol = candidate['symbol']
            
            if not usage.can_make_request():
                print(f"\n⚠️ Gemini Budget exhausted for {symbol}.")
                continue
                
            print(f"\n🚀 TRACING GEMINI EXECUTION GATE for {symbol}...")
            
            # Identify existing positions for this symbol
            existing_pos = [p for p in self.execution.get_positions() if p['symbol'] == symbol]
            candidate['quant_features']['open_positions'] = len(existing_pos)
            
            result = ai_analyst.analyze_symbol(symbol, candidate.get('quant_features'))
            if result:
                report_path, verdict = result
                print(f"✅ AI Analysis Complete: {report_path}")
                print(f"🧠 VERDICT: {verdict.get('action')} (Conf: {verdict.get('confidence')}%)")
                
                action = verdict.get('action')
                if action in ["BUY", "SELL"] and AUTO_EXECUTE:
                    
                    # 1. Check if we should Scale-In (Pyramid) or start new
                    if self.risk.can_add_to_winner(symbol, action):
                        
                        # Calculate current pyramid level
                        existing = [p for p in self.execution.get_positions() if p['symbol'] == symbol]
                        level = len(existing) + 1
                        risk_mult = self.risk.get_pyramid_risk_multiplier(level)
                        
                        # 2. Dynamic Position Sizing (Half-Kelly Optimized + Hurst Aware)
                        sl_pips = verdict.get('sl_pips', 50)
                        win_rate_est = verdict.get('confidence', 50) / 100.0
                        hurst_val = candidate.get('quant_features', {}).get('hurst', 0.5)
                        
                        lots = self.risk.calculate_lot_size(
                            symbol=symbol, 
                            risk_percent=RISK_PER_TRADE * risk_mult, 
                            sl_pips=sl_pips,
                            win_rate=win_rate_est,
                            rr_ratio=2.0, # Default institutional targeting
                            hurst=hurst_val
                        )
                        
                        print(f"🔥 EXECUTING {action} Unit {level} for {symbol} ({lots} lots)...")
                        
                        order_result = self.execution.execute_order(
                            symbol=symbol,
                            order_type=action, 
                            volume=lots,
                            sl_pips=sl_pips,
                            tp_pips=verdict.get('tp_pips', 100),
                            comment=f"Titan-Auto-L{level}"
                        )
                        
                        if order_result:
                            # 3. Cluster Protection: Move all SLs to protect profits
                            if level > 1:
                                print(f"🛡️ Unit {level} added. Adjusting Cluster SL to protect profits...")
                                # Logic: Move previous units to breakeven or unified SL
                                new_sl = verdict.get('sl') # AI suggested price level
                                for pos in existing:
                                    self.execution.modify_position(pos['ticket'], sl=new_sl)
                            
                            print(f"💰 TRADE SUCCESSFUL: Ticket {order_result['ticket']}")
                        else:
                            print(f"❌ EXECUTION FAILED for {symbol}")
                    else:
                        print(f"⏳ {symbol} {action} setup ignored (Risk constraints or Pending Profit)")
                
                self.feedback.log_decision({
                    "symbol": symbol,
                    "decision": action if action else "WAIT",
                    "model": "gemini-2.0-flash",
                    "regime": candidate['regime_data']['regime'],
                    "confidence": candidate['regime_data']['confidence'],
                    "reasoning": verdict.get('reason', 'AI Processed'),
                    "alpha_score": candidate['regime_data']['institutional']['alpha_efficiency'],
                    "market_data": {
                        **candidate['regime_data'], 
                        "patterns": candidate['patterns'], 
                        "quant": candidate['quant_features'],
                        "verdict": verdict
                    }
                })
            else:
                print(f"❌ Gemini Execution Gate Error: {symbol}")

    def run_loop(self):
        """Main execution loop."""
        while True:
            try:
                self.run_funnel()
            except KeyboardInterrupt:
                print("\n🛑 Sentinel Stopped by User.")
                break
            except Exception as e:
                print(f"\n💥 Global Error: {e}")
            
            print(f"\n💤 Sleeping for {SCAN_INTERVAL_MINUTES} minutes...")
            time.sleep(SCAN_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    sentinel = AutonomousSentinel()
    sentinel.run_loop()
