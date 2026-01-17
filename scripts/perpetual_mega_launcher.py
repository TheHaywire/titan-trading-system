import subprocess
import time
import sys
import os
from datetime import datetime

# Setup paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MEGA_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "mega_launcher_24_7.py")
LOG_FILE = os.path.join(PROJECT_ROOT, "MEGA_OPERATIONS.log")

def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [MEGA_ORCHESTRATOR] {message}\n"
    print(log_msg.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg)

def run_perpetual_mega():
    log_event("="*60)
    log_event("   TITAN MEGA-UNIVERSE ORCHESTRATOR: ACTIVATING 24/7 MODE")
    log_event("="*60)
    log_event(f"Discovery: 1500+ Symbols | Async Multi-Processing")
    
    while True:
        log_event("Launching Mega Launcher Engine...")
        
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                process = subprocess.Popen(
                    [sys.executable, MEGA_SCRIPT],
                    cwd=PROJECT_ROOT,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=os.environ.copy()
                )
                
                log_event(f"Mega Engine running with PID: {process.pid}")
                process.wait()
            
            if process.returncode != 0:
                log_event(f"Mega Engine CRASHED (Return Code: {process.returncode}). Restarting in 15s...")
            else:
                log_event("Mega Engine exited cleanly. Restarting in 10s...")
                
        except Exception as e:
            log_event(f"Mega Orchestrator encountered error: {e}")
            
        time.sleep(15)

if __name__ == "__main__":
    try:
        run_perpetual_mega()
    except KeyboardInterrupt:
        log_event("Mega Orchestrator shutdown by user.")
