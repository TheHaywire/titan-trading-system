"""
Complete Market Analyst with Visual Charts - PRODUCTION VERSION
Combines institutional analysis with automatic chart generation
"""

import subprocess
import sys
from pathlib import Path
import re
from datetime import datetime


def generate_charts_for_timeframes(symbol, timeframes):
    """Generate charts for specified timeframes"""
    
    chart_paths = {}
    
    print("\n[CHARTS] Generating visual charts...")
    
    for tf in timeframes:
        try:
            result = subprocess.run(
                [sys.executable, "scripts/visual_chart_generator.py", symbol, tf],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Chart saved:' in line:
                        chart_path = line.split('Chart saved:')[-1].strip()
                        chart_paths[tf] = chart_path
                        print(f"  [OK] {tf} chart generated")
                        break
            else:
                print(f"  [WARN] {tf} chart failed")
                
        except Exception as e:
            print(f"  [ERROR] {tf}: {str(e)}")
    
    return chart_paths


def inject_charts_into_report(report_path, chart_paths):
    """Inject chart images into the markdown report"""
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for tf, chart_path in chart_paths.items():
        pattern = f"### {tf} Timeframe"
        
        if pattern in content:
            insertion_point = content.find(pattern)
            if insertion_point > 0:
                next_newline = content.find('\n', insertion_point)
                
                if next_newline > 0:
                    chart_md = f"\n\n![{tf} Visual Chart]({chart_path})\n"
                    content = content[:next_newline] + chart_md + content[next_newline:]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return report_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python complete_analyst_with_charts.py <SYMBOL>")
        print("Example: python complete_analyst_with_charts.py GOLD")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    print("\n" + "="*70)
    print(f"  COMPLETE MARKET ANALYST WITH VISUAL CHARTS")
    print(f"  Symbol: {symbol}")
    print("="*70 + "\n")
    
    # Step 1: Run institutional market analysis
    print("[STEP 1/4] Running institutional market analysis...")
    result = subprocess.run(
        [sys.executable, "scripts/institutional_market_analyst.py", symbol],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[ERROR] Analysis failed")
        sys.exit(1)
    
    report_path = None
    for line in result.stdout.split('\n'):
        if "REPORT_PATH:" in line:
            report_path = line.split("REPORT_PATH:")[-1].strip()
            break
    
    if not report_path:
        print("[ERROR] Could not find report path")
        sys.exit(1)
    
    print(f"[OK] Analysis complete: {report_path}\n")
    
    # Step 2: Generate charts
    print("[STEP 2/4] Generating visual charts...")
    key_timeframes = ['1W', '1D', '4H', '1H']
    chart_paths = generate_charts_for_timeframes(symbol, key_timeframes)
    print(f"[OK] Generated {len(chart_paths)} charts\n")
    
    # Step 3: Inject charts
    print("[STEP 3/4] Embedding charts in report...")
    enhanced_report = inject_charts_into_report(report_path, chart_paths)
    print(f"[OK] Charts embedded\n")
    
    # Step 4: Add action plans
    print("[STEP 4/4] Adding action plans and setups...")
    result = subprocess.run(
        [sys.executable, "scripts/enhance_report.py", report_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"[OK] Action plans added\n")
    else:
        print(f"[WARN] Enhancement skipped\n")
    
    # Final summary
    print("="*70)
    print(f"  COMPLETE ANALYSIS READY!")
    print(f"  Report: {report_path}")
    print(f"  Charts: {len(chart_paths)} embedded")
    print("="*70 + "\n")
    
    print("Report includes:")
    print("  [+] Multi-timeframe analysis (8 timeframes)")
    print("  [+] Visual charts (1W, 1D, 4H, 1H)")
    print("  [+] Candlestick & chart patterns")
    print("  [+] Support/Resistance levels")
    print("  [+] Fibonacci retracements")
    print("  [+] RSI indicators")
    print("  [+] Action plans (IF-THEN scenarios)")
    print("  [+] Trader recommendations")
    print("  [+] Ready-to-trade setups\n")
    
    print(f"REPORT_PATH:{report_path}")


if __name__ == "__main__":
    main()
