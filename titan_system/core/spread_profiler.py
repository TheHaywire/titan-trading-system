"""
Spread Profiler
===============
Samples spreads across time to build reliable liquidity profiles.
A single snapshot is unreliable - spreads widen during:
- Asian session (for EUR pairs)
- News events
- Market open/close
- Low volume hours
"""
import MetaTrader5 as mt5
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

SPREAD_DATA_FILE = "data/spread_profiles.json"


def sample_current_spreads(symbols: List[str] = None) -> Dict:
    """
    Sample current spread for all or specified symbols.
    Returns dict with timestamp and spreads.
    """
    if not mt5.initialize():
        return {"error": "MT5 not initialized"}
    
    if symbols is None:
        # Get all tradeable symbols
        all_syms = mt5.symbols_get()
        symbols = [s.name for s in all_syms if mt5.symbol_info(s.name) and mt5.symbol_info(s.name).trade_mode == 4]
    
    now = datetime.now()
    sample = {
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "weekday": now.weekday(),  # 0=Monday, 6=Sunday
        "spreads": {}
    }
    
    for sym in symbols:
        info = mt5.symbol_info(sym)
        if info:
            sample["spreads"][sym] = info.spread
    
    return sample


def load_spread_profiles() -> Dict:
    """Load existing spread profile data."""
    if os.path.exists(SPREAD_DATA_FILE):
        with open(SPREAD_DATA_FILE, 'r') as f:
            return json.load(f)
    return {"samples": [], "profiles": {}}


def save_spread_profiles(data: Dict):
    """Save spread profile data."""
    os.makedirs(os.path.dirname(SPREAD_DATA_FILE), exist_ok=True)
    with open(SPREAD_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def add_spread_sample():
    """
    Add a new spread sample to the profile data.
    Call this periodically (e.g., every hour) to build profiles.
    """
    data = load_spread_profiles()
    sample = sample_current_spreads()
    
    if "error" not in sample:
        data["samples"].append(sample)
        # Keep only last 7 days of samples (168 hours)
        if len(data["samples"]) > 168:
            data["samples"] = data["samples"][-168:]
        save_spread_profiles(data)
        print(f"Added spread sample at {sample['timestamp']} - {len(sample['spreads'])} symbols")
    
    return sample


def calculate_spread_profiles() -> Dict:
    """
    Calculate spread statistics from collected samples.
    Returns per-symbol profiles with min/avg/max/std spreads.
    """
    data = load_spread_profiles()
    samples = data.get("samples", [])
    
    if not samples:
        return {"error": "No samples collected yet. Run add_spread_sample() periodically."}
    
    # Aggregate spreads per symbol
    symbol_spreads = defaultdict(list)
    hour_spreads = defaultdict(lambda: defaultdict(list))  # symbol -> hour -> spreads
    
    for sample in samples:
        hour = sample.get("hour", 0)
        for sym, spread in sample.get("spreads", {}).items():
            symbol_spreads[sym].append(spread)
            hour_spreads[sym][hour].append(spread)
    
    # Calculate profiles
    profiles = {}
    for sym, spreads in symbol_spreads.items():
        if spreads:
            profiles[sym] = {
                "min": min(spreads),
                "max": max(spreads),
                "avg": round(sum(spreads) / len(spreads), 1),
                "samples": len(spreads),
                "spread_range": max(spreads) - min(spreads),
                # Best and worst hours
                "hourly_avg": {
                    h: round(sum(s)/len(s), 1) if s else 0 
                    for h, s in hour_spreads[sym].items()
                }
            }
    
    # Save profiles
    data["profiles"] = profiles
    data["last_calculated"] = datetime.now().isoformat()
    save_spread_profiles(data)
    
    return profiles


def get_liquid_symbols_from_profile(max_avg_spread: int = 100, min_samples: int = 5) -> List[Dict]:
    """
    Get liquid symbols based on profiled spread data (not just snapshot).
    """
    profiles = calculate_spread_profiles()
    
    if "error" in profiles:
        return []
    
    liquid = []
    for sym, profile in profiles.items():
        if profile["samples"] >= min_samples and profile["avg"] < max_avg_spread:
            liquid.append({
                "symbol": sym,
                "avg_spread": profile["avg"],
                "max_spread": profile["max"],
                "spread_variability": profile["spread_range"],
                "samples": profile["samples"]
            })
    
    # Sort by average spread
    liquid.sort(key=lambda x: x["avg_spread"])
    return liquid


def print_spread_report(top_n: int = 50):
    """Print a spread profile report."""
    profiles = calculate_spread_profiles()
    
    if "error" in profiles:
        print(profiles["error"])
        return
    
    # Sort by average spread
    sorted_profiles = sorted(profiles.items(), key=lambda x: x[1]["avg"])
    
    print(f"\n{'='*70}")
    print(f"SPREAD PROFILE REPORT - {len(profiles)} symbols analyzed")
    print(f"{'='*70}\n")
    
    print(f"{'Symbol':<20} {'Avg':<8} {'Min':<8} {'Max':<8} {'Range':<8} {'Samples':<8}")
    print("-" * 70)
    
    for sym, profile in sorted_profiles[:top_n]:
        print(f"{sym:<20} {profile['avg']:<8.1f} {profile['min']:<8} {profile['max']:<8} {profile['spread_range']:<8} {profile['samples']:<8}")
    
    # Summary
    print(f"\n{'='*70}")
    print("LIQUIDITY TIERS:")
    
    tight = [s for s, p in sorted_profiles if p["avg"] < 50]
    moderate = [s for s, p in sorted_profiles if 50 <= p["avg"] < 100]
    wide = [s for s, p in sorted_profiles if 100 <= p["avg"] < 500]
    illiquid = [s for s, p in sorted_profiles if p["avg"] >= 500]
    
    print(f"  🟢 Tight (avg < 50):     {len(tight)} symbols")
    print(f"  🟡 Moderate (50-100):    {len(moderate)} symbols")
    print(f"  🟠 Wide (100-500):       {len(wide)} symbols")
    print(f"  🔴 Illiquid (500+):      {len(illiquid)} symbols")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        # Add a new sample
        print("Sampling current spreads...")
        sample = add_spread_sample()
        print(f"Sampled {len(sample.get('spreads', {}))} symbols")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        # Print report
        print_spread_report()
    
    else:
        # Default: sample + report if enough data
        mt5.initialize()
        
        data = load_spread_profiles()
        if len(data.get("samples", [])) < 3:
            print("Collecting spread sample...")
            add_spread_sample()
            print(f"\nNeed more samples! Current: {len(data.get('samples', [])) + 1}")
            print("Run this script periodically (every hour) to build profiles:")
            print("  python titan_system/core/spread_profiler.py sample")
            print("\nOnce you have 5+ samples, run:")
            print("  python titan_system/core/spread_profiler.py report")
        else:
            add_spread_sample()
            print_spread_report()
        
        mt5.shutdown()
