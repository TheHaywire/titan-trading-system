import time
import subprocess
import os
import sys
import json
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s | WATCHDOG | %(message)s')
logger = logging.getLogger("Titan.Watchdog")

STATE_FILE = "titan_system/dashboard/state.json"
ENGINE_SCRIPT = ["python", "titan_system/core/engine.py"]
TIMEOUT_SECONDS = 30 

def launch_engine():
    logger.info("🚀 Launching Titan Engine...")
    # Run in the same console to avoid window spam
    return subprocess.Popen(ENGINE_SCRIPT)

def check_heartbeat():
    try:
        if not os.path.exists(STATE_FILE):
            return False, "No State File"
            
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            
        last_update = state.get('timestamp', 0)
        age = time.time() - last_update
        
        if age > TIMEOUT_SECONDS:
            return False, f"State Stale ({age:.1f}s)"
            
        return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    print("🐕 Titan Watchdog Active")
    process = launch_engine()
    
    while True:
        # Check if process crashed
        if process.poll() is not None:
            logger.warning("⚠️ Engine Process Died! preventing rapid respawn...")
            # Backoff to prevent popup storm
            time.sleep(5)
            logger.info("Restarting Engine...")
            process = launch_engine()
        
        # Check Heartbeat (Freeze Detection)
        alive, reason = check_heartbeat()
        if not alive:
             logger.error(f"💀 Engine Frozen: {reason}. Killing & Restarting...")
             process.terminate()
             try:
                 process.wait(timeout=5)
             except subprocess.TimeoutExpired:
                 process.kill()
                 
             process = launch_engine()
             
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Watchdog exiting...")
