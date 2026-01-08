"""
Enhanced Report Generator - Adds Action Plans and Trade Setups
Wrapper around institutional_market_analyst.py
"""

import sys
from pathlib import Path
from datetime import datetime
import re

def generate_action_plan(current_price: float, support: list, resistance: list, bullish_bias: bool) -> str:
    """Generate IF-THEN action plan section"""
    
    plan = f"\n## 🎯 ACTION PLAN\n\n"
    plan += f"**Current Price**: {current_price:.2f}\n\n"
    
    if support and resistance:
        primary_support = support[0]
        primary_resistance = resistance[0]
        
        plan += f"### Decision Tree:\n\n"
        plan += f"**SCENARIO 1**: IF price holds above **{primary_support:.2f}** (Support)\n"
        if bullish_bias:
            plan += f"  → **THEN**: Look for BUY opportunities ✅\n"
            plan += f"  → **Target**: {primary_resistance:.2f}\n"
            plan += f"  → **Stop Loss**: Below {primary_support:.2f}\n"
        else:
            plan += f"  → **THEN**: Range-bound trading 🟡\n"
        plan += "\n"
        
        plan += f"**SCENARIO 2**: IF price breaks above **{primary_resistance:.2f}** (Resistance)\n"
        if bullish_bias:
            plan += f"  → **THEN**: GO LONG aggressively 🚀\n"
            if len(resistance) > 1:
                plan += f"  → **Target**: {resistance[1]:.2f}\n"
            plan += f"  → **Stop Loss**: {primary_resistance:.2f} (previous resistance)\n"
        else:
            plan += f"  → **THEN**: Wait for confirmation ⚠️\n"
        plan += "\n"
        
        plan += f"**SCENARIO 3**: IF price breaks below **{primary_support:.2f}** (Support)\n"
        if not bullish_bias:
            plan += f"  → **THEN**: GO SHORT 📉\n"
            if len(support) > 1:
                plan += f"  → **Target**: {support[1]:.2f}\n"
            plan += f"  → **Stop Loss**: Above {primary_support:.2f}\n"
        else:
            plan += f"  → **THEN**: EXIT LONGS - Trend break ⚠️\n"
            if len(support) > 1:
                plan += f"  → **Watch**: {support[1]:.2f} for reversal\n"
    
    return plan

def generate_trader_recommendations(current_price: float, weekly_bias: str, daily_bias: str,  
                                   support: list, resistance: list) -> str:
    """Generate recommendations for different trader types"""
    
    recs = "\n## 💼 TRADER-SPECIFIC RECOMMENDATIONS\n\n"
    
    # Position Traders
    recs += "### 📊 Position Traders (Weekly/Daily)\n\n"
    if 'BUY' in weekly_bias:
        recs += "- **Bias**: BULLISH ✅\n"
        recs += f"- **Action**: HOLD long positions or add on dips to {support[0]:.2f if support else 'support'}\n"
        recs += f"- **Target**: {resistance[0]:.2f if resistance else 'next resistance'}\n"
        recs += "- **Stop**: Major support break\n"
    elif 'SELL' in weekly_bias:
        recs += "- **Bias**: BEARISH ⚠️\n"
        recs += "- **Action**: HOLD short positions or add on rallies\n"
        recs += "- **Stop**: Major resistance break\n"
    else:
        recs += "- **Bias**: NEUTRAL 🟡\n"
        recs += "- **Action**: Wait for clearer directional bias\n"
    recs += "\n"
    
    # Swing Traders
    recs += "### 🎯 Swing Traders (4H/1H)\n\n"
    if 'BUY' in daily_bias:
        recs += "- **Strategy**: Buy dips to support zones\n"
        if support:
            recs += f"- **Entry Zone**: {support[0]:.2f} - {support[1]:.2f if len(support) > 1 else support[0] * 0.99:.2f}\n"
        if resistance:
            recs += f"- **Target**: {resistance[0]:.2f}\n"
        recs += "- **Hold Time**: 2-5 days\n"
    else:
        recs += "- **Strategy**: Sell rallies to resistance\n"
        recs += "- **Hold Time**: 2-5 days\n"
    recs += "\n"
    
    # Day Traders
    recs += "### ⚡ Day Traders (1H/15M/5M)\n\n"
    recs += "- **Strategy**: Trade the range or momentum\n"
    if support and resistance:
        recs += f"- **Range**: {support[0]:.2f} - {resistance[0]:.2f}\n"
        recs += f"- **Scalp BUY**: Near {support[0]:.2f} → Target {current_price:.2f}\n"
        recs += f"- **Scalp SELL**: Near {resistance[0]:.2f} → Target {current_price:.2f}\n"
    recs += "- **Breakout**: Watch for range break, trade with momentum\n"
    recs += "- **Hold Time**: Minutes to hours\n"
    
    return recs

def generate_trade_setups(current_price: float, support: list, resistance: list, bullish_bias: bool) -> str:
    """Generate ready-to-trade setups with R:R"""
    
    setups = "\n## 📈 READY-TO-TRADE SETUPS\n\n"
    
    if not support or not resistance:
        setups += "*No clear setups identified. Wait for better structure.*\n"
        return setups
    
    setup_count = 0
    
    # Setup 1: Pullback Entry
    if bullish_bias and len(support) >= 1:
        entry = support[0]
        sl = support[1] if len(support) > 1 else entry * 0.99
        tp = resistance[0]
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = reward / risk if risk > 0 else 0
        
        if rr >= 1.5:
            setup_count += 1
            setups += f"### Setup #{setup_count}: 🟢 Bullish Pullback Entry\n\n"
            setups += f"- **Type**: BUY LIMIT\n"
            setups += f"- **Entry Zone**: {entry:.2f}\n"
            setups += f"- **Stop Loss**: {sl:.2f}\n"
            setups += f"- **Take Profit**: {tp:.2f}\n"
            setups += f"- **Risk/Reward**: {rr:.1f}:1 ✅\n"
            setups += f"- **Strategy**: Wait for price to pull back to {entry:.2f}, then BUY\n"
            setups += f"- **Invalidation**: Break below {sl:.2f}\n\n"
    
    # Setup 2: Breakout Entry
    if len(resistance) >= 1:
        breakout_level = resistance[0]
        sl = current_price if bullish_bias else resistance[1] if len(resistance) > 1 else breakout_level * 1.01
        tp = resistance[1] if len(resistance) > 1 else breakout_level * 1.02
        risk = abs(breakout_level - sl)
        reward = abs(tp - breakout_level)
        rr = reward / risk if risk > 0 else 0
        
        if rr >= 1.0 and bullish_bias:
            setup_count += 1
            setups += f"### Setup #{setup_count}: ⚡ Breakout Entry\n\n"
            setups += f"- **Type**: BUY STOP\n"
            setups += f"- **Entry**: {breakout_level:.2f} (on break)\n"
            setups += f"- **Stop Loss**: {sl:.2f}\n"
            setups += f"- **Take Profit**: {tp:.2f}\n"
            setups += f"- **Risk/Reward**: {rr:.1f}:1\n"
            setups += f"- **Strategy**: IF price breaks above {breakout_level:.2f} with strong candle, GO LONG\n"
            setups += f"- **Confirmation**: Close above {breakout_level:.2f} + volume surge\n\n"
    
    if setup_count == 0:
        setups += "*No high-probability setups with favorable R:R at this time.*\n"
    
    return setups

def enhance_report(report_path: str):
    """Add enhanced sections to existing report"""
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract key information from report
    current_price_match = re.search(r'\*\*Current Price\*\*: ([\d.]+)', content)
    current_price = float(current_price_match.group(1)) if current_price_match else 0
    
    # Extract bias
    weekly_match = re.search(r'\*\*Weekly\*\*: (.*?)\\n', content)
    daily_match = re.search(r'\*\*Daily\*\*: (.*?)\\n', content)
    weekly_bias = weekly_match.group(1) if weekly_match else ''
    daily_bias = daily_match.group(1) if daily_match else ''
    
    bullish_bias = 'BUY' in weekly_bias or 'BUY' in daily_bias
    
    # Extract support/resistance
    resistance_match = re.search(r'\*\*Resistance\*\*: ([\d., →]+)', content)
    support_match = re.search(r'\*\*Support\*\*: ([\d., →]+)', content)
    
    resistance = []
    support = []
    
    if resistance_match:
        resistance = [float(r.strip()) for r in resistance_match.group(1).replace('→', ',').split(',') if r.strip().replace('.', '').isdigit()]
    
    if support_match:
        support = [float(s.strip()) for s in support_match.group(1).replace('→', ',').split(',') if s.strip().replace('.', '').isdigit()]
    
    # Generate new sections
    action_plan = generate_action_plan(current_price, support, resistance, bullish_bias)
    trade_setups = generate_trade_setups(current_price, support, resistance, bullish_bias)
    trader_recs = generate_trader_recommendations(current_price, weekly_bias, daily_bias, support, resistance)
    
    # Insert before the final timestamp
    timestamp_pos = content.rfind('*Analysis generated by')
    
    if timestamp_pos > 0:
        enhanced_content = content[:timestamp_pos] + action_plan + trader_recs + trade_setups + "\n---\n\n" + content[timestamp_pos:]
    else:
        enhanced_content = content + action_plan + trader_recs + trade_setups
    
    # Save enhanced report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"✅ Enhanced report saved with Action Plans and Trade Setups!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhance_report.py <report_file_path>")
        sys.exit(1)
    
    enhance_report(sys.argv[1])
