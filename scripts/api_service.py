"""
API SERVICE
===========
FastAPI server exposing MT5 and Finviz data.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import sys, os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_service import get_session, Symbol, FinvizData, News, Alert
from mt5_service import MT5Service
from finviz_service import FinvizService

app = FastAPI(title="MT5 Command Center API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
mt5_svc = MT5Service()
finviz_svc = FinvizService()

# Pydantic Models for Response
class SymbolMetrics(BaseModel):
    ticker: str
    price: Optional[float]
    change_pct: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    pe: Optional[float]
    rel_vol: Optional[float]
    source: str
    last_updated: str

class PositionInfo(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: float
    profit: float
    price_open: float
    price_current: float
    sl: float
    tp: float

class PortfolioSnapshot(BaseModel):
    account: dict
    positions: List[PositionInfo]
    timestamp: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "MT5 Command Center API"}

@app.get("/symbols", response_model=List[SymbolMetrics])
def get_all_symbols():
    """Get list of active symbols with combined MT5 + Finviz metrics."""
    session = get_session()
    symbols = session.query(Symbol).filter(Symbol.is_active == 1).all()
    
    # Get real-time prices for MT5 symbols
    mt5_symbols = [s.ticker for s in symbols if "MT5" in s.source or "Both" in s.source]
    real_time_prices = mt5_svc.get_prices(mt5_symbols)
    
    results = []
    for s in symbols:
        price_data = real_time_prices.get(s.ticker, {})
        f_data = s.finviz_data
        
        results.append(SymbolMetrics(
            ticker=s.ticker,
            price=price_data.get("last") or (f_data.price if f_data else None),
            change_pct=f_data.change_pct if f_data else None,
            bid=price_data.get("bid"),
            ask=price_data.get("ask"),
            pe=f_data.pe if f_data else None,
            rel_vol=f_data.rel_vol if f_data else None,
            source=s.source,
            last_updated=s.last_updated.isoformat()
        ))
    
    session.close()
    return results

@app.get("/portfolio", response_model=PortfolioSnapshot)
def get_portfolio():
    """Get live MT5 account and position data."""
    acc = mt5_svc.get_account_info()
    if not acc:
        raise HTTPException(status_code=503, detail="MT5 not connected")
    
    pos = mt5_svc.get_positions()
    return PortfolioSnapshot(
        account=acc,
        positions=pos,
        timestamp=datetime.now().isoformat()
    )

@app.get("/news/{ticker}")
def get_news(ticker: str):
    """Get latest news for a specific ticker."""
    news = finviz_svc.get_ticker_news(ticker)
    if news is None:
        raise HTTPException(status_code=404, detail=f"News not found for {ticker}")
    
    # Check if news is a DataFrame or List
    if hasattr(news, 'to_dict'):
        return news.to_dict(orient='records')
    return news

@app.get("/alerts")
def get_active_alerts():
    """Get latest unread alerts."""
    session = get_session()
    alerts = session.query(Alert).filter(Alert.is_read == 0).order_by(Alert.timestamp.desc()).limit(20).all()
    session.close()
    return alerts

# ========== TRADING CONTROL ENDPOINTS ==========

# Global state for auto-trading (in production, use Redis or DB)
AUTO_TRADE_ENABLED = False

class AutoTradeRequest(BaseModel):
    enabled: bool

@app.post("/trade/autobots")
def toggle_auto_trade(request: AutoTradeRequest):
    """
    Enable or disable automated trading.
    POST /trade/autobots {"enabled": true}
    """
    global AUTO_TRADE_ENABLED
    AUTO_TRADE_ENABLED = request.enabled
    
    status = "ENABLED" if request.enabled else "DISABLED"
    return {
        "status": "success",
        "auto_trade": status,
        "message": f"Automated trading {status}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trade/status")
def get_trade_status():
    """Get current auto-trade status."""
    return {
        "auto_trade_enabled": AUTO_TRADE_ENABLED,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/trade/panic")
def emergency_close_all():
    """
    PANIC BUTTON: Close all open positions immediately.
    POST /trade/panic
    """
    # Disable auto-trading first
    global AUTO_TRADE_ENABLED
    AUTO_TRADE_ENABLED = False
    
    # Close all positions
    closed_count = mt5_svc.close_all_positions()
    
    if closed_count is None:
        raise HTTPException(status_code=503, detail="MT5 not connected or operation failed")
    
    return {
        "status": "success",
        "message": f"Emergency closure executed: {closed_count} positions closed",
        "closed_count": closed_count,
        "auto_trade_disabled": True,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    uvicorn.run(app, host="0.0.0.0", port=8010)
