"""
MT5 Account Reconnaissance Script
Generates a comprehensive analysis of your trading account state.
"""
import MetaTrader5 as mt5
from mt5_interface import MT5Interface
import pandas as pd
import datetime
from daily_analyst import DailyAnalyst

class MT5Recon:
    def __init__(self):
        self.interface = MT5Interface()
        
    def generate_full_report(self):
        if not self.interface.start():
            print("❌ Failed to connect to MT5")
            return
            
        # Open output file
        output_file = open("RECON_REPORT.txt", "w", encoding="utf-8")
        
        def print_both(*args, **kwargs):
            """Print to both console and file"""
            print(*args, **kwargs)
            print(*args, **kwargs, file=output_file)
        
        print_both("=" * 80)
        print_both("🔍 TITAN TRADING SYSTEM - ACCOUNT RECONNAISSANCE REPORT")
        print_both("=" * 80)
        print_both(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_both()
        
        # 1. Account Overview
        self._print_account_info()
        
        # 2. Open Positions
        self._print_open_positions()
        
        # 3. Recent History
        self._print_trade_history()
        
        # 4. Market Scan
        self._print_market_opportunities()
        
        # 5. Risk Analysis
        self._print_risk_analysis()
        
        print("=" * 80)
        print("✅ Reconnaissance Complete")
        print("=" * 80)
        
        self.interface.shutdown()
        
    def _print_account_info(self):
        account = mt5.account_info()
        if not account:
            print("⚠️  Could not fetch account info")
            return
            
        print("📊 ACCOUNT OVERVIEW")
        print("-" * 80)
        print(f"Account ID:       {account.login}")
        print(f"Server:           {account.server}")
        print(f"Name:             {account.name}")
        print(f"Company:          {account.company}")
        print()
        print(f"💰 Balance:       ${account.balance:,.2f}")
        print(f"💵 Equity:        ${account.equity:,.2f}")
        print(f"📈 Profit:        ${account.profit:,.2f}")
        print(f"📊 Margin:        ${account.margin:,.2f}")
        print(f"🆓 Free Margin:   ${account.margin_free:,.2f}")
        print(f"📉 Margin Level:  {account.margin_level:.2f}%" if account.margin > 0 else "📉 Margin Level:  N/A (No positions)")
        print()
        print(f"🎯 Leverage:      1:{account.leverage}")
        print(f"💱 Currency:      {account.currency}")
        print()
        
    def _print_open_positions(self):
        positions = mt5.positions_get()
        
        print("📍 OPEN POSITIONS")
        print("-" * 80)
        
        if not positions or len(positions) == 0:
            print("   No open positions")
            print()
            return
            
        total_profit = 0
        for pos in positions:
            profit_emoji = "🟢" if pos.profit > 0 else "🔴"
            type_str = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
            
            print(f"{profit_emoji} {pos.symbol} | {type_str} | {pos.volume} lots")
            print(f"   Entry: {pos.price_open:.5f} | Current: {pos.price_current:.5f}")
            print(f"   P&L: ${pos.profit:,.2f} | Swap: ${pos.swap:,.2f}")
            print(f"   Opened: {datetime.datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M')}")
            print()
            total_profit += pos.profit
            
        print(f"💰 Total Unrealized P&L: ${total_profit:,.2f}")
        print()
        
    def _print_trade_history(self):
        print("📜 RECENT TRADE HISTORY (Last 7 Days)")
        print("-" * 80)
        
        # Get deals from last 7 days
        from_date = datetime.datetime.now() - datetime.timedelta(days=7)
        deals = mt5.history_deals_get(from_date, datetime.datetime.now())
        
        if not deals or len(deals) == 0:
            print("   No trades in the last 7 days")
            print()
            return
            
        # Filter only position closures (profit != 0)
        closed_deals = [d for d in deals if d.profit != 0 and d.entry == mt5.DEAL_ENTRY_OUT]
        
        if not closed_deals:
            print("   No closed positions in the last 7 days")
            print()
            return
            
        wins = len([d for d in closed_deals if d.profit > 0])
        losses = len([d for d in closed_deals if d.profit < 0])
        total_profit = sum(d.profit for d in closed_deals)
        
        print(f"   Total Trades: {len(closed_deals)}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {(wins/len(closed_deals)*100):.1f}%" if closed_deals else "   Win Rate: N/A")
        print(f"   Net P&L: ${total_profit:,.2f}")
        print()
        
        # Show last 5 trades
        print("   Last 5 Trades:")
        for deal in sorted(closed_deals, key=lambda x: x.time, reverse=True)[:5]:
            emoji = "✅" if deal.profit > 0 else "❌"
            type_str = "BUY" if deal.type == mt5.ORDER_TYPE_BUY else "SELL"
            print(f"   {emoji} {deal.symbol} | {type_str} | ${deal.profit:,.2f} | {datetime.datetime.fromtimestamp(deal.time).strftime('%m-%d %H:%M')}")
        print()
        
    def _print_market_opportunities(self):
        print("🎯 CURRENT MARKET OPPORTUNITIES")
        print("-" * 80)
        
        # Use existing Daily Analyst logic
        analyst = DailyAnalyst()
        
        # Quick scan (top 10 only for speed)
        symbols = analyst.scanner.get_tradable_symbols(max_spread=30)
        if not symbols:
            print("   Could not scan market")
            print()
            return
            
        print(f"   Scanning {len(symbols)} symbols...")
        
        # Analyze top movers
        opportunities = []
        for symbol in symbols[:20]:  # Limit to 20 for speed
            try:
                import MetaTrader5 as mt5_lib
                df = analyst.interface.get_closes(symbol, mt5_lib.TIMEFRAME_H1, num_candles=100)
                if df is not None and len(df) > 50:
                    strat = analyst.scanner.interface
                    from strategy import Strategy
                    s = Strategy(symbol, mt5_lib.TIMEFRAME_H1)
                    signal = s.generate_signal(df)
                    
                    if signal:
                        opportunities.append((symbol, signal))
            except:
                continue
                
        if opportunities:
            print(f"   🚀 Found {len(opportunities)} signals:")
            for sym, sig in opportunities[:5]:
                emoji = "🟢" if sig == "BUY" else "🔴"
                print(f"   {emoji} {sym} → {sig}")
        else:
            print("   No strong signals at this moment")
        print()
        
    def _print_risk_analysis(self):
        print("⚠️  RISK ANALYSIS")
        print("-" * 80)
        
        account = mt5.account_info()
        positions = mt5.positions_get()
        
        if not account:
            return
            
        # Calculate exposure
        total_volume = sum(pos.volume for pos in positions) if positions else 0
        exposure_pct = (account.margin / account.equity * 100) if account.equity > 0 else 0
        
        print(f"   Total Exposure: {total_volume:.2f} lots")
        print(f"   Margin Usage: {exposure_pct:.1f}%")
        
        # Risk warnings
        if exposure_pct > 50:
            print("   ⚠️  WARNING: High margin usage")
        elif exposure_pct > 30:
            print("   ⚡ CAUTION: Moderate margin usage")
        else:
            print("   ✅ SAFE: Low margin usage")
            
        # Account health
        if account.margin_level and account.margin_level < 200:
            print("   🚨 CRITICAL: Low margin level - Risk of margin call!")
        elif account.margin_level and account.margin_level < 500:
            print("   ⚠️  WARNING: Margin level below recommended threshold")
        else:
            print("   ✅ Account health: GOOD")
        print()

if __name__ == "__main__":
    recon = MT5Recon()
    recon.generate_full_report()
