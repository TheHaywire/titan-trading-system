import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
import glob

def get_latest_matrix():
    """Finds the most recent Weekly Trading Plan CSV."""
    files = glob.glob("WEEKLY_TRADING_PLAN_*.csv")
    if not files:
        return None
    # Sort by timestamp in filename (assumes format WEEKLY_TRADING_PLAN_YYYYMMDD_HHMMSS.csv or WEEKLY_TRADING_PLAN_YYYYMMDD.csv)
    files.sort(reverse=True)
    return files[0]

def resolve_root(symbol):
    """Strips broker suffixes to match Matrix roots."""
    return symbol.replace("Cash", "").replace("!", "").replace(".pro", "").replace(".raw", "").replace("m", "").upper()

def get_better_trades(df_matrix, today_trades_roots):
    """Identifies high-conviction Matrix opportunities that weren't traded."""
    # Score >= 4 or <= -4 are 'High Conviction'
    high_conviction = df_matrix[(df_matrix['Net Score'].astype(float).abs() >= 4) & (df_matrix['Focus'] != 'Stand Aside')]
    
    missed = []
    for _, row in high_conviction.iterrows():
        root = str(row['Ticker']).upper()
        if root not in today_trades_roots:
            missed.append({
                'Instrument': row['Instrument'],
                'Score': row['Net Score'],
                'Bias': row['Primary Bias'],
                'Reason': row['Notes']
            })
    return sorted(missed, key=lambda x: abs(x['Score']), reverse=True)

def get_tech_context(symbol, time_pos, count=20):
    """Fetches M15 technical context around the trade time."""
    rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, time_pos, count)
    if rates is None or len(rates) < 2:
        return "Unknown"
    
    # Simple trend detection
    start_price = rates[0]['close']
    end_price = rates[-1]['close']
    trend = "Up" if end_price > start_price else "Down"
    
    # Volatility (High-Low average)
    vols = [r['high'] - r['low'] for r in rates]
    avg_vol = sum(vols) / len(vols)
    
    return {"Trend": trend, "Avg_Bar_Size": avg_vol}

def audit_trades():
    print("=" * 100)
    print("INSTITUTIONAL TRADE AUDITOR & MENTOR")
    print("=" * 100)
    
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return

    # 1. Fetch Today's History
    from_date = datetime.now() - timedelta(days=1)
    to_date = datetime.now()
    
    history = mt5.history_deals_get(from_date, to_date)
    if history is None or len(history) == 0:
        print("  Patience: No closed trades found in the last 24 hours.")
        mt5.shutdown()
        return

    df_trades = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
    # Filter for entries/exits (deal type)
    # 0 = Buy, 1 = Sell
    # We want to group by position ID to see total profit/loss per trade
    
    # 2. Get latest Matrix
    matrix_file = get_latest_matrix()
    if not matrix_file:
        print("⚠️ No Weekly Trading Plan found! Run /plan first.")
        mt5.shutdown()
        return
        
    print(f"📊 Auditing against: {matrix_file}")
    df_matrix = pd.read_csv(matrix_file)
    
    # 3. Process Trades
    audit_results = []
    
    # Group by position to analyze full trade lifecycle
    for pos_id, group in df_trades.groupby('position_id'):
        symbol = group['symbol'].iloc[0]
        root = resolve_root(symbol)
        
        # Determine trade direction and entry info
        entry_deal = group[group['entry'] == mt5.DEAL_ENTRY_IN]
        if entry_deal.empty: continue
        
        entry_time = int(entry_deal['time'].iloc[0])
        direction = "Buy" if entry_deal['type'].iloc[0] == 0 else "Sell"
        total_profit = group['profit'].sum() + group['commission'].sum() + group['swap'].sum()
        
        # Get Matrix Info
        # Match by Ticker OR Instrument name (case-insensitive)
        matrix_row = df_matrix[
            (df_matrix['Ticker'].str.upper() == root) | 
            (df_matrix['Instrument'].str.upper().str.contains(root))
        ]
        
        bias = "Unknown"
        conviction = "N/A"
        if not matrix_row.empty:
            bias = matrix_row['Primary Bias'].iloc[0]
            conviction = matrix_row['Conviction'].iloc[0]
            
        # Get Technical Context (Expert Layer)
        tech = get_tech_context(symbol, entry_time)
        tech_trend = tech['Trend'] if isinstance(tech, dict) else "Unknown"
        
        # Classification
        discipline = "Off-Plan" 
        
        if bias == "Bullish":
            if direction == "Buy":
                discipline = "On-Plan"
            else:
                discipline = "Defiant (Against Bias)"
        elif bias == "Bearish":
            if direction == "Sell":
                discipline = "On-Plan"
            else:
                discipline = "Defiant (Against Bias)"
        elif bias == "Neutral":
            discipline = "Gambling (No Edge)"

        audit_results.append({
            'Symbol': symbol,
            'Direction': direction,
            'Profit': total_profit,
            'Time': datetime.fromtimestamp(entry_time).strftime('%H:%M'),
            'Matrix Bias': bias,
            'Tech Trend': tech_trend,
            'Discipline': discipline
        })

    df_audit = pd.DataFrame(audit_results)
    
    # 4. Find Missed Opportunities
    today_roots = [resolve_root(s) for s in df_audit['Symbol'].unique()] if not df_audit.empty else []
    better_trades = get_better_trades(df_matrix, today_roots)
    
    # 5. Generate Mentor/Critic Report
    print("\n[ PERFORMANCE SUMMARY ]")
    if not df_audit.empty:
        print(df_audit[['Symbol', 'Direction', 'Profit', 'Matrix Bias', 'Discipline']])
    
    on_plan_count = len(df_audit[df_audit['Discipline'] == 'On-Plan']) if not df_audit.empty else 0
    total_trades = len(df_audit) if not df_audit.empty else 0
    discipline_score = (on_plan_count / total_trades * 100) if total_trades > 0 else 0
    
    print(f"\nDiscipline Score: {discipline_score:.1f}%")
    
    # Save Audit
    audit_filename = f"analysis/TRADE_AUDIT_{datetime.now().strftime('%Y%m%d')}.md"
    os.makedirs("analysis", exist_ok=True)
    
    with open(audit_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Institutional Trade Audit - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"**Overall Discipline Score: {discipline_score:.1f}%**\n\n")
        
        if not df_audit.empty:
            f.write("## Execution Log\n")
            f.write(df_audit.to_markdown(index=False))
            f.write("\n\n## 🎓 Mentorship & Strategy Review\n")
            
            # --- SYNTHETIC FEEDBACK ENGINE ---
            defiant_trades = df_audit[df_audit['Discipline'] == 'Defiant (Against Bias)']
            gambling_trades = df_audit[df_audit['Discipline'].str.contains('Gambling|Off-Plan')]
            
            if not defiant_trades.empty or not gambling_trades.empty:
                f.write("### 🚨 The Expert Critique (Quant & Technical Perspective)\n")
                
                # Group by Symbol for deep dive
                for symbol, group in df_audit[df_audit['Discipline'] != 'On-Plan'].groupby('Symbol'):
                    bias = group['Matrix Bias'].iloc[0]
                    tech_trend = group['Tech Trend'].iloc[0]
                    total_pnl = group['Profit'].sum()
                    count = len(group)
                    
                    f.write(f"#### {symbol} Analysis\n")
                    f.write(f"- **Quant Perspective**: You took {count} trades here with a total P&L of ${total_pnl:,.2f}. If this was a proprietary trading firm, your 'Sharpe Ratio' on these specific trades would be negative because you are fighting the dominant flow.\n")
                    f.write(f"- **Technical Perspective**: While the Matrix was **{bias}**, the M15 Technical Trend was **{tech_trend}**. You were attempting to trade a reversal against the HTF Institutional Bias. This is the #1 reason why retail traders blow accounts—they are 'Right' about a pullback but 'Wrong' about the trend.\n")
                    f.write(f"- **The Expert Verdict**: These are **Toxic Profits**. A professional trader would have let the pullback happen and then entered in the direction of the Matrix once the M15 Technicals aligned with the HTF Institutional Bias.\n\n")

                if not gambling_trades.empty:
                    f.write("#### Trading in the 'Gray Zone'\n")
                    f.write(f"- You took {len(gambling_trades)} trades on symbols with 'Unknown' or 'Neutral' Matrix bias.\n")
                    f.write("- **Expert Advice**: Your 'Capital Allocation' efficiency is low. You are tying up margin on symbols without a statistical edge. Focus your liquidity only on the +4 or -4 setups.\n\n")
            
            # --- QUANT SUMMARY ---
            f.write("## 📈 Quantitative Session Metrics\n")
            win_rate = (len(df_audit[df_audit['Profit'] > 0]) / total_trades * 100) if total_trades > 0 else 0
            gross_profit = df_audit[df_audit['Profit'] > 0]['Profit'].sum()
            gross_loss = abs(df_audit[df_audit['Profit'] < 0]['Profit'].sum())
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
            
            f.write(f"- **Win Rate**: {win_rate:.1f}%\n")
            f.write(f"- **Profit Factor**: {profit_factor:.2f}\n")
            f.write(f"- **Institutional Alignment (Discipline)**: {discipline_score:.1f}%\n")
            f.write(f"- **Market Regime Awareness**: " + ("High" if discipline_score > 80 else "Low (Fighting Flow)") + "\n\n")
        else:
            f.write("## Execution Log\nNo trades executed today.\n\n")

        f.write("### ✅ The Discipline (Praise)\n")
        on_plan = df_audit[df_audit['Discipline'] == 'On-Plan']
        if not on_plan.empty:
            f.write(f"You showed professional discipline on **{', '.join(on_plan['Symbol'].unique())}**. These were your cleanest decisions, regardless of the P&L.\n")
        else:
            f.write("No 'On-Plan' trades detected today. Tomorrow is a new opportunity to align with the Matrix.\n")
        
        if better_trades:
            f.write("\n### 💎 Missed High-Conviction Opportunities\n")
            f.write("The Matrix flagged these as 'A-Grade' setups. While you were fighting lower-conviction moves, these were the real institutional targets:\n\n")
            f.write("| Instrument | Score | Bias | Reason |\n")
            f.write("|:-----------|:------|:-----|:-------|\n")
            for bt in better_trades[:5]:
                f.write(f"| {bt['Instrument']} | {bt['Score']} | {bt['Bias']} | {bt['Reason']} |\n")
            f.write("\n> [!IMPORTANT]\n")
            f.write("> **The Golden Rule**: 80% of your profits will come from the 20% of trades that are +4/-4 on the Matrix. Focus on the best, ignore the rest.\n")

    print(f"\n✅ REFINED AUDIT REPORT GENERATED: {audit_filename}")
    mt5.shutdown()

    print(f"\n✅ FULL AUDIT REPORT GENERATED: {audit_filename}")
    mt5.shutdown()

if __name__ == "__main__":
    audit_trades()
