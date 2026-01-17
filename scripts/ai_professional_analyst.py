"""
AI-Powered Professional Market Analysis
Uses Gemini AI to generate institutional-grade trade reports
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Install with: pip install google-generativeai")

from config.settings import settings

try:
    from titan_system.core.news_intelligence import get_news_context
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

# Try to import usage tracker
try:
    from titan_system.core.gemini_usage import can_make_request, track_request, get_usage_status
    USAGE_TRACKING = True
except ImportError:
    USAGE_TRACKING = False

# Try to import comprehensive market intelligence
try:
    from titan_system.core.comprehensive_intel import ComprehensiveIntel
    INTEL_AVAILABLE = True
except ImportError:
    INTEL_AVAILABLE = False

# Initialize Gemini
def init_gemini():
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = getattr(settings, 'google_api_key', None) or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not found in settings or environment")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Try newer models first
        for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"✅ Gemini initialized with {model_name}")
                return model
            except:
                continue
        return None
    except Exception as e:
        print(f"❌ Failed to initialize Gemini: {e}")
        return None

def get_market_data(symbol: str):
    """Fetch comprehensive market data for AI analysis"""
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return None
    
    data = {}
    
    # Current price info
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        data['current_price'] = tick.ask
        data['bid'] = tick.bid
        data['spread'] = round((tick.ask - tick.bid) * 10000, 1)  # in pips
    
    # Get OHLC data for multiple timeframes
    timeframes = {
        '1W': mt5.TIMEFRAME_W1,
        '1D': mt5.TIMEFRAME_D1,
        '4H': mt5.TIMEFRAME_H4,
        '1H': mt5.TIMEFRAME_H1,
    }
    
    for tf_name, tf in timeframes.items():
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, 100)
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate indicators
            close = df['close']
            high = df['high']
            low = df['low']
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            # Moving Averages
            sma_20 = close.rolling(20).mean()
            sma_50 = close.rolling(50).mean()
            
            # ATR
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            # Support/Resistance
            recent = df.tail(20)
            support = recent['low'].min()
            resistance = recent['high'].max()
            
            data[tf_name] = {
                'close': round(close.iloc[-1], 5),
                'high': round(high.iloc[-1], 5),
                'low': round(low.iloc[-1], 5),
                'rsi': round(rsi.iloc[-1], 1) if not np.isnan(rsi.iloc[-1]) else 50,
                'sma_20': round(sma_20.iloc[-1], 5) if not np.isnan(sma_20.iloc[-1]) else close.iloc[-1],
                'sma_50': round(sma_50.iloc[-1], 5) if not np.isnan(sma_50.iloc[-1]) else close.iloc[-1],
                'atr': round(atr.iloc[-1], 5) if not np.isnan(atr.iloc[-1]) else 0,
                'support': round(support, 5),
                'resistance': round(resistance, 5),
                'trend': 'BULLISH' if close.iloc[-1] > sma_50.iloc[-1] else 'BEARISH'
            }
    
    # Add news context if available
    if NEWS_AVAILABLE:
        try:
            news_context = get_news_context(symbol)
            data['news'] = news_context
        except Exception as e:
            data['news'] = {'error': str(e)}
    
    # Add comprehensive market intelligence if available
    if INTEL_AVAILABLE:
        try:
            intel = ComprehensiveIntel()
            symbol_intel = intel.get_symbol_intelligence(symbol)  # Fixed method name
            master = symbol_intel.get('master', {})  # Data is nested in 'master'
            sessions = symbol_intel.get('sessions', [])
            
            if master:
                best_session = None
                if sessions:
                    # Find session with lowest spread ratio
                    sorted_sessions = sorted(sessions, key=lambda x: x.get('spread_ratio', 9999))
                    if sorted_sessions:
                        best_session = sorted_sessions[0].get('session', 'Unknown')
                
                data['symbol_properties'] = {
                    'spread_ratio': round(master.get('spread_ratio', 0), 2),
                    'adrenaline_score': round(master.get('adrenaline_score', 0), 2),
                    'avg_atr': round(master.get('avg_h1_atr', 0), 2),
                    'avg_spread': round(master.get('avg_spread', 0), 2),
                    'swap_long': round(master.get('swap_long', 0), 2),
                    'swap_short': round(master.get('swap_short', 0), 2),
                    'is_tradeable': 'YES' if master.get('is_tradeable') else 'NO',
                    'contract_size': master.get('contract_size', 'N/A'),
                    'lot_min': master.get('lot_min', 'N/A'),
                    'lot_max': master.get('lot_max', 'N/A'),
                    'best_session': best_session or master.get('best_session', 'Unknown'),
                    'category': master.get('category', 'Unknown'),
                }
        except Exception as e:
            data['symbol_properties'] = {'error': str(e)}
    
    return data

def generate_ai_report(model, symbol: str, market_data: dict):
    """Generate AI-powered professional trade report"""
    
    prompt = f"""You are Titan, a Senior Institutional Strategist. 
    Analyze the following Multi-Timeframe (MTF) market data for {symbol} and generate a high-precision trading report.

    FRAMEWORK:
    1. **Structure (H4)**: Is the big picture Trending or Ranging? (Use Hurst > 0.55 as Trend confirmation).
    2. **Momentum (H1)**: Is the intermediate flow supporting the H4 structure? (Use ROC & MACD).
    3. **Trigger (M15)**: Is there a tactical entry? (Look for Liquidity Voids/Imbalance or Mean Reversion).

    QUANTITATIVE DATA:
    {json.dumps({k: v for k, v in market_data.items() if k not in ['news', 'symbol_properties']}, indent=2)}

    NEWS & RISKS:
    {json.dumps(market_data.get('news', {}), indent=2)}
    Macro Correlation: (Check 'corr_sp500' and 'risk_prox').

    OUTPUT FORMAT (Markdown):

    # 🏛️ {symbol} Institutional Strategy Brief

    ## 1. Executive Summary
    **Bias:** [BULLISH / BEARISH / NEUTRAL]
    **Conviction:** [High/Medium/Low]
    **Verdict:** [A clear, spoken-english sentence explaining WHY. E.g., "Buying the dip into the M15 Liquidity Void because the H4 Trend is strongly bullish."]

    ## 2. The "Why" (Plain English)
    *   **The Big Picture (H4):** [Explain the structural trend simply. Mention if 'Smart Money' is accummulating via OFI.]
    *   **The Setup (M15):** [Explain the specific trigger. "Price left a void at 2030..."]
    *   **The Risk:** [Mention any news events or macro headwinds.]

    ## 3. Trade Plan
    | Action | Type | Price Zone |
    | :--- | :--- | :--- |
    | **ENTRY** | [Limit/Market] | [Price] |
    | **STOP LOSS** | [Protection] | [Price] (Risk: X pips) |
    | **TARGET 1** | [Conservative] | [Price] |
    | **TARGET 2** | [Runner] | [Price] |

    ---
    *AI Confidence: [X]% | Hurst Regime: [Trending/Ranging]*

    ### FINAL_VERDICT_JSON
    ```json
    {{
      "action": "BUY | SELL | WAIT",
      "confidence": 0-100,
      "sl": 1.2345,
      "tp": 1.2345,
      "sl_pips": 50,
      "tp_pips": 100,
      "reason": "Clear narrative summary of the trade rationale."
    }}
    ```
    """
    
    try:
        # Check usage limits before making request
        if USAGE_TRACKING:
            can_request, msg = can_make_request()
            if not can_request:
                print(f"⚠️ {msg}")
                print("💡 Tip: Wait until tomorrow or upgrade to paid tier")
                return None
            status = get_usage_status()
            print(f"📊 API Usage: {status['requests_used']}/{status['requests_limit']} today")
        
        response = model.generate_content(prompt)
        
        # Track successful request
        if USAGE_TRACKING:
            track_request(tokens_used=len(prompt) + len(response.text))
            
        return response.text
    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_professional_analyst.py SYMBOL")
        print("Example: python ai_professional_analyst.py GOLD")
        return
    
    symbol = sys.argv[1].upper()
    
    print("=" * 60)
    print(f"  🤖 AI PROFESSIONAL ANALYST v1.0")
    print(f"  Symbol: {symbol}")
    print("=" * 60)
    
    # Initialize Gemini
    print("\n🔌 Initializing Gemini AI...")
    model = init_gemini()
    if not model:
        print("❌ Cannot proceed without AI model")
        return
    
    # Get market data
    print(f"\n📊 Fetching market data for {symbol}...")
    market_data = get_market_data(symbol)
    if not market_data:
        print("❌ Failed to fetch market data")
        return
    
    print(f"   Current Price: {market_data.get('current_price', 'N/A')}")
    for tf in ['1W', '1D', '4H', '1H']:
        if tf in market_data:
            print(f"   {tf}: RSI={market_data[tf]['rsi']}, Trend={market_data[tf]['trend']}")
    
    # Generate AI report
    print("\n🧠 Generating AI Professional Report...")
    report = generate_ai_report(model, symbol, market_data)
    
    if report:
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis/{symbol}_AI_REPORT_{timestamp}.md"
        
        os.makedirs("analysis", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ AI Report saved: {filename}")
        print("\n" + "=" * 60)
        print("REPORT PREVIEW:")
        print("=" * 60)
        # Print first 50 lines
        lines = report.split('\n')[:50]
        for line in lines:
            print(line)
        print("\n... [See full report in file]")
        
        print(f"\nREPORT_PATH:{filename}")
    else:
        print("❌ Failed to generate report")
    
    mt5.shutdown()

def analyze_symbol(symbol: str, quant_features: Optional[Dict] = None) -> Optional[tuple]:
    """Helper function for external modules to run a full AI analysis."""
    symbol = symbol.upper()
    model = init_gemini()
    if not model:
        return None
        
    market_data = get_market_data(symbol)
    if not market_data:
        return None
        
    if quant_features:
        market_data['quant_features'] = quant_features
        
    report = generate_ai_report(model, symbol, market_data)
    if not report:
        return None
        
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"analysis/{symbol}_AI_REPORT_{timestamp}.md"
    os.makedirs("analysis", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    # Parse verdict from report
    verdict = {"action": "WAIT"}
    try:
        if "### FINAL_VERDICT_JSON" in report:
            json_str = report.split("### FINAL_VERDICT_JSON")[1].split("```json")[1].split("```")[0].strip()
            verdict = json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Failed to parse verdict: {e}")
        
    return filename, verdict

if __name__ == "__main__":
    main()
