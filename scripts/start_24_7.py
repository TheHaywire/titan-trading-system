import subprocess
import time
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_bot():
    """
    Persistence Layer: Restarts the bot if it crashes.
    """
    script_path = os.path.join(os.path.dirname(__file__), "..", "titan_system", "execution", "main_loop.py")
    
    print("="*60)
    print("   TITAN 24/7 ORCHESTRATOR: PERSISTENCE LAYER ACTIVE")
    print("="*60)
    
    while True:
        print(f"\n[INFO] Launching Titan Main Loop at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # We use subprocess to run the main_loop in a separate process
        # This allows us to catch fatal python-level crashes (Segfaults, etc.) 
        # that even try-except inside the loop might miss.
        try:
            process = subprocess.Popen([sys.executable, script_path], 
                                     env=os.environ.copy())
            process.wait() # Wait for it to finish (or crash)
            
            if process.returncode != 0:
                print(f"[CRASH] Titan Loop exited with code {process.returncode}. Restarting in 10s...")
            else:
                print("[INFO] Titan Loop exited cleanly. Restarting for 24/7 duty in 5s...")
                
        except Exception as e:
            print(f"[ERROR] Orchestrator encountered failure: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    run_bot()
