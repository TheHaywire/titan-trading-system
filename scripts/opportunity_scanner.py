"""
Institutional Real-Time Opportunity Scanner
Runs multi-symbol analysis in parallel and ranks best trading setups.
"""

import os
import sys
import subprocess
import re
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import watchlist
try:
    from scanner_watchlist import WATCHLIST, MIN_SCORE_THRESHOLD, MAX_CONCURRENT_SCANS
except ImportError:
    WATCHLIST = ["GOLD", "SILVER", "BTCUSD", "EURUSD"]
    MIN_SCORE_THRESHOLD = 3.0
    MAX_CONCURRENT_SCANS = 3

def analyze_symbol(symbol):
    """Run fresh institutional analysis for a symbol"""
    print(f"🔍 Starting real-time analysis for {symbol}...")
    
    try:
        # Use PowerShell to handle encoding issues on Windows
        ps_command = f"$env:PYTHONIOENCODING='utf-8'; python scripts/institutional_market_analyst.py {symbol}"
        
        start_time = time.time()
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120  # Analysis can take a while for 8 timeframes
        )
        duration = time.time() - start_time
        
        if result.returncode != 0:
            print(f"❌ {symbol} failed after {duration:.1f}s: {result.stderr.strip()}")
            return None
        
        # Extract report path
        report_path = None
        for line in result.stdout.split('\n'):
            if "REPORT_PATH:" in line:
                report_path = line.split("REPORT_PATH:")[-1].strip()
                break
        
        if not report_path or not Path(report_path).exists():
            print(f"⚠️  {symbol}: Analysis finished but report not found.")
            return None
            
        print(f"✅ {symbol}: Analysis complete ({duration:.1f}s)")
        return parse_report(symbol, report_path)
        
    except Exception as e:
        print(f"💥 {symbol}: Unexpected error: {str(e)}")
        return None

def parse_report(symbol, report_path):
    """Extract key metrics from the generated markdown report"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract current price
        price_match = re.search(r'\*\*Current Price\*\*: ([\d.]+)', content)
        current_price = float(price_match.group(1)) if price_match else 0.0
        
        # Extract 24H change
        change_match = re.search(r'\*\*24H Change\*\*: ([+\-\d.]+)%', content)
        change_24h = float(change_match.group(1)) if change_match else 0.0
        
        # Extract signals for key timeframes
        def get_signal(content, tf):
            # Look for the row in the executive summary table
            # | **1H** | 🟢 STRONG UPTREND | 68.7 | 61.4 | ...
            pattern = rf'\| \*\*{tf}\*\* \| (.*?) \|'
            match = re.search(pattern, content)
            if match:
                return match.group(1).split('|')[0].strip()
            return "NEUTRAL"

        weekly_sig = get_signal(content, "1W")
        daily_sig = get_signal(content, "1D")
        h4_sig = get_signal(content, "4H")
        
        # Calculate Score (0-10)
        score = 0
        reasons = []
        
        # 1. Trend Alignment (up to 4 points)
        bullish_count = sum(1 for s in [weekly_sig, daily_sig, h4_sig] if "UPTREND" in s or "BUY" in s)
        bearish_count = sum(1 for s in [weekly_sig, daily_sig, h4_sig] if "DOWNTREND" in s or "SELL" in s)
        
        market_bias = "NEUTRAL"
        if bullish_count >= 2:
            market_bias = "BULLISH"
            score += 4 if bullish_count == 3 else 2
            reasons.append(f"{'Perfect' if bullish_count==3 else 'Moderate'} Bullish Alignment")
        elif bearish_count >= 2:
            market_bias = "BEARISH"
            score += 4 if bearish_count == 3 else 2
            reasons.append(f"{'Perfect' if bearish_count==3 else 'Moderate'} Bearish Alignment")
            
        # 2. Confluence Zones (up to 3 points)
        zones = re.findall(r'\| \*\*([\d.]+)\*\* \| (\d+) \|', content)
        if zones:
            max_confluence = max(int(z[1]) for z in zones)
            if max_confluence >= 4:
                score += 3
                reasons.append(f"Institutional Confluence Zone ({max_confluence} TFs)")
            elif max_confluence >= 2:
                score += 1
                reasons.append(f"Minor Confluence Zone ({max_confluence} TFs)")
                
        # 3. Patterns (up to 3 points)
        if market_bias == "BULLISH" and any(p in content for p in ["PENNANT", "TRIANGLE", "FLAG", "DOUBLE BOTTOM", "HAMMER"]):
            score += 3
            reasons.append("Bullish Continuity/Reversal Pattern")
        elif market_bias == "BEARISH" and any(p in content for p in ["PENNANT", "TRIANGLE", "FLAG", "DOUBLE TOP", "SHOOTING STAR"]):
            score += 3
            reasons.append("Bearish Continuity/Reversal Pattern")
            
        # 4. Divergence (Alignment check - IMPORTANT)
        div_section = content.split("## 🎯 CONFLUENCE")[0]
        if "BULLISH DIVERGENCE" in div_section:
            if market_bias == "BULLISH":
                score += 2
                reasons.append("Bullish Momentum Divergence (Confirmation)")
            else:
                score -= 4
                reasons.append("WARNING: Bearish Trend with Bullish Divergence")
        elif "BEARISH DIVERGENCE" in div_section:
            if market_bias == "BEARISH":
                score += 2
                reasons.append("Bearish Momentum Divergence (Confirmation)")
            else:
                score -= 4
                reasons.append("WARNING: Bullish Trend with Bearish Divergence")

        # 5. Overbought/Oversold Caution (-2 points if extreme)
        if market_bias == "BULLISH" and "⚠️ Overbought" in content:
            score -= 2
            reasons.append("Caution: Bullish Exhaustion (Overbought)")
        elif market_bias == "BEARISH" and "⚠️ Oversold" in content:
            score -= 2
            reasons.append("Caution: Bearish Exhaustion (Oversold)")

        quality = "PREMIUM" if score >= 8 else "HIGH" if score >= 6 else "MEDIUM" if score >= 4 else "LOW"
        emoji = "🏆" if score >= 8 else "✅" if score >= 6 else "🟡" if score >= 4 else "⚠️"

        return {
            "symbol": symbol,
            "score": max(0, score),
            "quality": quality,
            "emoji": emoji,
            "price": current_price,
            "change": change_24h,
            "weekly": weekly_sig,
            "daily": daily_sig,
            "h4": h4_sig,
            "reasons": reasons,
            "report_path": report_path
        }
    except Exception as e:
        print(f"❌ Error parsing {report_path}: {str(e)}")
        return None

def generate_grand_report(opportunities):
    """Create a beautiful markdown summary of all scanned opportunities"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"OPPORTUNITIES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = Path("analysis") / filename
    
    # Sort by score
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    lines = [
        f"# 🌍 REAL-TIME MARKET SCANNER v3.0",
        f"**Generated**: {timestamp}",
        f"**Symbols Scanned**: {len(opportunities)}",
        "",
        "---",
        "",
        "## 🥇 TOP INSTITUTIONAL SETUPS",
        ""
    ]
    
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    for i, opp in enumerate(opportunities[:5]):
        medal = medals[i] if i < len(medals) else "🔹"
        # Relative path is most professional and robust for local markdown reports
        rel_report_path = Path(opp['report_path']).name
        
        lines.append(f"### {medal} {opp['symbol']} — Score: {opp['score']}/10 {opp['emoji']}")
        lines.append(f"**Quality**: {opp['quality']} | **Price**: {opp['price']:.2f} ({opp['change']:+.2f}%)")
        lines.append(f"**Alignment**: {opp['weekly']} | {opp['daily']} | {opp['h4']}")
        lines.append("")
        lines.append("**Key Catalysts:**")
        for reason in opp['reasons']:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append(f"📄 **[View Full Institutional Analysis]({rel_report_path})**")
        lines.append("")
        lines.append("---")
        
    lines.append("")
    lines.append("## 📊 SCANNER SUMMARY TABLE")
    lines.append("")
    lines.append("| Rank | Symbol | Score | Quality | Bias (W/D/H4) | Price | 24H % |")
    lines.append("|------|--------|-------|---------|---------------|-------|-------|")
    
    for i, opp in enumerate(opportunities):
        bias = f"{opp['weekly'].split()[-1]}/{opp['daily'].split()[-1]}/{opp['h4'].split()[-1]}"
        rel_report_path = Path(opp['report_path']).name
        lines.append(f"| {i+1} | [**{opp['symbol']}**]({rel_report_path}) | {opp['score']} | {opp['emoji']} {opp['quality']} | {bias} | {opp['price']:.2f} | {opp['change']:+.2f}% |")
    
    lines.append("")
    lines.append("---")
    lines.append("*Disclaimer: This analysis uses institutional-grade quantitative metrics but does not constitute financial advice.*")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return filepath

def main():
    print("\n" + "🚀" * 30)
    print("  INSTITUTIONAL REAL-TIME SCANNER v3.0")
    print("  Watchlist: " + ", ".join(WATCHLIST))
    print("🚀" * 30 + "\n")
    
    opportunities = []
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SCANS) as executor:
        future_to_symbol = {executor.submit(analyze_symbol, sym): sym for sym in WATCHLIST}
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                data = future.result()
                if data:
                    opportunities.append(data)
            except Exception as exc:
                print(f"❌ {symbol} generated an exception: {exc}")
                
    # Sort by score for logging
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    # Log high-quality setups to performance tracker
    try:
        from performance_tracker import PerformanceTracker
        tracker = PerformanceTracker()
        for opp in opportunities:
            if opp['score'] >= 7:
                # Log to DB
                tracker.log_setup(
                    symbol=opp['symbol'],
                    tf="MTF",
                    signal="BUY" if "BULLISH" in opp['weekly'] or "BUY" in opp['weekly'] else "SELL",
                    price=opp['price'],
                    score=opp['score'],
                    patterns=opp['reasons'],
                    tp=opp['price'] * 1.02 # Nominal 2% TP for tracking
                )
    except Exception as e:
        print(f"⚠️ Could not log setups to performance tracker: {e}")

    # Generate the grand report
    print("\n📊 Aggregating setup intelligence...")
    final_report = generate_grand_report(opportunities)
    
    print("\n" + "🏆" * 30)
    print("  SCANNER COMPLETE")
    print(f"  Grand Report: {final_report}")
    print("🏆" * 30 + "\n")
    
    # Print summary to console
    if opportunities:
        top = opportunities[0]
        print(f"👑 TOP PICK: {top['symbol']} ({top['score']}/10)")
        print(f"💬 REASONING: {', '.join(top['reasons'][:2])}")
    else:
        print("⚠️  No opportunities found in current market conditions.")
    
    print(f"\nREPORT_PATH:{final_report}")

if __name__ == "__main__":
    main()
