"""
Titan Morning Review: AI Performance Synthesis
==============================================
Analyzes institutional decisions and outcomes to find 
unseen patterns and refine the autonomous strategy.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

DB_PATH = "data/alpha_feedback.db"

def init_gemini():
    api_key = getattr(settings, 'google_api_key', None) or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    # Use Gemma-3-27b for high token limit reviews
    return genai.GenerativeModel('models/gemma-3-27b-it')

def get_recent_decisions(days: int = 1) -> str:
    """Fetch all sentinel decisions from the database."""
    if not os.path.exists(DB_PATH):
        return "No decision data found."
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    since = (datetime.now() - timedelta(days=days)).isoformat()
    c.execute("SELECT * FROM ai_decisions WHERE timestamp > ? ORDER BY timestamp DESC", (since,))
    rows = c.fetchall()
    
    if not rows:
        return "No recent decisions to analyze."
        
    report = []
    for r in rows:
        # Don't include huge JSON blobs in the AI prompt to save context
        summary = (
            f"[{r['timestamp'][:16]}] {r['symbol']}: {r['decision']} | "
            f"Regime: {r['regime']} (Conf: {r['confidence']}) | "
            f"Alpha: {r['alpha_score']} | Reasoning: {r['reasoning']}"
        )
        report.append(summary)
        
    conn.close()
    return "\n".join(report)

def run_morning_review():
    print("🌅 Starting Titan Morning Review...")
    
    model = init_gemini()
    if not model:
        print("❌ Gemini/Gemma initialization failed.")
        return

    # 1. Gather data
    decision_log = get_recent_decisions(days=2) # Review last 48 hours for context
    
    # 2. Build Prompt
    prompt = f"""
    You are the 'Titan Chief Strategy Officer'. Your goal is to review the decisions made by the 
    Autonomous Sentinel and find patterns that need optimization.
    
    DECISION LOG (Last 48 Hours):
    ---
    {decision_log}
    ---
    
    TASKS:
    1. SUMMARY: How many symbols were scanned and how many were rejected?
    2. REJECTION PATTERNS: Are we being too strict? Or too loose? 
       (e.g., Is News/Technical Mismatch causing us to miss good trends?)
    3. ALPHA EFFICIENCY: Which symbols are consistently showing the best 'Alpha Efficiency'? 
    4. ACTIONABLE IMPROVEMENTS: Suggest one specific threshold to adjust 
       (e.g., 'Lower alpha requirement for BTCUSD during Asian session' or 'Increase confidence gate for US100').
    
    Output a professional markdown report.
    """
    
    try:
        print("🤔 AI is analyzing the performance patterns...")
        response = model.generate_content(prompt)
        report = response.text
        
        # Save Report
        date_str = datetime.now().strftime('%Y-%m-%d')
        report_path = f"analysis/MORNING_REVIEW_{date_str}.md"
        os.makedirs("analysis", exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 🌅 TITAN MORNING REVIEW: {date_str}\n\n")
            f.write(report)
            
        print(f"✅ Morning Review complete! Report: {report_path}")
        return report_path
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

if __name__ == "__main__":
    run_morning_review()
