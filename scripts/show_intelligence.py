from titan_system.execution.main_loop import TitanBot
from titan_system.data.ingest_mt5 import ingest_history
from titan_system.research.data_loader import load_data
import logging
from datetime import datetime
import os

# Silence loggers for clean report
logging.getLogger("Titan").setLevel(logging.WARNING)

def show_intelligence():
    print("\n" + "="*60)
    print("   TITAN INTELLIGENCE REPORT: FULL UNIVERSE SCAN")
    print("="*60)
    
    # Initialize Bot with full universe
    bot = TitanBot() # Uses the expanded 16-asset universe by default now
    
    if not bot.executor.connect():
        print("❌ MT5 Connection Failed.")
        return

    print(f"Scanning {len(bot.universe)} symbols... This may take a moment.")

    with open("SCAN_SUMMARY.md", "w") as f:
        f.write("# Market Scan Intelligence Report\n")
        f.write(f"*Last Scan (IST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Perform scan
        opportunities = bot.scanner.scan()
        
        for opp in opportunities:
            symbol = opp['symbol']
            score = opp['score']
            signal = opp['order_type']
            comment = opp['comment']
            ctx = opp.get('context', {})
            
            f.write(f"## SYMBOL: {symbol}\n")
            f.write(f"**MARKET CLIMATE**: {ctx.get('climate', 'N/A')} {ctx.get('meter', '')}\n")
            f.write(f"**SCORING**: {score}/100\n\n")
            
            f.write("### Playbook Checklist:\n")
            for item in opp.get('checklist', []):
                f.write(f"* {item}\n")
            
            if "DEATH ZONE" in comment or "EXHAUSTION" in comment:
                 f.write(f"\n> [!CAUTION]\n> **{comment}**\n")
            
            f.write(f"\n**DECISION**: {signal}\n")
            f.write(f"**REASON**: {comment}\n\n")
            f.write("---\n")
            
    bot.executor.shutdown()
    print("\n✅ Intelligence Report generated: SCAN_SUMMARY.md")
    print("="*60)

if __name__ == "__main__":
    show_intelligence()
