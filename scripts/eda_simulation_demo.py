import time
import random
import threading
from typing import Callable, List, Dict

# ==========================================
# 1. THE EVENT BUS (The Broker)
# ==========================================
class EventBus:
    def __init__(self):
        # A dictionary mapping Event Types to lists of Subscriber functions
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Registers a function to listen for a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        print(f"[Bus] Subscribed {callback.__name__} to {event_type}")

    def publish(self, event_type: str, data: dict):
        """Sends data to all functions subscribed to this event type."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                # In a real system, these would run in separate threads
                callback(data)

# ==========================================
# 2. THE PRODUCER (Market Data)
# ==========================================
def market_data_producer(bus: EventBus):
    """Simulates a live price feed from MT5."""
    symbols = ["GOLD", "BTCUSD", "US100"]
    print("\n--- Starting Market Data Feed ---")
    for _ in range(5):
        time.sleep(1)
        symbol = random.choice(symbols)
        price = round(2000 + random.uniform(-50, 50), 2)
        
        # The Producer just "shouts" the event
        event_data = {"symbol": symbol, "price": price, "timestamp": time.time()}
        print(f"\n[Producer] >> PUBLISHING: NEW_PRICE for {symbol} at {price}")
        bus.publish("NEW_PRICE", event_data)

# ==========================================
# 3. THE CONSUMERS (Strategies & Risk)
# ==========================================
def rsi_strategy_consumer(data):
    """Listens for price updates and looks for signals."""
    if data['price'] < 1970:
        print(f"  [RSI Strategy] Found BUY signal for {data['symbol']}!")
        # It then publishes its own event
        bus.publish("SIGNAL_DETECTED", {"strategy": "RSI", "symbol": data['symbol'], "type": "BUY"})

def risk_manager_consumer(data):
    """Listens for signals and evaluates risk."""
    print(f"  [Risk Manager] 🛡 Evaluating signal: {data['type']} on {data['symbol']}")
    # Logic to approve or deny
    approved = random.choice([True, True, False]) # Usually approved
    if approved:
        print(f"  [Risk Manager] ✅ RISK APPROVED for {data['symbol']}")
        bus.publish("ORDER_READY", data)
    else:
        print(f"  [Risk Manager] ❌ RISK DENIED for {data['symbol']}")

def dashboard_ui_consumer(data):
    """Just logs everything to a 'UI'."""
    print(f"  [Dashboard UI] 📊 Updating chart for {data.get('symbol')}...")

# ==========================================
# 4. RUNNING THE DEMO
# ==========================================
if __name__ == "__main__":
    bus = EventBus()

    # Setup the wiring (Subscriptions)
    # Note how multiple things can listen to "NEW_PRICE" at the same time!
    bus.subscribe("NEW_PRICE", rsi_strategy_consumer)
    bus.subscribe("NEW_PRICE", dashboard_ui_consumer)
    
    # Risk only cares about Signals, not raw prices
    bus.subscribe("SIGNAL_DETECTED", risk_manager_consumer)

    # Start the "Engine"
    market_data_producer(bus)
    
    print("\n--- Demo Complete ---")
    print("Notice how the Producer never talked to the Risk Manager directly.")
    print("They only talk through the BUS using EVENTS.")
