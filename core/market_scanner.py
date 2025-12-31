import MetaTrader5 as mt5
import pandas as pd
from core.mt5_interface import MT5Interface

class MarketScanner:
    def __init__(self):
        self.interface = MT5Interface()
        # Import engines locally to avoid circular deps if any
        try:
            from core.reasoning_engine import ReasoningEngine
            from core.scenario_analyzer import ScenarioAnalyzer
            from core.strategy import Strategy
        except ImportError:
            # Fallback for dev environment without package structure
            import sys
            sys.path.append(".")
            from core.reasoning_engine import ReasoningEngine
            from core.scenario_analyzer import ScenarioAnalyzer
            from core.strategy import Strategy

        self.reasoning = ReasoningEngine
        self.scenario = ScenarioAnalyzer
        self.Strategy = Strategy

    def scan(self, categories=None, max_spread=50):
        """
        Deep Scan of the market.
        Returns detailed report of Accepted and Rejected trades.
        """
        if not self.interface.start():
            return {'accepted': [], 'rejected': []}

        if categories is None:
            # Default Categories
            categories = {
                "Major Forex": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"],
                "Metals": ["XAUUSD", "XAGUSD"],
                "Crypto": ["BTCUSD", "ETHUSD"]
            }

        scan_results = {
            'accepted': [],
            'rejected': [],
            'summary': {}
        }

        print("🧠 Starting Deep Reasoning Scan...")

        for category, symbols in categories.items():
            print(f"  🔍 Analyzing {category}...")
            
            for symbol in symbols:
                # 1. Technical Analysis & Data Fetching
                try:
                    # Get Data first (we need it for ATR)
                    df = self.interface.get_closes(symbol, mt5.TIMEFRAME_H1, 200)
                    if df is None:
                        continue

                    # Calculate ATR (Volatility)
                    import numpy as np
                    current_price = df['close'].iloc[-1]
                    df['tr'] = np.maximum(df['high'] - df['low'], np.abs(df['high'] - df['close'].shift(1)))
                    atr = df['tr'].rolling(14).mean().iloc[-1]

                    # 2. Dynamic Spread Check (Data-Driven)
                    # Instead of hard limit 50, we check if spread eats too much of the expected move.
                    info = mt5.symbol_info(symbol)
                    if not info:
                        continue
                        
                    # Convert spread points to price difference
                    spread_cost = info.spread * info.point 
                    
                    # Rule: Spread shouldn't exceed 10% of the hourly ATR
                    # If the candle moves 10 pips, and spread is 2 pips, that's 20% friction. Too high.
                    # We want friction < 10-15%
                    spread_threshold = atr * 0.15 
                    
                    if spread_cost > spread_threshold:
                        scan_results['rejected'].append({
                            'symbol': symbol,
                            'reason_code': 'HIGH_COST_RATIO',
                            'reason_text': f"Spread Cost ({spread_cost:.5f}) > 15% of ATR ({atr:.5f})",
                            'data': {'spread': info.spread, 'atr': atr, 'ratio': spread_cost/atr}
                        })
                        continue

                    # Run Strategy
                    # 2025-12-07: Load Evolved Parameters if available
                    import json
                    import os
                    params = None
                    # Updated to look in data/ folder for brains
                    brain_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data', f"brain_{symbol}.json")
                    
                    if os.path.exists(brain_file):
                        # print(f"  🧠 Using evolved brain for {symbol}")
                        try:
                            with open(brain_file, 'r') as f:
                                data = json.load(f)
                                # Handle new metadata format vs old raw format
                                if 'genes' in data:
                                    params = data['genes']
                                else:
                                    params = data
                        except:
                            pass
                            
                    strat = self.Strategy(symbol, mt5.TIMEFRAME_H1, params=params)
                    signal = strat.generate_signal(df)
                    
                    # Calculate Metrics
                    import numpy as np
                    current_price = df['close'].iloc[-1]
                    df['tr'] = np.maximum(df['high'] - df['low'], np.abs(df['high'] - df['close'].shift(1)))
                    atr = df['tr'].rolling(14).mean().iloc[-1]
                    sma_long = df['SMA_100'].iloc[-1] if 'SMA_100' in df else current_price
                    trend = "BULLISH" if current_price > sma_long else "BEARISH"
                    volatility_ratio = (atr / current_price) * 100
                    
                    data_context = {
                        'symbol': symbol,
                        'price': current_price,
                        'atr': atr,
                        'trend': trend,
                        'rsi': df['RSI'].iloc[-1] if 'RSI' in df else 50,
                        'spread': info.spread
                    }

                    # 3. Decision Logic
                    if signal:
                        # ACCEPTED
                        # Calculate Financial Scenarios
                        sl = current_price - (atr * 1.5) if signal == 'BUY' else current_price + (atr * 1.5)
                        tp = current_price + (atr * 3.0) if signal == 'BUY' else current_price - (atr * 3.0)
                        
                        financials = self.scenario.analyze_trade(current_price, sl, tp, 0.1, info) # 0.1 Lot default
                        
                        # Generate "Why"
                        why_text = self.reasoning.analyze_acceptance(signal, trend, atr, volatility_ratio)
                        
                        # Determine Style
                        style = "SCALP" if volatility_ratio > 0.05 else "SWING"
                        
                        scan_results['accepted'].append({
                            'symbol': symbol,
                            'signal': signal,
                            'entry': current_price,
                            'sl': sl,
                            'tp': tp,
                            'atr': atr,
                            'volatility': volatility_ratio,
                            'style': style,
                            'financials': financials,
                            'why': why_text,
                            'category': category
                        })
                    else:
                        # REJECTED (Technical)
                        # Infer rejection reason
                        # e.g. Trend mismatch or RSI filters
                        # For now, simple logic
                        reason_code = "NO_SIGNAL"
                        if trend == "BULLISH" and data_context['rsi'] > 70:
                            reason_code = "RSI_OVERBOUGHT"
                        elif trend == "BEARISH" and data_context['rsi'] < 30:
                            reason_code = "RSI_OVERSOLD"
                            
                        why_not = self.reasoning.analyze_rejection(symbol, reason_code, data_context)
                        
                        scan_results['rejected'].append({
                            'symbol': symbol,
                            'reason_code': reason_code,
                            'reason_text': why_not,
                            'data': data_context
                        })

                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

        print(f"✅ Deep Scan Complete. Accepted: {len(scan_results['accepted'])}, Rejected: {len(scan_results['rejected'])}")
        self.interface.shutdown()
        return scan_results

if __name__ == "__main__":
    scanner = MarketScanner()
    # Deep Scan
    results = scanner.scan(max_spread=30)
    print("\nACCEPTED TRADES:")
    for t in results['accepted']:
        print(f"✅ {t['symbol']} ({t['signal']}): {t['why']}")
        
    print("\nREJECTED SAMPLES:")
    for t in results['rejected'][:5]:
        print(f"❌ {t['symbol']}: {t['reason_text']}")
