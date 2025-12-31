import logging
import asyncio
from titan_system.execution.main_loop import TitanBot

# Concise logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

async def test_live_notifications():
    print("\n" + "="*60)
    print("   TITAN LIVE ALERTS DEMO")
    print("="*60 + "\n")
    
    # 1. Init Bot
    bot = TitanBot(universe=["GOLD"])
    
    if not bot.notifier.enabled:
        print("❌ Telegram NOT enabled. Check your .env file.")
        return

    print("📤 Sending System Startup Alert...")
    bot.send_telegram_sync("🚀 *TITAN DEMO:* Live Alert System Verified! I am now monitoring GOLD for you.")

    # 2. Mock a Scanner Hit (High Score)
    print("\n[Action] Mocking a High-Conviction Scanner Hit...")
    mock_opp = {
        'symbol': 'GOLD',
        'score': 95,
        'order_type': 'BUY',
        'comment': 'Perfect H4 Trend + H1 Crossover Alignment',
        'checklist': [
            '[X] H4 Trend (UP)',
            '[X] H1 Trigger (BUY)',
            '[X] Trend Power (ADX: 35.0)',
            '[X] Momentum (RSI: 62.0)'
        ]
    }
    
    alert_msg = f"🚨 *MOCK TRADE ALERT: {mock_opp['symbol']}*\n"
    alert_msg += f"Score: {mock_opp['score']}/100\n"
    alert_msg += f"Signal: {mock_opp['order_type']}\n"
    alert_msg += f"Reason: {mock_opp['comment']}\n\n"
    alert_msg += "Checklist:\n" + "\n".join(mock_opp['checklist'])
    
    bot.send_telegram_sync(alert_msg, priority="HIGH")
    
    print("\n✅ Demo notifications sent. Check your Telegram!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_live_notifications())
