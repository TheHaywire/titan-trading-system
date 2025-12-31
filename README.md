[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MetaTrader 5](https://img.shields.io/badge/MetaTrader-5-green.svg)](https://www.metatrader5.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional algorithmic trading system for MetaTrader 5 with multiple automated strategies, risk management, and real-time monitoring.

## 📚 Documentation

- **[Getting Started](docs/wiki/Getting-Started.md)** - Installation and setup guide
- **[Architecture](docs/wiki/Architecture.md)** - System design and components
- **[Trading Strategies](docs/wiki/Trading-Strategies.md)** - How the bot trades
- **[Risk Management](docs/wiki/Risk-Management.md)** - Safety features

## 🚀 Features

### Trading Bots
- **Robust Bot** - Production-ready with full risk controls
- **GOLD Scalper** - Specialized M5 gold scalping
- **Aggressive Bot** - Multi-symbol momentum trading
- **Proven Bot** - Backtested EMA strategies
- **Mega Scanner** - Scans 1500+ symbols

### Risk Management
- Dynamic position sizing (% of equity)
- Correlation limits per instrument group
- Auto break-even protection
- Total portfolio risk cap
- Circuit breaker for drawdowns

### Infrastructure
- Event-driven architecture
- SQLite trade logging
- Telegram notifications
- Google Sheets integration
- Real-time dashboard

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/TheHaywire/titan-trading-system.git
cd titan-trading-system

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your MT5 credentials
```

## ⚙️ Configuration

Edit `.env` with your settings:
```env
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🎮 Quick Start

```bash
# Run the production bot (recommended)
python -m titan_system.titan_production

# Alternative: Robust bot
python -m titan_system.robust_bot

# Check account status
python scripts/status.py

# Secure profits (move SL to break-even)
python scripts/secure_profits.py
```

## 📊 Trading Bots Overview

| Bot | Timeframe | Symbols | Risk/Trade | Description |
|-----|-----------|---------|------------|-------------|
| `robust_bot` | M15 | 9 curated | 0.5% | Production-ready |
| `gold_scalper` | M5 | GOLD | 5 lots fixed | Scalping |
| `aggressive_bot` | M15 | 9 symbols | 1% | High frequency |
| `proven_bot` | H1 | 8 symbols | 1% | EMA strategies |
| `mega_scanner` | M15 | 1500+ | 0.5% | Full market scan |

## 📁 Project Structure

```
titan-trading-system/
├── titan_system/           # Core trading modules
│   ├── core/               # Engine, memory, circuit breaker
│   ├── strategies/         # Trading strategies
│   ├── execution/          # MT5 executor, trade manager
│   ├── agents/             # Decision agents
│   └── *.py                # Trading bots
├── scripts/                # Utility scripts
│   ├── status.py           # Account status
│   ├── secure_profits.py   # Profit protection
│   └── scan_all.py         # Market scanner
├── config/                 # Configuration
└── data/                   # Trade data, logs
```

## 🛡️ Risk Controls

1. **Position Sizing**: `lot = (equity × risk%) / (SL_points × tick_value)`
2. **Correlation Limits**: Max 2 positions per currency group
3. **Total Risk Cap**: Max 5% portfolio risk at any time
4. **Auto Break-Even**: SL moved to entry when profit > $100/lot
5. **Circuit Breaker**: Halts trading at 5% daily drawdown

## 📈 Performance Tracking

```bash
# Analyze recent trades
python scripts/analyze_my_trades.py

# Check protection status
python scripts/check_protection.py
```

## ⚠️ Disclaimer

This software is for educational purposes only. Trading forex and CFDs carries substantial risk of loss. Past performance is not indicative of future results. Use at your own risk.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 👤 Author

**Manan Kharbanda** ([@TheHaywire](https://github.com/TheHaywire))

---

*Built with 🔥 for automated trading*
