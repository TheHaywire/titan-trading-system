"""Quick reconnaissance using MT5"""
import MetaTrader5 as mt5
from mt5_interface import MT5Interface
import datetime

interface = MT5Interface()
interface.start()

# Account Info
account = mt5.account_info()
print("\n" + "="*80)
print("MT5 ACCOUNT RECONNAISSANCE REPORT")
print("="*80)
print(f"\n📊 ACCOUNT: {account.login} | {account.server}")
print(f"💰 Balance: ${account.balance:,.2f}")
print(f"💵 Equity: ${account.equity:,.2f}")
print(f"📈 Profit: ${account.profit:,.2f} ({((account.equity/account.balance-1)*100):.2f}%)")
print(f"📊 Margin Used: ${account.margin:,.2f}")
print(f"🆓 Free Margin: ${account.margin_free:,.2f}")
if account.margin > 0:
    print(f"📉 Margin Level: {account.margin_level:.1f}%")
print(f"🎯 Leverage: 1:{account.leverage}")

# Open Positions
positions = mt5.positions_get()
print(f"\n📍 OPEN POSITIONS: {len(positions) if positions else 0}")
if positions:
    total_pnl = 0
    for pos in positions:
        emoji = "🟢" if pos.profit > 0 else "🔴"
        action = "BUY" if pos.type == 0 else "SELL"
        print(f"{emoji} {pos.symbol} | {action} | {pos.volume} lots | P&L: ${pos.profit:,.2f}")
        total_pnl += pos.profit
    print(f"💰 Total Unrealized: ${total_pnl:,.2f}")

# Recent History (Last 7 days)
from_date = datetime.datetime.now() - datetime.timedelta(days=7)
deals = mt5.history_deals_get(from_date, datetime.datetime.now())
if deals:
    closed = [d for d in deals if d.profit != 0 and d.entry == 1] # Entry OUT
    if closed:
        wins = len([d for d in closed if d.profit > 0])
        total_profit = sum(d.profit for d in closed)
        print(f"\n📜 LAST 7 DAYS:")
        print(f"   Trades: {len(closed)} | Wins: {wins} | Losses: {len(closed)-wins}")
        print(f"   Win Rate: {(wins/len(closed)*100):.1f}%")
        print(f"   Net P&L: ${total_profit:,.2f}")

# Market Scan
from market_scanner import MarketScanner
scanner = MarketScanner()
symbols = scanner.get_tradable_symbols(max_spread=20)
print(f"\n🎯 MARKET SCAN: {len(symbols)} tradable symbols found")

# Top opportunities (quick check)
from strategy import Strategy
opportunities = []
for sym in symbols[:10]:  # Check first 10
    df = interface.get_closes(sym, mt5.TIMEFRAME_H1, 100)
    if df is not None:
        s = Strategy(sym, mt5.TIMEFRAME_H1)
        signal = s.generate_signal(df)
        if signal:
            opportunities.append((sym, signal))

if opportunities:
    print(f"⚡ CURRENT SIGNALS:")
    for sym, sig in opportunities:
        emoji = "🟢" if sig == "BUY" else "🔴"
        print(f"   {emoji} {sym} → {sig}")
else:
    print("   No signals at this time")

# Risk Analysis
print(f"\n⚠️  RISK ASSESSMENT:")
if account.margin > 0:
    exposure = (account.margin / account.equity) * 100
    print(f"   Margin Usage: {exposure:.1f}%")
    if exposure > 50:
        print("   🚨 HIGH RISK - Reduce positions!")
    elif exposure > 30:
        print("   ⚠️  MODERATE - Monitor closely")
    else:
        print("   ✅ SAFE - Good position sizing")
else:
    print("   ✅ No active positions")

print("\n" + "="*80)
print("Report complete at", datetime.datetime.now().strftime('%H:%M:%S'))
print("="*80 + "\n")

interface.shutdown()
