
import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_system.core.execution import MT5Execution
from titan_system.analytics.market_state import MarketAnalyzer
from titan_system.notifications.email import EmailNotifier
from config.settings import settings

async def generate_single_report(symbol: str):
    print(f"🚀 Generating ON-DEMAND Report for {symbol}...")
    
    # 1. Initialize Components
    execution = MT5Execution(settings)
    if not execution.connect():
        print("❌ Failed to connect to MT5")
        return

    brain = MarketAnalyzer(execution)
    notifier = EmailNotifier()
    
    # 2. Force Analysis
    print("🧠 Analyzing Market Structure...")
    market_state = await brain.analyze_symbol(symbol)
    
    if not market_state:
        print("❌ Failed to fetch market data.")
        return

    # FORCE AI Analysis if it was skipped (e.g. Neutral Score)
    if not isinstance(market_state['ai_insight'], str) or market_state['ai_insight'] in ["Waiting for Signal strength > 40/60", "AI Loading..."]:
        print("⚡ Forcing AI Analysis for Manual Request...")
        
        h1 = market_state['timeframes']['H1']
        d1 = market_state['timeframes']['D1']
        current_price = market_state.get('prices', {}).get('current', 0)
        
        ai_data = {
             'price': current_price,
             'trend': h1['trend'],
             'rsi': h1['rsi'],
             'adx': h1['adx'],
             'd1_trend': d1['trend'],
             'pivot': market_state['pivot_points']['pp']
        }
        
        try:
            insight = await brain.ai.analyze(symbol, ai_data)
            market_state['ai_insight'] = insight
        except Exception as e:
            print(f"AI Failed: {e}")

    print(f"✅ Analysis Complete. Score: {market_state['score']}")
    
    # 3. Construct Email Content
    trade_data = {
        'symbol': symbol,
        'type': 'MARKET REPORT',
        'price': market_state.get('prices', {}).get('current', 0),
        'comment': 'On-Demand Intelligence'
    }
    
    print("📧 Sending Rich Email...")
    notifier.send_trade_alert(trade_data, market_state)
    print("✅ Email Sent!")
    
    # Clean shutdown
    execution.shutdown()

if __name__ == "__main__":
    target = "BTCUSD"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    asyncio.run(generate_single_report(target))
