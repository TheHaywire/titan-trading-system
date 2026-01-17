"""
Gemini API Usage Optimization
=============================
Free tier limits are strict. This module helps manage usage.

gemini-2.5-flash:
- 5 requests/minute (RPM)
- 250K tokens/minute (TPM)
- 20 requests/DAY (RPD) ← HARD LIMIT

Strategies:
1. Cache results to avoid duplicate requests
2. Use smaller prompts where possible
3. Use gemini-2.5-flash-lite for simple tasks
4. Track usage to avoid hitting limits
"""
import json
import os
from datetime import datetime, date
from typing import Dict, Optional

USAGE_FILE = "data/gemini_usage.json"
DAILY_LIMIT = 20


def load_usage() -> Dict:
    """Load today's API usage."""
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            data = json.load(f)
            # Reset if new day
            if data.get("date") != str(date.today()):
                return {"date": str(date.today()), "requests": 0, "tokens": 0}
            return data
    return {"date": str(date.today()), "requests": 0, "tokens": 0}


def save_usage(data: Dict):
    """Save usage data."""
    os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
    with open(USAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def track_request(tokens_used: int = 0):
    """Track an API request."""
    usage = load_usage()
    usage["requests"] += 1
    usage["tokens"] += tokens_used
    usage["last_request"] = datetime.now().isoformat()
    save_usage(usage)
    return usage


def can_make_request() -> tuple[bool, str]:
    """Check if we can make a request within limits."""
    usage = load_usage()
    
    if usage["requests"] >= DAILY_LIMIT:
        return False, f"Daily limit reached ({usage['requests']}/{DAILY_LIMIT})"
    
    remaining = DAILY_LIMIT - usage["requests"]
    return True, f"OK - {remaining} requests remaining today"


def get_usage_status() -> Dict:
    """Get current usage status."""
    usage = load_usage()
    return {
        "date": usage["date"],
        "requests_used": usage["requests"],
        "requests_limit": DAILY_LIMIT,
        "requests_remaining": DAILY_LIMIT - usage["requests"],
        "tokens_used": usage["tokens"],
        "can_request": usage["requests"] < DAILY_LIMIT
    }


def reset_usage():
    """Manually reset usage (use with caution)."""
    save_usage({"date": str(date.today()), "requests": 0, "tokens": 0})


# Model recommendations based on task
MODEL_RECOMMENDATIONS = {
    "simple_chat": "gemini-2.5-flash-lite",  # 10 RPM, simpler tasks
    "analysis": "gemini-2.5-flash",          # Full analysis
    "embeddings": "gemini-embedding-1.0",    # For embeddings
}


def get_recommended_model(task_type: str = "analysis") -> str:
    """Get recommended model based on task type."""
    return MODEL_RECOMMENDATIONS.get(task_type, "gemini-2.5-flash")


if __name__ == "__main__":
    status = get_usage_status()
    print("=" * 50)
    print("GEMINI API USAGE STATUS")
    print("=" * 50)
    print(f"Date: {status['date']}")
    print(f"Requests: {status['requests_used']} / {status['requests_limit']}")
    print(f"Remaining: {status['requests_remaining']}")
    print(f"Tokens used: {status['tokens_used']}")
    print(f"Can request: {'YES' if status['can_request'] else 'NO - LIMIT REACHED'}")
