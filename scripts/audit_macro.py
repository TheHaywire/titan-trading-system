import json
import os
from datetime import datetime, timedelta

def audit_macro():
    """
    Scans for high-impact economic news events and saves them to a schedule.
    In a live production environment, this would use a real-time news API or scraper.
    """
    print("\n" + "="*80)
    print("   TITAN MACRO AUDIT: ECONOMIC NEWS SCANNER")
    print("="*80)

    # Today's date from system: 2025-12-19
    today_str = "2025-12-19"
    
    # These are the high-impact events found via research
    # Times are approximated for the demo/build purposes
    events = [
        {
            "event": "BoJ Interest Rate Decision",
            "symbol_group": "JPY",
            "time_ist": "2025-12-19 08:30:00", # Typical BoJ morning time
            "impact": "HIGH",
            "status": "PAST"
        },
        {
            "event": "UK Retail Sales m/m",
            "symbol_group": "GBP",
            "time_ist": "2025-12-19 12:30:00",
            "impact": "MEDIUM/HIGH",
            "status": "PAST"
        },
        {
            "event": "US Core PCE Price Index",
            "symbol_group": "USD",
            "time_ist": "2025-12-19 19:00:00", # Typical US 8:30 AM EST -> 19:00 IST
            "impact": "HIGH",
            "status": "UPCOMING"
        },
        {
            "event": "US Final GDP q/q",
            "symbol_group": "USD",
            "time_ist": "2025-12-19 19:00:00",
            "impact": "HIGH",
            "status": "UPCOMING"
        }
    ]

    print(f"Checking events for {today_str}...")
    
    upcoming = []
    now = datetime.now()
    
    for e in events:
        event_time = datetime.strptime(e['time_ist'], "%Y-%m-%d %H:%M:%S")
        if event_time > now:
            e['status'] = "UPCOMING"
            upcoming.append(e)
            print(f"  [⚠️ UPCOMING] {e['event']} ({e['symbol_group']}) at {e['time_ist']}")
        else:
            e['status'] = "PAST"
            print(f"  [✅ PAST] {e['event']} ({e['symbol_group']}) at {e['time_ist']}")

    # Save to JSON for the bot to read
    schedule_path = "MACRO_SCHEDULE.json"
    with open(schedule_path, "w") as f:
        json.dump(events, f, indent=4)

    # Save to Markdown for user visibility
    with open("MACRO_REPORT.md", "w") as f:
        f.write("# Titan Macro Intelligence Report\n\n")
        f.write(f"Scanned at: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Today's High-Impact Events\n")
        f.write("| Event | Group | Time (IST) | Impact | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for e in events:
            f.write(f"| {e['event']} | {e['symbol_group']} | {e['time_ist']} | {e['impact']} | {e['status']} |\n")
        
        f.write("\n\n## Quantitative Guidance\n")
        if upcoming:
            f.write("> [!WARNING]\n")
            f.write(f"> **NEWS SHIELD ACTIVE**. High-impact events are pending. The bot will automatically block new trades on {', '.join(set([u['symbol_group'] for u in upcoming]))} pairs +/- 30 mins from the event time.")
        else:
            f.write("> [!NOTE]\n")
            f.write("> **CLEAR SKIES**. No major high-impact events remaining for the day.")

    print(f"\n✅ Created MACRO_SCHEDULE.json and MACRO_REPORT.md")
    print("="*80)

if __name__ == "__main__":
    audit_macro()
