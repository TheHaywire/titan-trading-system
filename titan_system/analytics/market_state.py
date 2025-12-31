
import logging
import asyncio
import pandas as pd
import datetime
import MetaTrader5 as mt5
from titan_system.analytics.indicators import IndicatorFactory
from titan_system.analytics.news import NewsFilter
from titan_system.analytics.ai_analyst import AIAnalyst
from titan_system.analytics.sessions import SessionManager

logger = logging.getLogger("Titan.MarketState")

class MarketAnalyzer:
    """
    The 'Brain' of Titan Intelligence.
    Fetches multi-timeframe data and computes a unified market view.
    """
    def __init__(self, execution_client):
        self.execution = execution_client
        self.news = NewsFilter()
        self.ai = AIAnalyst()
        self.ai_cache = {} # {symbol: {'insight': str, 'time': datetime}}

    async def analyze_symbol(self, symbol: str) -> dict:
        """
        Performs deep analysis on a symbol across M5, H1, and D1 timeframes.
        Returns a 'Glass Box' report with reasoning.
        """
        # 1. Fetch Data Concurrently
        timeframes = {
            "M5": mt5.TIMEFRAME_M5,
            "H1": mt5.TIMEFRAME_H1,
            "D1": mt5.TIMEFRAME_D1
        }
        
        data = {}
        # Note: In a real async MT5 client we'd use gather, but here we loop 
        # because the MT5 python library is synchronous.
        for tf_name, tf_code in timeframes.items():
            df = self.execution.get_data(symbol, tf_code, 200)
            if df is not None:
                data[tf_name] = IndicatorFactory.calculate_all(df)
            else:
                logger.warning(f"Failed to fetch {tf_name} data for {symbol}")
                return None

        if len(data) < 3:
            return None # Incomplete data

        # 2. Extract Key States
        m5_state = IndicatorFactory.get_market_state(data['M5'])
        h1_state = IndicatorFactory.get_market_state(data['H1'])
        d1_state = IndicatorFactory.get_market_state(data['D1'])

        # Initialize reasoning list early to avoid errors
        reasoning = [] 

        # 3. Compute Confluence Score (0-100)
        # Weightage: H1 (50%), D1 (30%), M5 (20%)
        score = 50 # Default Neutral
        
        # Trend Alignment Bonus
        if h1_state['trend'] == "BULLISH" and d1_state['trend'] == "BULLISH":
            score += 20
        elif h1_state['trend'] == "BEARISH" and d1_state['trend'] == "BEARISH":
            score -= 20
            
        # Momentum Bonus
        if m5_state['momentum'] == "BULLISH": score += 10
        if m5_state['momentum'] == "BEARISH": score -= 10
        
        # 4. News Check
        news_report = self.news.check_risk(symbol)
        if news_report['risk_level'] == 'HIGH':
            score = 0 # Kill score on high news
            reasoning.append(f"⛔ NEWS ALERT: {news_report['message']}")
        
        # 5. Session Check
        session_status = SessionManager.get_market_status()
        is_active_session = symbol in session_status['recommended_symbols']
        
        if not is_active_session and session_status['active_sessions']:
             # If trading outside active session for this symbol (e.g. trading EURUSD in Asian session)
             # we apply a small penalty or just note it.
             score -= 10
             reasoning.append(f"⚠️ Low Liquidity: {symbol} is inactive in {session_status['active_sessions']}")
        elif is_active_session:
             score += 5
             reasoning.append(f"✅ Prime Volume: Active in {'/'.join(session_status['active_sessions'])}")

        # 6. Generate Reasoning (Additional)
        if d1_state['trend'] == "BULLISH": reasoning.append("Daily Trend is Up")
        if h1_state['trend'] == "BULLISH": reasoning.append("Hourly Trend is Up")
        if m5_state['rsi'] < 30: reasoning.append("Short-term Oversold (RSI < 30)")
        if h1_state['volatility'] == "HIGH": reasoning.append("High Volatility Detected")

        # 7. AI Insight (Cached 15 mins)
        ai_insight = "AI Loading..."
        now = datetime.datetime.now()
        
        # Check cache
        cache_entry = self.ai_cache.get(symbol)
        if cache_entry and (now - cache_entry['time']).total_seconds() < 900:
             ai_insight = cache_entry['insight']
        else:
             # Only query AI if we have a "interesting" setup (Score > 60 or < 40)
             # to save API calls.
             if score > 60 or score < 40:
                 # Run in background to not block main loop? 
                 # For now, let's just await it properly (it's synchronous in ai_analyst currently, but fast enough)
                 # Converting synchronous generate_content to async structure requires loop.run_in_executor
                 
                 # Prepare data subset for AI
                 ai_data = {
                     'price': data['H1'].iloc[-1]['close'],
                     'trend': h1_state['trend'],
                     'rsi': h1_state['rsi'],
                     'adx': h1_state['adx'],
                     'd1_trend': d1_state['trend'],
                     'pivot': data['H1'].iloc[-1]['pivot_pp']
                 }
                 
                 # Fire and forget update? No, we want the result.
                 # We'll do a simple non-blocking call in future, for now blocking is safer for v1
                 try:
                     ai_insight = await self.ai.analyze(symbol, ai_data)
                     self.ai_cache[symbol] = {'insight': ai_insight, 'time': now}
                 except Exception:
                     ai_insight = "AI Busy"
             else:
                 ai_insight = "Waiting for Signal strength > 40/60"

        # 8. Strategy Category Analysis (The "Institutional View")
        categories = {
            "Trend Following": {
                "score": 80 if h1_state['trend'] == "BULLISH" and h1_state['adx'] > 25 else 20,
                "label": "STRONG" if h1_state['adx'] > 25 else "WEAK/CHOP",
                "status": h1_state['trend']
            },
            "Mean Reversion": {
                "score": 90 if (h1_state['rsi'] < 30 or h1_state['rsi'] > 70) else 10,
                "label": "ACTIVE" if (h1_state['rsi'] < 30 or h1_state['rsi'] > 70) else "SLEEPING",
                "status": "OVERSOLD" if h1_state['rsi'] < 30 else "OVERBOUGHT" if h1_state['rsi'] > 70 else "NEUTRAL"
            },
            "Volatility": {
                "label": h1_state['volatility'],
                "status": "EXPANDING" if h1_state['volatility'] == "HIGH" else "STABLE"
            }
        }

        return {
            "symbol": symbol,
            "score": max(0, min(100, score)), # Clamp 0-100
            "bias": "BULLISH" if score > 60 else "BEARISH" if score < 40 else "NEUTRAL",
            "categories": categories, # NEW
            "timeframes": {
                "M5": m5_state,
                "H1": h1_state,
                "D1": d1_state
            },
            "prices": {
                 "current": data['H1'].iloc[-1]['close'],
            },
            "reasoning": reasoning,
            "ai_insight": ai_insight,
            "news": news_report,
            "pivot_points": {
                "r1": data['H1'].iloc[-1]['pivot_r1'],
                "s1": data['H1'].iloc[-1]['pivot_s1'],
                "pp": data['H1'].iloc[-1]['pivot_pp']
            }
        }
