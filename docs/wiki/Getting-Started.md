# Getting Started

## Prerequisites

Before running Titan, ensure you have:

1. **Python 3.10+** installed
2. **MetaTrader 5** terminal installed and running
3. A **forex/CFD broker** that supports MT5
4. Basic understanding of algorithmic trading risks

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/TheHaywire/titan-trading-system.git
cd titan-trading-system
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Edit `.env` File

Open `.env` in a text editor and configure:

```env
# MT5 Credentials
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server  # e.g., "ICMarkets-Demo"

# Telegram (Optional)
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Settings
TRADING_MODE=LIVE  # or PAPER
MAX_DAILY_LOSS_PERCENT=5.0
```

### 3. Get MT5 Credentials

- **Login**: Your MT5 account number
- **Password**: Your MT5 password
- **Server**: Find in MT5 → Tools → Options → Server

### 4. Set Up Telegram (Optional)

1. Create a bot: Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Get your bot token
3. Get your chat ID: Talk to [@userinfobot](https://t.me/userinfobot)

## Running the Bot

### Production Bot (Recommended)

```bash
python -m titan_system.titan_production
```

### Alternative Bots

```bash
# Robust bot (simple, proven)
python -m titan_system.robust_bot

# GOLD scalper (M5, gold only)
python -m titan_system.gold_scalper
```

## Verification

Once running, you should see:

```
============================================================
🚀 Titan Production Bot v1.0.0
============================================================
Account: 12345678
Equity: $10,000.00
Universe: 8 symbols
Risk/Trade: 0.5%
============================================================
✅ Database initialized
--- CYCLE 1 ---
```

## Monitoring

### Check Account Status

In a separate terminal:

```bash
python scripts/status.py
```

Output:
```
Equity: $10,000.00
Balance: $10,000.00
Profit: $0.00
Open Positions: 0
```

### View Database Logs

```bash
sqlite3 titan_production.db
```

```sql
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;
```

## Safety Checks

Before going live:

1. ✅ Test on **demo account** first
2. ✅ Verify `.env` configuration
3. ✅ Check MT5 is connected
4. ✅ Monitor first few trades
5. ✅ Set appropriate risk limits

## Common Issues

### "MT5 initialization failed"

- Ensure MT5 terminal is running
- Check login credentials in `.env`
- Verify internet connection

### "Symbol not found"

- Symbol name might differ by broker (e.g., "XAUUSD" vs "GOLD")
- Edit `UNIVERSE` in `titan_production.py`

### "Spread too high"

- Normal for volatile symbols
- Bot automatically skips high-spread trades
- Check broker spread fees

## Next Steps

- [Configuration Guide](Configuration) - Detailed settings
- [Trading Strategies](Trading-Strategies) - How signals work
- [Risk Management](Risk-Management) - Safety features

## Support

Having issues? 
- [GitHub Issues](https://github.com/TheHaywire/titan-trading-system/issues)
- [Discussions](https://github.com/TheHaywire/titan-trading-system/discussions)
