import time
import subprocess
import logging
import sys
import psutil
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | WATCHDOG | %(message)s',
    handlers=[
        logging.FileHandler("TITAN_WATCHDOG.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

TITAN_SCRIPT = "start_titan.bat"
CHECK_INTERVAL_SECONDS = 30

def is_titan_running():
    """Checks if the Titan API/Engine process is running."""
    # This is a bit tricky on Windows with batch files spawning python.
    # We look for a python process running 'titan_system.api.server' or 'engine.py'
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and "python" in proc.info['name'].lower():
                # Check for either module or script execution
                if any("titan_system.api.server" in arg for arg in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def start_titan():
    """Starts the Titan system using the batch script."""
    logging.info("🚀 Launching Titan System...")
    # Use Popen to start it detached
    subprocess.Popen([TITAN_SCRIPT], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

def main():
    logging.info("🛡️ Titan Watchdog Started")
    
    while True:
        try:
            running = is_titan_running()
            
            if not running:
                logging.warning("⚠️ Titan System NOT detected! Restarting...")
                start_titan()
            else:
                pass 
                # Optional: Ping the /status API Endpoint to check if it's frozen
                # But for now, process existence check is a good first step.
            
            time.sleep(CHECK_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logging.info("Watchdog stopped by user.")
            break
        except Exception as e:
            logging.error(f"Watchdog Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
