
import google.generativeai as genai
import logging
import json
from config.settings import settings

logger = logging.getLogger("Titan.AI_Analyst")

class AIAnalyst:
    """
    Interfaces with Google Gemini (via google-generativeai) to provide
    human-like market analysis based on technical data.
    """
    
    def __init__(self):
        if not settings.google_api_key:
            logger.warning("Google API Key not found. AI Analysis disabled.")
            self.enabled = False
            return
            
        try:
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
            self.enabled = True
            logger.info("✅ Gemini AI Analyst Initialized")
        except Exception as e:
            logger.error(f"Failed to init Gemini: {e}")
            self.enabled = False

    async def analyze(self, symbol: str, technical_data: dict) -> str:
        """
        Sends technical summary to Gemini and gets a trading insight.
        """
        if not self.enabled:
            return "AI Analysis Disabled (Check API Key)"

        # Construct a concise prompt to save tokens/latency
        try:
            # Run blocking I/O in executor
            import asyncio
            
            # New "InnoTrade-Style" Prompt
            prompt = f"""
            Act as an expert financial analyst for InnoTrade. Analyze {symbol} based on this technical data:
            {json.dumps(technical_data, indent=2)}
            
            Produce a detailed JSON analysis matching this structure exactly (no markdown formatting, just raw JSON):
            {{
                "summary": "One concise sentence summary of the market state.",
                "bias": "BULLISH/BEARISH/NEUTRAL",
                "confidence": 0-100,
                "trade_setup": {{
                    "entry_zone": "Price range for entry",
                    "stop_loss": "Specific price level",
                    "take_profit_1": "Conservative target",
                    "take_profit_2": "Extended target"
                }},
                "key_drivers": ["Reason 1", "Reason 2"],
                "risk_factors": ["Risk 1", "Risk 2"],
                "execution_plan": "Step-by-step instruction (e.g., 'Wait for pullback to X, then enter.')"
            }}
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            # Clean response to ensure valid JSON (remove ```json wrappers if present)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return text
            
        except Exception as e:
            logger.error(f"AI Generation Failed: {e}")
            return json.dumps({"bias": "NEUTRAL", "summary": "AI Unavailable"})

