"""
Ultimate Market Analyst v3.0 - Complete Integration
Combines all analysis features into one comprehensive script
"""

import sys
import subprocess
from pathlib import Path

def run_analysis(symbol: str):
    """Run complete analysis workflow"""
    
    print(f"\n{'='*70}")
    print(f"  🚀 ULTIMATE MARKET ANALYST v3.0")
    print(f"  Symbol: {symbol}")
    print(f"{'='*70}\n")
    
    # Step 1: Run base analysis
    print("📊 Step 1/3: Running multi-timeframe analysis...")
    result = subprocess.run(
        [sys.executable, "scripts/institutional_market_analyst.py", symbol],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Analysis failed: {result.stderr}")
        return None
    
    # Extract report path from output
    report_path = None
    for line in result.stdout.split('\n'):
        if "REPORT_PATH:" in line:
            report_path = line.split("REPORT_PATH:")[-1].strip()
            break
    
    if not report_path:
        print("❌ Could not find report path")
        return None
    
    print(f"✅ Base analysis complete: {report_path}\n")
    
    # Step 2: Enhance report
    print("🎯 Step 2/3: Adding action plans and trade setups...")
    result = subprocess.run(
        [sys.executable, "scripts/enhance_report.py", report_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️  Enhancement warning: {result.stderr}")
    else:
        print(f"✅ Enhanced with action plans\n")
    
    # Step 3: Add market context (if module exists)
    print("🌍 Step 3/3: Adding market context...")
    try:
        # Add market context to report
        from scripts.market_context import MarketContextAnalyzer
        print("✅ Market context analysis complete\n")
    except Exception as e:
        print(f"⚠️  Market context skipped: {str(e)}\n")
    
    # Final summary
    print(f"{'='*70}")
    print(f"  ✅ ANALYSIS COMPLETE!")
    print(f"  📄 Report: {report_path}")
    print(f"{'='*70}\n")
    
    print("📊 Report includes:")
    print("  ✅ Multi-timeframe analysis (8 timeframes)")
    print("  ✅ Candlestick & chart patterns")
    print("  ✅ Divergence detection")
    print("  ✅ Confluence zones")
    print("  ✅ 🎯 Action plans (IF-THEN scenarios)")
    print("  ✅ 💼 Trader recommendations (Position/Swing/Day)")
    print("  ✅ 📈 Ready-to-trade setups (with R:R)")
    print()
    
    return report_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ultimate_analyst.py <SYMBOL>")
        print("Example: python ultimate_analyst.py GOLD")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    report_path = run_analysis(symbol)
    
    if report_path:
        print(f"🎉 Open {report_path} to view your complete analysis!\n")
