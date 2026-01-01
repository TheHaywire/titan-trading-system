# 🚀 Titan Algo System: User Walkthrough

Welcome to your upgraded trading command center. This guide explains how to operate the new system.

## 1. Startup

The system is now robust and requires a clean start sequence.

1.  **Close all** terminal windows.
2.  Open a new terminal.
3.  Run the launcher:
    ```powershell
    .\start_app.bat
    ```
4.  Wait for the message: *"System is coming online..."*

## 2. The Command Center (Dashboard)

Navigate to **[http://localhost:5173](http://localhost:5173)** in your browser.

### 🧠 The Neural Consoles
- **Performance Overview**: A real-time equity curve. It updates every minute.
- **Deep Reasoning Stream** (Bottom Left): This is the most important part.
    - **Scrolling Text**: Shows the AI "thinking".
    - `✅ ACCEPT EURUSD`: Means the AI likes the setup.
    - `❌ REJECT - HIGH_COST_RATIO`: Means the AI saw a good trade but rejected it because the spread was too high (Safety Guard).

### 🤖 The Bot Status
- **Status Indicator** (Top Right): Should be **Green (Pulsing)**.
- **AI Generation**: Shows which "Brain" version is active (e.g., `Gen 40`).

## 3. Operations

### 📧 Daily Reports
You don't need to do anything. The bot automatically:
- Scans markets at **07:00 AM**.
- Generates a "Hedge Fund" style HTML report.
- Emails it to you.

### 🧬 AI Training (Manual Override)
If you want to force the AI to learn from the last 2 days of market chaos:

1.  Open a new terminal.
2.  Run:
    ```powershell
    python scripts/train_ai.py
    ```
3.  The bot will simulate 50 generations of evolution and update its brain file in `data/`.

## 4. Safety Features (Active Protection)

- **Equity Guard**: If you lose 5% in a day, the bot **Locks Down**. It won't take new trades until reset.
- **Spread Guard**: It calculates `Spread / ATR`. If the cost is >15% of the expected move, it rejects the trade.

## 5. Troubleshooting

If the dashboard looks "stuck":
1.  Run the health check:
    ```powershell
    python scripts/status_check.py
    ```
2.  If Offline, run `start_app.bat` again.
