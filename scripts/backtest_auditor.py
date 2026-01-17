"""
Titan AI Backtest Auditor
=========================
Uses Gemini to perform a deep forensic audit on backtest data 
to identify which filters are working and which are failing.
"""

import os
import sys
import json
from datetime import datetime
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

def init_gemini():
    api_key = getattr(settings, 'google_api_key', None) or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('models/gemma-3-27b-it')

def audit_backtest(file_path: str):
    print(f"🕵️ AI is auditing backtest: {file_path}")
    
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print(f"⚠️ Skipping empty or missing file: {file_path}")
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON: {file_path}")
        return

    model = init_gemini()
    if not model:
        return

    prompt = f"""
    You are the 'Titan Quantitative Auditor'. Analyze this backtest data 
    and identify the CRITICAL FAILURE POINTS in the current logic.
    
    BACKTEST DATA (Symbol: {data['symbol']}, Win Rate: {data['win_rate']}%):
    ---
    {json.dumps(data['trades'], indent=2)}
    ---
    
    TASKS:
    1. LOSS ANALYSIS: What is the most common reason for the LOSSES in this data? 
       (e.g., Are we entering too early? Is the 'Regime' lagging?)
    2. REGIME ACCURACY: Does the 'TRENDING_BULLISH/BEARISH' label actually lead to wins?
    3. WINNING PATTERN: Describe the 'Perfect Setup' found in the Winning trades.
    4. SYSTEM ADJUSTMENT: Suggest one specific change to the Sentinel logic 
       (e.g., 'Add a 2-bar confirmation' or 'Ignore ADX < 30').
    
    Output a hard-hitting institutional audit report.
    """
    
    try:
        response = model.generate_content(prompt)
        report = response.text
        
        # Save Report
        audit_path = file_path.replace(".json", "_AI_AUDIT.md")
        with open(audit_path, "w", encoding="utf-8") as f:
            f.write(f"# 🕵️ AI STRATEGIC AUDIT: {data['symbol']}\n")
            f.write(f"Source: {file_path}\n\n")
            f.write(report)
            
        print(f"✅ AI Audit Complete: {audit_path}")
        return audit_path
        
    except Exception as e:
        print(f"❌ AI Audit failed: {e}")
        return None

if __name__ == "__main__":
    # Audit all recent backtests
    import glob
    files = glob.glob("analysis/BACKTEST_*.json")
    for f in files:
        if "AI_AUDIT" not in f:
            audit_backtest(f)
