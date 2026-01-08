
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from typing import Dict

# Import the Engine
# In a real microservice, these might be separate processes communicating via Redis
# For this monolith-in-a-box, we import the engine instance (singleton pattern)
from titan_system.core.engine import TitanEngine
from config.settings import settings as Config


from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

from titan_system.core.engine import TitanEngine
from titan_system.api.scanner_service import ScannerService
from config.settings import settings as Config
import MetaTrader5 as mt5

# Custom Logger to stream to WebSockets
class WebSocketHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.clients = []

    def emit(self, record):
        try:
            loop = asyncio.get_running_loop()
            if loop and loop.is_running():
                log_entry = self.format(record)
                for client in self.clients:
                    asyncio.create_task(client.send_text(log_entry))
        except RuntimeError:
            pass

ws_handler = WebSocketHandler()
logging.getLogger().addHandler(ws_handler)
logging.getLogger("Titan").setLevel(logging.INFO)

app = FastAPI(title="Titan System API", version=Config.VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("Titan.API")

# Global Instances
engine = TitanEngine()
scanner_service = ScannerService()

# Models
class TradeRequest(BaseModel):
    symbol: str
    action: str # BUY or SELL
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@app.on_event("startup")
async def startup_event():
    """Start the Engine Loop when API starts"""
    logger.info("⚡ API Starting... Booting Titan Engine...")
    asyncio.create_task(engine.start())

@app.get("/")
def read_root():
    return {"system": "Titan Algo Platform", "version": Config.VERSION, "status": "ONLINE"}

@app.get("/status")
def get_status():
    """Returns the holistic system status for the dashboard."""
    account = engine.execution.get_account_info()
    return {
        "running": engine.running,
        "connected": engine.execution.connected,
        "regime": engine.strategy.last_regime if hasattr(engine.strategy, 'last_regime') else "UNKNOWN",
        "equity": account.get('equity', 0),
        "balance": account.get('balance', 0),
        "profit_today": 0.0, # TODO link to DB
        "active_trades": len(account.get('positions', [])),
        "latency": 34, # Placeholder
        "scanner": engine.scan_results, # Now populated
        "exposure": {p['symbol']: p['volume'] for p in account.get('positions', [])},
        "trades": account.get('positions', [])
    }

@app.post("/start")
def start_bot():
    if not engine.running:
        engine.running = True
        return {"message": "Engine Started"}
    return {"message": "Already Running"}

@app.post("/stop")
def stop_bot():
    engine.running = False
    return {"message": "Engine Output Paused (Process still alive)"}

@app.post("/execute")
def execute_trade(trade: TradeRequest):
    """Manual Trade Execution Endpoint"""
    logger.info(f"⚡ Manual Execution Request: {trade.action} {trade.symbol} {trade.volume}")
    
    result = engine.execution.execute_order(
        symbol=trade.symbol,
        order_type=trade.action,
        volume=trade.volume,
        sl_pips=50, # Defaults if not provided, TODO: logic
        tp_pips=100,
        comment="Titan-Web-Manual"
    )
    
    if result:
         return {"status": "success", "ticket": result.order}
    return {"status": "failed"}

# --- WebSockets ---

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    ws_handler.clients.append(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except Exception:
        ws_handler.clients.remove(websocket)

@app.websocket("/ws/market_data")
async def websocket_market(websocket: WebSocket):
    """
    Streams scanner results in real-time.
    Client sends 'start_scan' to trigger a scan loop.
    """
    await websocket.accept()
    logger.info("WS: Market Data Client Connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "start_scan":
                # Get Universe
                # For MVP, use the same lists as SMC Scanner
                universe = [
                    "XAUUSD", "GOLD", "EURUSD", "GBPUSD", "USDJPY", 
                    "US30", "NAS100", "SPX500", "BTCUSD", "ETHUSD"
                ]
                
                # Check for other symbols in Market Watch?
                # For MVP just do these hardcoded + active
                
                async for result in scanner_service.scan_stream(universe):
                    await websocket.send_json(result)
                    
                await websocket.send_json({"status": "scan_complete"})
                
    except Exception as e:
        logger.error(f"WS Error: {e}")

def start_server():
    uvicorn.run(app, host=Config.api_host, port=Config.api_port)

if __name__ == "__main__":
    start_server()
