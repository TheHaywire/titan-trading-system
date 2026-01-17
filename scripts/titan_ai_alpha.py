"""
TITAN AI ALPHA: THE ULTIMATE INSTITUTIONAL ORCHESTRATOR
======================================================
Mission: Recon → Intel → Thesis → Seeded Execution
Power: Multi-Model AI (Flash + Pro) + Unified Engine Handover
"""

import sys
import os
import json
import asyncio
import argparse
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import google.generativeai as genai

from config.settings import settings
from titan_system.core.recon import MarketRecon
from titan_system.analytics.ai_analyst import AIAnalyst
from titan_system.core.symbol_mapper import mapper

# --- INSTITUTIONAL SKILL IMPORTS ---
# We point to the scripts directly for modular execution
SKILLS = {
    "infra": ".agent/skills/mt5_bridge/scripts/connectivity_manager.py",
    "heartbeat": ".agent/skills/mt5_bridge/scripts/heartbeat_monitor.py",
    "data_audit": ".agent/skills/data_intelligence/scripts/data_auditor.py",
    "macro": ".agent/skills/data_intelligence/scripts/macro_context.py",
    "regime": ".agent/skills/alpha_research/scripts/regime_scout.py",
    "risk": ".agent/skills/factor_risk/scripts/dynamic_kelly_allocator.py",
    "audit_trail": ".agent/skills/mt5_bridge/scripts/audit_trail_manager.py"
}

def run_skill_module(script_path, *args):
    """Bridge to modular Agent Skills."""
    import subprocess
    try:
        cmd = [sys.executable, script_path] + list(args)
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
    return {"status": "FAILED"}

# --- CONFIGURATION ---
MODELS = {
    "recon": "gemini-2.5-flash",
    "intel": "gemini-2.5-flash",
    "strategy": "gemini-2.5-flash"  # Fallback to Flash for reliability
}

class TitanAIAlpha:
    def __init__(self, mode='paper'):
        self.mode = mode
        self.recon_engine = MarketRecon()
        self.ai_analyst = AIAnalyst()
        self.output_dir = "analysis/titan_alpha"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize GenAI
        api_key = getattr(settings, 'google_api_key', None) or os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
        else:
            print("❌ MISSING GOOGLE_API_KEY")

    async def discover_opportunities(self):
        """Stage 1: Reconnaissance (Flash Model)"""
        print("\n🔍 STAGE 1: RECONNAISSANCE (AI DISCOVERY)")
        if not self.recon_engine.connect():
            return []
        
        # For this script, we use a curated fast-scan list
        watchlist = ["GOLD", "SILVER", "BTCUSD", "ETHUSD", "US100", "EURUSD", "GBPUSD", "USDJPY"]
        print(f"Scanning Universe: {', '.join(watchlist)}")
        
        # Fetch basic stats for ranking
        opportunities = []
        for symbol in watchlist:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 10)
            if rates is not None:
                df = pd.DataFrame(rates)
                change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
                opportunities.append({
                    "symbol": symbol,
                    "change": abs(change),
                    "raw_change": change
                })
        
        # Sort by volatility/magnitude
        opportunities.sort(key=lambda x: x['change'], reverse=True)
        top_3 = opportunities[:3]
        print(f"✅ Top 3 Opportunities: {[o['symbol'] for o in top_3]}")
        return top_3

    async def build_intel_profile(self, symbol):
        """Stage 2: Technical Intelligence (Flash Model)"""
        print(f"\n📊 STAGE 2: BUILDING INTEL FOR {symbol} (QUANT ANALYTICS)")
        # This calls the existing analyst logic but we'll simulate the report path
        # In a real impl, we'd call InstitutionalMarketAnalyst directly
        import subprocess
        
        cmd = [sys.executable, "scripts/institutional_market_analyst.py", symbol]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"❌ Sub-analyst failed for {symbol}: {stderr.decode()[:200]}")
            return None
            
        report_path = None
        for line in stdout.decode().split('\n'):
            if "REPORT_PATH:" in line:
                report_path = line.split("REPORT_PATH:")[1].strip()
        
        return report_path

    async def synthesize_strategy(self, symbol, tech_report_path):
        """Stage 3: Executive Thesis (Pro/Flash Model)"""
        print(f"\n🧠 STAGE 3: EXECUTIVE STRATEGY SYNTHESIS (PROMPT v2.0)")
        
        if not tech_report_path or not os.path.exists(tech_report_path):
            return {"status": "ERROR", "reason": "No technical report"}

        with open(tech_report_path, 'r', encoding='utf-8') as f:
            tech_data = f.read()

        # Load Prompt Template
        prompt_path = "scripts/prompts/institutional_strategy_v3_cot.txt"
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
            prompt = template.replace("{{symbol}}", symbol).replace("{{tech_data}}", tech_data)
        else:
            print("⚠️ v3 CoT Prompt template not found, using v2 fallback")
            prompt_path = "scripts/prompts/institutional_strategy_v2.txt"
            # ... (re-load v2 if needed)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().replace("{{symbol}}", symbol).replace("{{tech_data}}", tech_data)

        model = genai.GenerativeModel(MODELS["strategy"])
        
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            full_text = response.text
            
            # Extract JSON mandate from response
            json_match = re.search(r"```json\n(.*?)\n```", full_text, re.DOTALL)
            if json_match:
                strategy_json = json.loads(json_match.group(1))
                strategy_json["raw_cot"] = full_text.split("```json")[0].strip()
                return strategy_json
            else:
                return json.loads(full_text) # Fallback if raw
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    async def generate_mission_report(self, symbol, tech_report_path, strategy_json):
        """Stage 4: Unified Mission Reporting"""
        print(f"\n📄 STAGE 4: GENERATING UNIFIED MISSION REPORT")
        
        tech_data = "No technical data available."
        if tech_report_path and os.path.exists(tech_report_path):
            with open(tech_report_path, 'r', encoding='utf-8') as f:
                tech_data = f.read()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/{symbol}_MISSION_REPORT_{timestamp}.md"
        
        report_content = f"""# 🔱 TITAN ALPHA MISSION REPORT: {symbol}
**Mission Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Status**: SEEDED FOR EXECUTION ({strategy_json.get('bias', 'NEUTRAL')})

{strategy_json.get('raw_cot', 'No strategic reasoning provided.')}

---

## 🧠 EXECUTIVE THESIS: {strategy_json.get('identity', 'Standard Setup')}
{strategy_json.get('thesis', 'No thesis generated.')}

### 🎯 EXECUTION PARAMETERS
| Parameter | Value |
|-----------|-------|
| **Direction** | {strategy_json.get('bias', 'N/A')} |
| **Entry Zone** | {strategy_json.get('execution', {}).get('entry', 'N/A')} |
| **Stop Loss** | {strategy_json.get('execution', {}).get('sl', 'N/A')} |
| **Take Profit 1** | {strategy_json.get('execution', {}).get('tp1', 'N/A')} |
| **Take Profit 2** | {strategy_json.get('execution', {}).get('tp2', 'N/A')} |
| **Risk Multiplier** | {strategy_json.get('execution', {}).get('risk_multiplier', '1.0')}x |

### ⚡ THE DEVIL'S ADVOCATE
> [!WARNING]
> {strategy_json.get('the_devils_advocate', 'No opposing argument identified.')}

---

## 📊 TECHNICAL INTELLIGENCE DATA
{tech_data}

---
*Generated by Titan AI Alpha v2.0 | Multi-Model Stack (Flash + Pro)*
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Unified Mission Report saved: {filename}")
        return filename

    async def seeded_execution(self, symbol, strategy_json, report_path):
        """Stage 5: Automated Handover (The Seed)"""
        print(f"\n🚀 STAGE 5: SEEDED EXECUTION HANDOVER")
        
        if strategy_json.get("quality_score", 0) < 70:
            print(f"⚠️ SKIP: Quality Score too low ({strategy_json.get('quality_score')})")
            run_skill_module(SKILLS["audit_trail"], "TITAN_EXECUTION", "Trade Reject", "LOW_QUALITY", f"Score: {strategy_json.get('quality_score')}")
            return False

        # 1. Risk Desk: Dynamic Sizing (Risk Skill)
        print("🛡️ Calculating Institutional Sizing...")
        risk_data = run_skill_module(SKILLS["risk"]) # Symbol is hashed in script for now, but we could extend
        suggested_lots = risk_data.get("suggested_lots", 0.1)
        
        print(f"💎 SEEDING {symbol} {strategy_json['bias']} | Vol: {suggested_lots} Lots...")
        
        # Persistence
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        thesis_file = f"{self.output_dir}/{symbol}_THESIS_{timestamp}.json"
        with open(thesis_file, 'w') as f:
            json.dump(strategy_json, f, indent=4)
        
        # Log Final Intent to Audit Trail
        run_skill_module(SKILLS["audit_trail"], "TITAN_EXECUTION", "Trade Seeded", "SUCCESS", json.dumps({
            "symbol": symbol,
            "lots": suggested_lots,
            "bias": strategy_json['bias'],
            "regime": strategy_json.get("market_regime")
        }))
        
        print(f"✨ EXECUTION ACTION: {strategy_json['bias']} {symbol} | Lots: {suggested_lots}")
        print(f"📑 THESIS PERSISTED: {thesis_file}")
        
        return True

    async def run_full_pipeline(self, target_symbol=None):
        """Run the end-to-end Alpha Workflow"""
        print("="*60)
        print(f"🚀 TITAN AI ALPHA MISSION STARTED | {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. MT5 Bridge Health Check (Infrastructure Skill)
        print("🌉 Verifying Institutional Bridge...")
        health = run_skill_module(SKILLS["infra"])
        if health.get("status") != "CONNECTED":
            print(f"❌ BRIDGE OFFLINE: {health}")
            return
        
        # Log to Institutional Audit Trail
        run_skill_module(SKILLS["audit_trail"], "TITAN_ORCHESTRATOR", "Mission Start", "SUCCESS", json.dumps({"target": target_symbol or "FULL_SCAN"}))
        
        # 2. Recon
        if target_symbol:
            # Standardize naming immediately
            if not mt5.initialize():
                print("❌ Failed to initialize MT5 for symbol resolution")
                return
            
            sym_clean = target_symbol.upper()
            all_syms = [s.name for s in mt5.symbols_get() or []]
            resolved_sym = next((s for s in all_syms if s.upper() == sym_clean or s.upper() == f"{sym_clean}CASH"), target_symbol)
            
            print(f"✅ Target: {target_symbol} -> Resolved: {resolved_sym}")
            opportunities = [{"symbol": resolved_sym}]
        else:
            opportunities = await self.discover_opportunities()
        
        for opp in opportunities:
            symbol = opp['symbol']
            
            # 2. Data Intelligence (Department check)
            print(f"📊 Auditing {symbol} Data Physics...")
            data_audit = run_skill_module(SKILLS["data_audit"])
            macro_audit = run_skill_module(SKILLS["macro"], symbol)
            
            if macro_audit.get("verdict") == "BLOCK":
                print(f"🛑 MACRO BLOCK: Skipping {symbol} due to {macro_audit.get('active_threats')}")
                continue
                
            # 3. Alpha Research (Regime Alignment)
            print(f"🔬 Identifying {symbol} Market Regime...")
            regime = run_skill_module(SKILLS["regime"])
            opp["regime"] = regime.get("regime")
            
            # 4. Intel Profile
            report_path = await self.build_intel_profile(symbol)
            
            # 5. Strategy Thesis
            strategy = await self.synthesize_strategy(symbol, report_path)
            
            # Add regime context to strategy for report
            strategy["market_regime"] = regime.get("regime", "UNKNOWN")
            
            # 6. Mission Report
            if "thesis" in strategy:
                mission_report = await self.generate_mission_report(symbol, report_path, strategy)
                
                # 7. Execution Handover (with Risk Sizing)
                await self.seeded_execution(symbol, strategy, mission_report)
            else:
                print(f"❌ AI Strategy failed for {symbol}: {strategy.get('reason')}")

        print("\n" + "="*60)
        print("🏁 TITAN AI ALPHA MISSION COMPLETE")
        print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, help='Target symbol (optional)')
    parser.add_argument('--mode', type=str, default='paper', choices=['live', 'paper'])
    args = parser.parse_args()

    titan = TitanAIAlpha(mode=args.mode)
    asyncio.run(titan.run_full_pipeline(args.symbol))
