
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config.settings import settings

logger = logging.getLogger("Titan.Telegram")

class TelegramNotifier:
    """
    Sends Push Notifications to the user's phone via Telegram.
    This is strictly for OUTBOUND communications (Alerts).
    """
    def __init__(self):
        self.enabled = False
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.warning("Telegram Token or Chat ID missing. Notifications disabled.")
            return

        try:
            self.bot = Bot(token=settings.telegram_bot_token)
            self.chat_id = settings.telegram_chat_id
            self.enabled = True
            
            # Verify bot works on init
            # Note: get_me is async, so we just log init success for now
            # and verify connectivity during the first send attempt
            logger.info("✅ Telegram Notifier Initialized")
            
        except Exception as e:
            logger.error(f"Failed to init Telegram Bot: {e}")

    async def send_message(self, message: str, priority: str = "NORMAL"):
        """
        Sends a text message to the configured chat_id.
        Priority: HIGH uses bold/alert formatting.
        """
        if not self.enabled: 
            return

        try:
            # Format message based on priority
            if priority == "HIGH":
                formatted_msg = f"🚨 *TITAN ALERT* 🚨\n\n{message}"
            elif priority == "SUCCESS":
                formatted_msg = f"✅ *Titan Success* \n\n{message}"
            else:
                formatted_msg = message

            # Async send
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=formatted_msg, 
                parse_mode='Markdown'
            )
        except TelegramError as e:
            if "Unauthorized" in str(e):
                logger.error("❌ Telegram Token Invalid. Disabling Telegram Bot.")
                self.enabled = False
            else:
                logger.error(f"Telegram Send Error: {e}")
        except Exception as e:
            logger.error(f"Telegram Unexpected Error: {e}")

    async def send_trade_alert(self, trade_result: dict, market_analysis: dict = None):
        """
        Specialized format for Trade Execution Alerts.
        """
        if not self.enabled: return

        symbol = trade_result.get('symbol', 'UNKNOWN')
        action = trade_result.get('type', 'ORDER') # BUY/SELL
        price = trade_result.get('price', 0.0)
        
        msg = (
            f"⚡ *TRADE EXECUTED*\n"
            f"**{action} {symbol}** @ {price}\n"
            f"-------------------\n"
        )
        
        if market_analysis:
            score = market_analysis.get('score', 'N/A')
        if market_analysis:
            score = market_analysis.get('score', 'N/A')
            ai_insight = market_analysis.get('ai_insight', None)
            
            msg += f"🧠 *Score*: {score}/100\n"
            
            # Try to parse compact AI summary
            if ai_insight:
                try:
                    import json
                    if isinstance(ai_insight, str):
                        ai_data = json.loads(ai_insight)
                    else:
                        ai_data = ai_insight
                    
                    msg += f"🤖 *AI Summary*: {ai_data.get('summary', 'N/A')}\n"
                    if 'trade_setup' in ai_data:
                        ts = ai_data['trade_setup']
                        msg += f"🎯 *Targets*: TP {ts.get('take_profit_1')} | SL {ts.get('stop_loss')}\n"
                except:
                    msg += f"🤖 *AI*: See Dashboard\n"
        
        msg += f"-------------------\n"
        msg += f"_Check dashboard for details._"
        
        await self.send_message(msg, priority="HIGH")

