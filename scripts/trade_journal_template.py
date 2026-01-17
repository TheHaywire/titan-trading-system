"""
TRADE JOURNAL - Track Every Trade Like a Pro
Run this after EVERY trade you close
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime
import json

def log_trade():
    print("="*60)
    print("📓 TRADE JOURNAL ENTRY")
    print("="*60)
    
    # Get last closed trade
    if not mt5.initialize():
        print("MT5 init failed")
        return
    
    # Get history from last 24 hours
    from datetime import timedelta
    from_date = datetime.now() - timedelta(hours=24)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    if not deals or len(deals) < 2:
        print("No recent trades found")
        mt5.shutdown()
        return
    
    # Get the last exit (position close)
    last_deal = deals[-1]
    
    print(f"\nSymbol: {last_deal.symbol}")
    print(f"Direction: {'BUY' if last_deal.type == 0 else 'SELL'}")
    print(f"Volume: {last_deal.volume}")
    print(f"Entry Price: {last_deal.price}")
    print(f"Profit: ${last_deal.profit:,.2f}")
    print(f"Time: {datetime.fromtimestamp(last_deal.time)}")
    
    # Interactive questions
    print("\n" + "="*60)
    print("JOURNAL QUESTIONS (Answer honestly):")
    print("="*60)
    
    questions = [
        "1. Why did you take this trade? (Setup/Strategy)",
        "2. Did you follow your trading plan? (Yes/No)",
        "3. How did you FEEL when entering? (Calm/Excited/Fearful)",
        "4. How did you FEEL when exiting? (Satisfied/Regret/Relief)",
        "5. What did you learn from this trade?",
        "6. What would you do differently next time?"
    ]
    
    answers = {}
    for q in questions:
        answer = input(f"\n{q}\n> ")
        answers[q] = answer
    
    # Save to journal file
    journal_entry = {
        "date": datetime.now().isoformat(),
        "symbol": last_deal.symbol,
        "direction": "BUY" if last_deal.type == 0 else "SELL",
        "volume": last_deal.volume,
        "profit": last_deal.profit,
        "answers": answers
    }
    
    # Append to journal file
    journal_file = "data/trade_journal.jsonl"
    os.makedirs("data", exist_ok=True)
    
    with open(journal_file, "a") as f:
        f.write(json.dumps(journal_entry) + "\n")
    
    print("\n✅ Journal entry saved!")
    print(f"Total entries: {sum(1 for _ in open(journal_file))}")
    
    mt5.shutdown()

if __name__ == "__main__":
    log_trade()
