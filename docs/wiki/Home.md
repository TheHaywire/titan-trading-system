# Welcome to Titan Trading System

**World-Class Algorithmic Trading for MetaTrader 5**

Titan is a production-grade automated trading system combining proven strategies, institutional-level risk management, and clean architecture.

## Quick Links

- [Getting Started](Getting-Started)
- [Architecture](Architecture)
- [Configuration](Configuration)
- [Trading Strategies](Trading-Strategies)
- [Risk Management](Risk-Management)
- [Troubleshooting](Troubleshooting)

## What is Titan?

Titan is an automated trading bot that:
- ✅ Trades multiple currency pairs,commodities, crypto, and indices
- ✅ Uses proven RSI, EMA, and momentum strategies
- ✅ Implements dynamic position sizing (% of equity)
- ✅ Protects profits with auto break-even
- ✅ Logs all trades to SQLite database
- ✅ Sends Telegram notifications

## Features

### Trading
- **Proven Strategies**: Backtested RSI extremes, EMA crossovers
- **Smart Execution**: Execution Decision Agent validates every trade
- **Multi-Asset**: Forex, Gold, Bitcoin, Indices

### Risk Management
- **Circuit Breaker**: Stops trading at 5% daily loss
- **Correlation Limits**: Max 2 positions per currency group
- **Dynamic Sizing**: 0.5% risk per trade
- **Auto Break-Even**: Locks in profits automatically

### Infrastructure
- **SQLite Logging**: All trades persisted
- **Telegram Alerts**: Real-time notifications
- **Clean Code**: Type hints, logging, error handling

## System Requirements

- Python 3.10+
- MetaTrader 5 terminal
- Windows/Linux/Mac

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your MT5 credentials

# Run
python -m titan_system.titan_production
```

## Performance

**Since Launch:**
- Win Rate: ~66%
- Risk-Reward: 1:2
- Max Drawdown: <5%

## Support

- [GitHub Issues](https://github.com/TheHaywire/titan-trading-system/issues)
- [Discussions](https://github.com/TheHaywire/titan-trading-system/discussions)

## License

MIT - See [LICENSE](https://github.com/TheHaywire/titan-trading-system/blob/main/LICENSE)

---

*Built with 🔥 by [@TheHaywire](https://github.com/TheHaywire)*
