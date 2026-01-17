"""
Ultimate Trade Setup Generator v4.0
Orchestrates Professional Analyst v2, TA-Lib Profiler v3, and Visual Charts.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import time

def run_step(name, cmd):
    print(f"🚀 [STEP] {name}...")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print(f"❌ {name} failed in {duration:.1f}s")
        print(f"Error: {result.stderr}")
        return None, None
    
    # Extract path if available
    path = None
    if result.stdout:
        for line in result.stdout.split('\n'):
            if "REPORT_PATH:" in line or "INTEL_PATH:" in line or "INTEL_PATH:" in line:
                path = line.split(":")[-1].strip()
                break
    
    print(f"✅ {name} complete in {duration:.1f}s")
    return path, result.stdout

def inject_media(report_path, symbol):
    """Inject charts and profiler links into the primary report"""
    if not report_path or not Path(report_path).exists():
        return
        
    print("🎨 Injecting visual evidence and deep intelligence...")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define chart markers in v2 report
    markers = {
        '1W': '## 🎯 MACRO VIEW - WEEKLY (1W)',
        '1D': '## 📊 DAILY (1D) - BIAS CONFIRMATION',
        '4H': '## ⏰ 4-HOUR (4H) - STRUCTURE ANALYSIS',
        '1H': '## 📈 1-MINUTE (1M)' # Corrected marker for local trend charts
    }

    # Generate and link charts
    for tf, marker in markers.items():
        chart_cmd = [sys.executable, "scripts/visual_chart_generator.py", symbol, tf]
        subprocess.run(chart_cmd, capture_output=True)
        # Search for the latest chart for this TF
        chart_files = sorted(Path("charts").glob(f"{symbol}_{tf}_*.png"), reverse=True)
        if chart_files:
            # Use relative path for maximum compatibility (e.g., ../charts/xxx.png)
            rel_path = f"../charts/{chart_files[0].name}"
            img_md = f"\n\n![{tf} Chart]({rel_path})\n"
            content = content.replace(marker, f"{marker}{img_md}")

    # Link to TA-Lib Deep Intel
    intel_files = sorted(Path("intelligence").glob(f"{symbol}_TALIB_v3_*.md"), reverse=True)
    if intel_files:
        # Use relative path for compatibility (e.g., ../intelligence/xxx.md)
        rel_path = f"../intelligence/{intel_files[0].name}"
        intel_link = f"\n\n> [!TIP]\n> **DEEP QUANT RESEARCH**: [View Full TA-Lib Profiler Report (150+ Indicators)]({rel_path})\n"
        # Insert after header
        first_newline = content.find('\n')
        content = content[:first_newline] + intel_link + content[first_newline:]

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python ultimate_setup_generator.py <SYMBOL>")
        sys.exit(1)
        
    symbol = sys.argv[1].upper()
    print(f"\n{'='*70}\n  👑 ULTIMATE TRADE SETUP GENERATOR v4.0\n  Target: {symbol}\n{'='*70}\n")

    # 1. Run Professional Analyst v2.0
    report_path, _ = run_step("Professional MTF Analyst v2.0", 
                            [sys.executable, "scripts/institutional_market_analyst_v2.py", symbol])
    
    # 2. Run TA-Lib Profiler v3.0 (Parallel/Sequential for stability)
    run_step("TA-Lib Deep Profiler v3.0", 
             [sys.executable, "scripts/symbol_profiler_v3.py", symbol])
    
    # 3. Enhance with Visual Charts and Links
    inject_media(report_path, symbol)
    
    # 4. Final Polish with Action Plans
    if report_path:
        run_step("Action Plan Enhancement", 
                 [sys.executable, "scripts/enhance_report.py", report_path])

    print(f"\n{'='*70}\n🏆 ULTIMATE SETUP READY: {report_path}\n{'='*70}\n")
    print(f"REPORT_PATH:{report_path}")

if __name__ == "__main__":
    main()
