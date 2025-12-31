import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
import json

# Add parent directory to path to import titan_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.engine import TitanEngine
from config.settings import settings

app = FastAPI(title="Titan Algo API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
# We initialize it globally.
engine = TitanEngine()
engine_task = None

# Custom Logger to stream to WebSockets
class WebSocketHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.clients = []

    def emit(self, record):
        # Safety check: Only emit if there is a running loop
        try:
            loop = asyncio.get_running_loop()
            if loop and loop.is_running():
                log_entry = self.format(record)
                for client in self.clients:
                    asyncio.create_task(client.send_text(log_entry))
        except RuntimeError:
            pass

ws_handler = WebSocketHandler()
# Add handler to Root Logger to capture EVERYTHING
logging.getLogger().addHandler(ws_handler)
logging.getLogger().setLevel(logging.INFO)


@app.get("/")
def read_root():
    return {"Status": "Online", "Service": "Titan System 2.0"}

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    global engine_task
    
    if engine.running:
        return {"message": "Already running"}
    
    # Run the engine loop as an asyncio task
    # We must ensure we don't block the API
    engine_task = asyncio.create_task(engine.start())
    
    return {"message": "Titan Engine Started"}

@app.post("/stop")
async def stop_bot():
    if not engine.running:
        return {"message": "Not running"}
    
    engine.running = False
    # The loop in engine.start() will break, and the task will finish.
    return {"message": "Stopping Engine..."}

@app.get("/status")
def get_status():
    return engine.get_status()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_handler.clients.append(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except:
        ws_handler.clients.remove(websocket)

@app.get("/api/reasoning")
def get_reasoning():
    """Returns the latest market scan analysis filtered into accepted/rejected for the console"""
    scan = engine.scan_results.get("Detailed Analysis", [])
    
    accepted = []
    rejected = []
    
    for item in scan:
        # Create common log object
        log_entry = {
            "symbol": item['symbol'],
            "why": item['reasoning'][0] if item['reasoning'] else "Analyzing...",
            "data": {"trend": item.get('trend', 'NEUTRAL')},
            "reason_code": item.get('strategy', 'AI_SCAN'),
            "score": item.get('score', 0)
        }
        
        if item.get('signal') and item.get('signal') != "HOLD":
            accepted.append(log_entry)
        else:
            # If rejected, maybe include why
            log_entry["reason_text"] = log_entry["why"]
            rejected.append(log_entry)
            
    return {
        "accepted": accepted,
        "rejected": rejected
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
