"""
Autonomous Strategy Council (AI-Powered)
========================================
A multi-agent discussion framework powered by Gemini to perfect 
the Autonomous trading architecture.

Agents:
1. THE QUANT - Focuses on statistical edge and mathematical robustness.
2. THE RISK MANAGER - Focuses on capital preservation and exposure.
3. THE EXECUTION SPECIALIST - Focuses on fills, slippage, and API limits.
4. THE REGIME ANALYST - Focuses on market environment and asset selection.
5. THE DEVIL'S ADVOCATE - Focuses on finding flaws and edge cases.
"""

import os
import sys
import json
import time
from typing import List, Dict
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

# Personas
PERSONAS = {
    "quant": {
        "name": "THE QUANT",
        "emoji": "🧮",
        "prompt": "You are a senior Quantitative Researcher at a top-tier hedge fund. Your focus is on the mathematical validity, statistical significance, and algorithmic robustness of trading strategies. Critique the proposed architecture from a math and probability perspective."
    },
    "risk": {
        "name": "THE RISK MANAGER",
        "emoji": "🛡️",
        "prompt": "You are the Head of Risk Management. Your job is to ensure capital preservation. You look for ways the system could fail, blow up, or over-expose the fund. You care about drawdown, leverage, and tail risks. Critique the architecture from a risk perspective."
    },
    "execution": {
        "name": "THE EXECUTION SPECIALIST",
        "emoji": "⚡",
        "prompt": "You are a High-Frequency Trading Execution specialist. You care about latency, spreads, slippage, fill quality, and API constraints. You know how 'paper profits' vanish in real markets. Critique the architecture from an implementation and execution perspective."
    },
    "regime": {
        "name": "THE REGIME ANALYST",
        "emoji": "🌊",
        "prompt": "You are a Macro Strategist who focuses on market regimes (Trend, Range, Volatility, Calm). You know that no single strategy works in all environments. Critique the architecture based on how it handles regime shifts and asset selection."
    },
    "devils_advocate": {
        "name": "THE DEVIL'S ADVOCATE",
        "emoji": "😈",
        "prompt": "Your only job is to break things. You are skeptical of everything. You look for 'too good to be true' scenarios, curve-fitting, and hidden assumptions that lead to catastrophe. Be brutally honest about why this architecture might fail."
    }
}

def init_gemini():
    api_key = getattr(settings, 'google_api_key', None) or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found.")
        sys.exit(1)
    genai.configure(api_key=api_key)
    # Use Gemma-3-27b-it for high limits and intelligence
    return genai.GenerativeModel('models/gemma-3-27b-it')

def get_agent_feedback(model, agent_id: str, proposal: str) -> str:
    persona = PERSONAS[agent_id]
    prompt = f"""
    {persona['prompt']}
    
    Current Proposal for 'Ultimate Autonomous AI Strategy':
    ---
    {proposal}
    ---
    
    Provide your critical assessment in markdown format. 
    Focus on specific strengths and weaknesses from your perspective.
    End with a clear 'VERDICT' (e.g., APPROVED, REJECTED, or CONDITIONAL).
    """
    
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Rate limited. Waiting 10s... (Attempt {attempt+1}/3)")
                time.sleep(10)
                continue
            return f"Error getting feedback: {e}"
    return "Error: Maximum retries exceeded."

def run_council(proposal: str):
    model = init_gemini()
    
    print("\n" + "="*60)
    print("🏛️  TITAN STRATEGY COUNCIL: AUTONOMOUS ARCHITECTURE")
    print("="*60 + "\n")
    
    feedbacks = {}
    
    for agent_id, persona in PERSONAS.items():
        print(f"[{persona['emoji']} {persona['name']}] is thinking...")
        feedback = get_agent_feedback(model, agent_id, proposal)
        feedbacks[agent_id] = feedback
        # Small delay to favor free tier limits if many requests
        time.sleep(2)
    
    # Final Synthesis (The CEO)
    print("[👑 THE CEO/SYNTHESIZER] is finalizing the roadmap...")
    all_feedback_text = "\n\n".join([f"### {PERSONAS[aid]['name']} Feedback\n{f}" for aid, f in feedbacks.items()])
    
    synthesis_prompt = f"""
    You are the Lead Portfolio Manager (CEO) of Titan Trading. 
    You have just received feedback from your 5 specialized departments regarding the new 'Autonomous AI Strategy'.
    
    Proposal:
    {proposal}
    
    Department Analysis:
    {all_feedback_text}
    
    YOUR GOAL:
    1. Synthesize the most critical points.
    2. Resolve any conflicts between departments.
    3. Produce the 'ULTIMATE AUTONOMOUS ROADMAP' which incorporates all necessary fixes and safeguards.
    4. Provide the final architecture design in a standard format.
    
    Produce a professional markdown report.
    """
    
    try:
        synthesis = model.generate_content(synthesis_prompt).text
    except Exception as e:
        synthesis = f"Synthesis Error: {e}"
        
    # Output to File
    report_path = "analysis/TITAN_AUTONOMOUS_COUNCIL_FINAL.md"
    os.makedirs("analysis", exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🏛️ TITAN STRATEGY COUNCIL: FINAL REPORT\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 👑 ULTIMATE ROADMAP: THE CEO'S SYNTHESIS\n\n")
        f.write(synthesis + "\n\n")
        f.write("---")
        f.write("\n\n## 📋 FULL DEPARTMENTAL FEEDBACK\n\n")
        f.write(all_feedback_text)
        
    print(f"\n✅ Council complete! Final Roadmap saved to: {report_path}")
    return report_path

if __name__ == "__main__":
    # Get current proposal
    proposal_path = r"C:\Users\manan\.gemini\antigravity\brain\2ad218f1-ac08-4f05-8c53-6fc7e9568eca\AUTONOMOUS_AI_STRATEGY.md"
    if not os.path.exists(proposal_path):
        print(f"❌ Error: Proposal not found at {proposal_path}")
        sys.exit(1)
        
    with open(proposal_path, "r", encoding="utf-8") as f:
        proposal_content = f.read()
        
    run_council(proposal_content)
