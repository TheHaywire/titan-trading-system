"""
Kill Switch Module - Emergency Trading Halt System
Provides 3-tier safety mechanism to stop trading under critical conditions.
"""

import MetaTrader5 as mt5
import logging
from datetime import datetime
from typing import Set, Optional
import json

logger = logging.getLogger(__name__)


class KillSwitch:
    """3-Tier Emergency Stop Mechanism"""
    
    def __init__(self, email_notifier=None, telegram_notifier=None):
        self.global_enabled = True  # Master switch
        self.account_active = True  # Account-level pause
        self.symbol_blacklist: Set[str] = set()  # Symbol-level blocks
        
        # Notifiers
        self.email = email_notifier
        self.telegram = telegram_notifier
        
        # State tracking
        self.triggers = []  # Log of all triggers
        
        logger.info("🛡️ Kill Switch initialized - All systems GO")
    
    def trigger_global(self, reason: str):
        """
        LEVEL 1: Global Kill Switch - STOPS EVERYTHING
        
        Actions:
        - Closes ALL open positions immediately
        - Cancels ALL pending orders
        - Blocks all future trades
        - Sends emergency alerts
        
        Use when: Catastrophic system failure, extreme market event
        """
        logger.critical(f"🚨 GLOBAL KILL SWITCH ACTIVATED: {reason}")
        
        self.global_enabled = False
        self._log_trigger("GLOBAL", reason)
        
        # Close all positions
        closed_count = self._close_all_positions()
        
        # Cancel all pending orders
        cancelled_count = self._cancel_all_orders()
        
        # Send alerts
        alert_msg = f"""
🚨 GLOBAL KILL SWITCH ACTIVATED

Reason: {reason}
Time: {datetime.now()}
Actions Taken:
  - Closed {closed_count} positions
  - Cancelled {cancelled_count} orders
  - All trading HALTED

Manual intervention required to restart.
"""
        self._send_alert(alert_msg, priority="CRITICAL")
        
        return {
            "triggered": True,
_type": "GLOBAL",
            "reason": reason,
            "positions_closed": closed_count,
            "orders_cancelled": cancelled_count
        }
    
    def trigger_symbol(self, symbol: str, reason: str):
        """
        LEVEL 2: Symbol Kill Switch - Block specific instrument
        
        Actions:
        - Adds symbol to blacklist
        - Closes all open positions for this symbol
        - Prevents new trades on this symbol
        
        Use when: Symbol-specific issues (excessive slippage, data corruption)
        """
        logger.warning(f"⚠️ SYMBOL KILL SWITCH: {symbol} - {reason}")
        
        self.symbol_blacklist.add(symbol)
        self._log_trigger("SYMBOL", f"{symbol}: {reason}")
        
        # Close positions for this symbol only
        positions = mt5.positions_get(symbol=symbol)
        closed_count = 0
        
        if positions:
            for pos in positions:
                if self._close_position(pos.ticket):
                    closed_count += 1
        
        alert_msg = f"""
⚠️ Symbol Blacklisted: {symbol}

Reason: {reason}
Positions closed: {closed_count}

This symbol is now blocked from trading.
"""
        self._send_alert(alert_msg, priority="HIGH")
        
        return {
            "triggered": True,
            "type": "SYMBOL",
            "symbol": symbol,
            "reason": reason,
            "positions_closed": closed_count
        }
    
    def trigger_account(self, reason: str):
        """
        LEVEL 3: Account Pause - Stop new trades, keep positions
        
        Actions:
        - Pauses new trade entries
        - Keeps existing positions open
        - Allows closing trades
        
        Use when: Need to stop trading temporarily without closing positions
        """
        logger.warning(f"⏸️ ACCOUNT PAUSED: {reason}")
        
        self.account_active = False
        self._log_trigger("ACCOUNT_PAUSE", reason)
        
        alert_msg = f"""
⏸️ Account Trading Paused

Reason: {reason}

New trades blocked. Existing positions remain open.
Can be resumed manually.
"""
        self._send_alert(alert_msg, priority="MEDIUM")
        
        return {
            "triggered": True,
            "type": "ACCOUNT_PAUSE",
            "reason": reason
        }
    
    def can_trade(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Check if trading is allowed for a symbol.
        
        Returns:
            (allowed: bool, block_reason: Optional[str])
        """
        if not self.global_enabled:
            return False, "Global kill switch active"
        
        if not self.account_active:
            return False, "Account paused"
        
        if symbol in self.symbol_blacklist:
            return False, f"Symbol {symbol} blacklisted"
        
        return True, None
    
    def reset_global(self, confirmation_code: str):
        """Reset global kill switch (requires confirmation code)"""
        if confirmation_code == "TITAN_RESET_GLOBAL":
            self.global_enabled = True
            logger.info("✅ Global kill switch RESET - Trading enabled")
            return True
        else:
            logger.error("❌ Invalid reset code")
            return False
    
    def reset_account(self):
        """Resume account trading"""
        self.account_active = True
        logger.info("✅ Account trading RESUMED")
    
    def remove_symbol_blacklist(self, symbol: str):
        """Remove symbol from blacklist"""
        if symbol in self.symbol_blacklist:
            self.symbol_blacklist.remove(symbol)
            logger.info(f"✅ Symbol {symbol} removed from blacklist")
            return True
        return False
    
    def get_status(self) -> dict:
        """Get current kill switch status"""
        return {
            "global_enabled": self.global_enabled,
            "account_active": self.account_active,
            "blacklisted_symbols": list(self.symbol_blacklist),
            "total_triggers": len(self.triggers),
            "last_trigger": self.triggers[-1] if self.triggers else None
        }
    
    # --- Internal Helper Methods ---
    
    def _close_all_positions(self) -> int:
        """Close all open positions"""
        positions = mt5.positions_get()
        closed_count = 0
        
        if positions:
            for pos in positions:
                if self._close_position(pos.ticket):
                    closed_count += 1
        
        return closed_count
    
    def _close_position(self, ticket: int) -> bool:
        """Close a specific position"""
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False
        
        pos = position[0]
        symbol = pos.symbol
        volume = pos.volume
        
        # Determine close order type
        if pos.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 50,  # Allow more slippage for emergency close
            "magic": pos.magic,
            "comment": "KILL_SWITCH_CLOSE",
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Closed position {ticket} ({symbol})")
            return True
        else:
            logger.error(f"Failed to close {ticket}: {result.comment}")
            return False
    
    def _cancel_all_orders(self) -> int:
        """Cancel all pending orders"""
        orders = mt5.orders_get()
        cancelled_count = 0
        
        if orders:
            for order in orders:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": order.ticket
                }
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    cancelled_count += 1
        
        return cancelled_count
    
    def _log_trigger(self, trigger_type: str, reason: str):
        """Log kill switch trigger"""
        trigger = {
            "type": trigger_type,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.triggers.append(trigger)
        
        # Also log to file
        with open('data/kill_switch_log.json', 'a') as f:
            f.write(json.dumps(trigger) + '\n')
    
    def _send_alert(self, message: str, priority: str = "MEDIUM"):
        """Send alerts via all available channels"""
        # Email
        if self.email:
            try:
                subject = f"[{priority}] Kill Switch Triggered"
                self.email.send_email(subject, message)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Telegram
        if self.telegram:
            try:
                self.telegram.send_message(message)
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
        
        # Console (always)
        print("\n" + "="*60)
        print(message)
        print("="*60 + "\n")


# --- Auto-Trigger Conditions ---

def check_kill_switch_conditions(kill_switch: KillSwitch, account_info, session_health: dict):
    """
    Automatically trigger kill switches based on predefined conditions.
    
    Call this every tick/cycle to monitor for emergency situations.
    """
    
    # Condition 1: Account drawdown > 10%
    starting_balance = 10000  # TODO: Get from config or DB
    current_equity = account_info.equity
    drawdown_pct = (starting_balance - current_equity) / starting_balance
    
    if drawdown_pct > 0.10:  # 10% max drawdown
        kill_switch.trigger_global(f"Max account drawdown reached: {drawdown_pct*100:.1f}%")
        return
    
    # Condition 2: Daily loss > 5%
    # TODO: Track daily starting balance
    
    # Condition 3: Connection loss > 5 seconds
    if session_health.get("ping_ms", 0) > 5000:
        kill_switch.trigger_global("Connection lost for >5 seconds")
        return
    
    # Condition 4: Symbol-specific excessive slippage
    # TODO: Track slippage per symbol and trigger symbol blacklist if > 5 pips avg

