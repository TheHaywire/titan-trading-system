import os
import signal
import subprocess
import sys
import time
import webbrowser
from threading import Thread

# FORCE UTF-8 MDOE ON WINDOWS
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure Project Root is in Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import settings

# Windows process management
processes = []

def run_service(cmd, name):
    print(f"🚀 Starting {name}...", end=" ", flush=True)
    try:
        # Check if node/python on path
        p = subprocess.Popen(cmd, shell=True, cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE)
        processes.append(p)
        print("✅ PID:", p.pid)
        return p
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def kill_all():
    print("\n🛑 Shutting down all services...")
    for p in processes:
        try:
            p.terminate() 
            # Force kill on windows often needs taskkill if shell=True
            subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    print("👋 System Offline.")
    sys.exit(0)

if __name__ == "__main__":
    print("========================================")
    print("       TITAN ALGO - UNIFIED RUNNER      ")
    print("========================================")
    print("Press Ctrl+C to stop all services correctly.\n")

    # 1. Start Backend (FastAPI + Trading Bot)
    # Using 'call' to run python in new window or same?
    # User wanted FEWER terminals. 
    # Let's run backend in THIS terminal if possible, but frontend needs to serve.
    # Actually, running Uvicorn here allows us to see logs in one place.
    
    # 1. Start Frontend (Vite) - in background (new minimized window?)
    # Vite is noisy, let's put it in its own window but minimized if possible, or just standard.
    fe_cmd = "cd frontend && npm run dev"
    run_service(fe_cmd, "Frontend Dashboard")
    
    time.sleep(3) # Wait for FE
    
    # 2. Start Backend - in THIS terminal so user sees the 'shit' happening
    print("🧠 Starting Neural Engine (Backend)...")
    try:
        subprocess.run("cd backend && uvicorn app:app --host 0.0.0.0 --port 8000", shell=True)
    except KeyboardInterrupt:
        kill_all()
