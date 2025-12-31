from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.orm import relationship
from titan_system.data.database import Base
from datetime import datetime

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True) # Full name if available
    market_type = Column(String, default="FOREX") # FOREX, CRYPTO, STOCK, etc.
    active = Column(Integer, default=1)

    # Relationships
    ohlcvs = relationship("OHLCV", back_populates="ticker", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticker(symbol='{self.symbol}', type='{self.market_type}')>"

class OHLCV(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    
    # Timeframe (e.g., 'M1', 'H1', 'D1')
    timeframe = Column(String, nullable=False, index=True)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    
    # Relationship
    ticker = relationship("Ticker", back_populates="ohlcvs")

    # Composite index for fast lookups by ticker, timeframe, and time
    __table_args__ = (
        Index('idx_ohlcv_ticker_tf_time', 'ticker_id', 'timeframe', 'timestamp', unique=True),
    )

    def __repr__(self):
        return f"<OHLCV(ticker_id={self.ticker_id}, tf='{self.timeframe}', time='{self.timestamp}', close={self.close})>"

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(String, primary_key=True) # Ticket ID from MT5
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    
    profit = Column(Float, default=0.0)
    volume = Column(Float, nullable=False)
    direction = Column(String, nullable=False) # BUY / SELL
    
    strategy_name = Column(String, nullable=True)

    def __repr__(self):
        return f"<Trade({self.id}, {self.direction} @ {self.entry_price}, profit={self.profit})>"
