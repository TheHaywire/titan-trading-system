import requests
import sys

def check_service(url, name):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {name} is ONLINE ({url})")
            return True
        else:
            print(f"⚠️ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is OFFLINE. (Connection Refused)")
        return False
    except Exception as e:
        print(f"❌ {name} Error: {e}")
        return False

print("🏥 SYSTEM HEALTH CHECK")
print("-" * 30)

backend = check_service("http://localhost:8000/", "Backend API")
reasoning = check_service("http://localhost:8000/api/reasoning", "Deep Reasoning Engine")
# Frontend is served by Vite, usually just static files but verifiable
frontend = check_service("http://localhost:5173/", "Frontend Dashboard")

print("-" * 30)
if backend and frontend:
    print("🚀 SYSTEM IS FULLY OPERATIONAL")
    print("   Open http://localhost:5173 in Chrome/Edge to view the dashboard.")
else:
    print("⚠️ SYSTEM ISSUES DETECTED")
    print("   Run 'start_app.bat' to restart services.")
