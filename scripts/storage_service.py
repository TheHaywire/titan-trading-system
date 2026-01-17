"""
STORAGE SERVICE
===============
Handles database interactions for the MT5 Command Center Dashboard.
Uses SQLAlchemy for ORM.
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "command_center.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    source = Column(String)  # 'MT5', 'Finviz', 'Both'
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    finviz_data = relationship("FinvizData", back_populates="symbol", uselist=False)
    news = relationship("News", back_populates="symbol")

class FinvizData(Base):
    __tablename__ = "finviz_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), unique=True)
    
    # Fundamentals
    price = Column(Float)
    change_pct = Column(Float)
    pe = Column(Float)
    eps_growth = Column(Float)
    float_vol = Column(String)
    insider_own = Column(Float)
    short_interest = Column(Float)
    
    # Technicals / Screener tags
    rel_vol = Column(Float)
    avg_vol = Column(String)
    rsi_14 = Column(Float)
    screener_tags = Column(JSON)  # List of screener names this symbol appeared in
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    symbol = relationship("Symbol", back_populates="finviz_data")

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"))
    headline = Column(Text, nullable=False)
    source = Column(String)
    url = Column(String)
    timestamp = Column(DateTime)
    sentiment = Column(String)  # Positive, Negative, Neutral
    
    symbol = relationship("Symbol", back_populates="news")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    symbol_ticker = Column(String)
    message = Column(Text)
    severity = Column(String)  # INFO, WARNING, CRITICAL
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Integer, default=0)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()

if __name__ == "__main__":
    print(f"Initializing database at {DB_PATH}...")
    init_db()
    print("Database initialized successfully.")
