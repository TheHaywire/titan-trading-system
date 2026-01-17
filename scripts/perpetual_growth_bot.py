import subprocess
import time
import sys
import os
from datetime import datetime

# Setup paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BOT_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "autonomous_bot.py")
LOG_FILE = os.path.join(PROJECT_ROOT, "GROWTH_OPERATIONS.log")

def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [ORCHESTRATOR] {message}\n"
    print(log_msg.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg)

    log_event("="*60)
    log_event("   TITAN SNIPER ENGINE: ACTIVATING RECOVERY MODE (GOLD ONLY)")
    log_event("="*60)
    log_event(f"Targeting: TOP-TIER GOLD LIQUIDITY ZONES (SNIPER SNIPER SNIPER)")
    
    while True:
        log_event("Launching Autonomous Growth Bot...")
        
        try:
            # Run the bot and capture output to log file
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                process = subprocess.Popen(
                    [sys.executable, BOT_SCRIPT],
                    cwd=PROJECT_ROOT,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=os.environ.copy()
                )
                
                log_event(f"Bot running with PID: {process.pid}")
                process.wait()
            
            if process.returncode != 0:
                log_event(f"Bot CRASHED (Return Code: {process.returncode}). Restarting in 10s...")
            else:
                log_event("Bot exited cleanly. Cycles complete. Restarting in 5s...")
                
        except Exception as e:
            log_event(f"Orchestrator encountered error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    try:
        run_perpetual_growth()
    except KeyboardInterrupt:
        log_event("Orchestrator shutdown by user.")
