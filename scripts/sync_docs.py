
import sys
import os
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO)

sys.path.append(os.getcwd())
try:
    from titan_system.integrations.google_sheets import TitanSheets
except ImportError as e:
    print(f"Import Error: {e}")
    exit()

def sync_documentation():
    print("🚀 Syncing INSTITUTIONAL COMMAND CENTER...")
    sheets = TitanSheets()
    if not sheets.enabled:
        print("❌ Cloud connection failed.")
        return

    # --- CLUSTER 1: COCKPIT ---
    
    # 1.2 SYSTEM CHECKLIST
    checklist_data = [
        ["HARDWARE", "VPS Latency < 10ms", "⚠️ CHECK", "Dynamic", "Bot", "Ping Google DNS"],
        ["HARDWARE", "RAM Usage < 80%", "✅ OK", "Auto", "Bot", "Task Manager Check"],
        ["MARKET", "Session NOT Asian", "✅ OK", "Dynamic", "Bot", "London/NY Only"],
        ["MARKET", "News Clear (> 30m)", "❓ MANUAL", "Manual", "Human", "ForexFactory Red Folder"],
        ["RISK", "Equity > $9,500", "✅ OK", "Auto", "Bot", "Drawdown Limit"],
        ["RISK", "Exposure < 4 Lots", "✅ OK", "Auto", "Bot", "Exposure Tab"],
        ["MINDSET", "Trader Tilted?", "❓ MANUAL", "Manual", "Human", "Are you chasing?"],
    ]
    sheets.update_documentation("SYSTEM CHECKLIST", checklist_data)
    
    # --- CLUSTER 2: BRAIN ---

    # 2.1 STRATEGY LOGIC
    logic_data = [
        # --- ACTIVE STRATEGIES ---
        ["MomentumScalper", "Entry", "EMA Cross", "9/21", "ADX < 20 Block", "Classic Trend Follow (M1)"],
        ["MomentumScalper", "Filter", "Regime", "TRENDING", "Range Block", "Must match ADX > 25"],
        ["WhaleProtect", "Mgmt", "Size Trigger", "> 2.0 Lots", "N/A", "Activates Trailing Mode"],
        
        # --- DATA-ARMORED FILTERS (New!) ---
        ["Risk-Armor", "Blacklist", "Losing Assets", "GOLD, AUDUSD", "Avoid -$1M combined loss"],
        ["Risk-Armor", "Whitelist", "Champions", "SILVER, GBPUSD", "Focus on $260k+ winner"],
        ["Risk-Armor", "Time-Block", "Death Zone", "18:00-21:00 GMT", "Avoid -$2.5M loss hour"],
        ["Risk-Armor", "Time-Boost", "Golden Hour", "12:00-15:00 GMT", "Trade +$1M profit hour"],
        ["Risk-Armor", "Volume", "Lot Cap", "Max 2.0 Lots", "Prevent outlier ruin"],
        
        # --- INACTIVE STRATEGIES ---
        ["MeanReversion", "Entry", "RSI Extreme", ">70 / <30", "Trend Block", "Counter-trend for Ranging Markets"],
        ["BreakoutHunter", "Entry", "London Open", "08:00 GMT", "False Break", "High Volatility Session Breakout"],
        
        # --- GLOBAL RULES ---
        ["Global", "Risk", "Max Drawdown", "5%", "Hard Stop", "Daily Circuit Breaker"],
        ["Global", "Risk", "Correlation", "Max 2 USD", "N/A", "Prevent stacking same currency"],
    ]
    sheets.update_documentation("STRATEGY LOGIC", logic_data)

    # 2.3 CORRELATION MATRIX (Placeholder)
    corr_data = [
        ["EURUSD", "1.00", "0.85", "-0.60", "0.40", "0.30", "0.50"],
        ["GBPUSD", "0.85", "1.00", "-0.55", "0.35", "0.25", "0.45"],
        ["USDJPY", "-0.60", "-0.55", "1.00", "-0.20", "0.10", "0.60"],
        ["XAUUSD", "0.40", "0.35", "-0.20", "1.00", "0.15", "-0.10"],
    ]
    sheets.update_documentation("CORRELATION MATRIX", corr_data)

    # --- CLUSTER 3: BUSINESS ---

    # 3.1 PRD OBJECTIVES
    prd_data = [
        ["Profitability", "Daily Profit Target", "$124", "$10,000", "0.1%", "IN PROGRESS"],
        ["Profitability", "Sharpe Ratio", "1.2", "> 2.0", "60%", "IMPROVING"],
        ["Risk", "Max Daily Drawdown", "0.5%", "< 5%", "10%", "EXCELLENT"],
        ["Win Rate", "Batting Average", "55%", "> 60%", "92%", "PENDING DATA"],
        ["Activity", "Trades Per Day", "12", "15-25", "50%", "LOW VOLATILITY"],
    ]
    sheets.update_documentation("PRD OBJECTIVES", prd_data)

    # 3.2 PROJECT PLAN
    plan_data = [
        ["1", "Regime Detection", "Bot", "P0", "DONE", "2025-12-11", "ADX Filter Active"],
        ["1", "MTF Trend Logic", "Bot", "P0", "DONE", "2025-12-11", "H1 Confirmation Active"],
        ["2", "Whale Protection", "Bot", "P0", "DONE", "2025-12-11", "Trailing Stop for > 2 Lots"],
        ["2", "Partial Profits", "Bot", "P1", "DONE", "2025-12-11", "50% Close Implemented"],
        ["3", "Session Filters", "Bot", "P1", "DONE", "2025-12-12", "Asian Session Blocked"],
        ["4", "Correlation Logic", "Bot", "P1", "DONE", "2025-12-12", "Max 2 Correlated Pairs"],
        ["5", "News Filter API", "Bot", "P2", "TODO", "2025-12-13", "Need ForexFactory Scraper"],
        ["6", "SQL Database", "Human", "P2", "TODO", "2025-12-15", "Migrate from CSV"],
    ]
    sheets.update_documentation("PROJECT PLAN", plan_data)

    # --- CLUSTER 4: AUDIT ---

    # 4.2 RISK AUDIT
    risk_data = [
        ["Flash Crash (Gold)", "Low (1%)", "Critical (Ruin)", "Hard Stop + Low Lev", "ACTIVE"],
        ["Broker Slippage", "High (20%)", "Low (Annoyance)", "Limit Orders + Tol Check", "ACTIVE"],
        ["Internet Outage", "Med (5%)", "High (Unmanaged)", "VPS + Auto-Reconnect", "PARTIAL"],
        ["API Rate Limit", "Med (10%)", "Low (No Logs)", "Exponential Backoff", "ACTIVE"],
        ["Correlation Fail", "Low (2%)", "High (Drawdown)", "Code Logic Check", "ACTIVE"],
    ]
    sheets.update_documentation("RISK AUDIT", risk_data)
    
    # 7. GENERATE LANDING PAGE (TOC)
    print("📑 Generating Landing Page...")
    sheets.update_landing_page()
    print("✅ INSTITUTIONAL SYNC COMPLETE")

if __name__ == "__main__":
    sync_documentation()
