"""
Centralized configuration management using Pydantic Settings.

This module loads all configuration from environment variables (.env file),
providing type safety and validation.

Usage:
    from config.settings import settings
    
    print(settings.mt5_login)
    print(settings.trading_symbols)
"""

from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by setting the corresponding
    environment variable (case-insensitive).
    """
    
    # System Version
    VERSION: str = "2.0.0"
    
    # ===== MT5 Configuration =====
    mt5_login: int
    mt5_password: str
    mt5_server: str
    
    # ===== Email Configuration =====
    emailjs_service_id: str
    emailjs_template_id: str
    emailjs_public_key: str
    emailjs_private_key: str
    emailjs_user_email: str
    
    # ===== Google AI Configuration =====
    google_api_key: str
    google_project_id: str
    
    # ===== Telegram Configuration =====
    telegram_bot_token: str = "7611636283:AAFKeBov2L66Qn6-T8U_z7t41I_V1yE9P2Q"
    telegram_chat_id: str = "1791285227"
    
    # ===== Trading Parameters =====
    risk_percentage: float = 5.0  # Aggressive Growth Mode
    max_daily_loss_percent: float = 15.0 # Wider Stop
    adx_threshold: int = 20
    
    # ===== System Configuration =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    db_path: str = str(Path(__file__).parent.parent / "titan_system" / "titan.db")
    
    # ===== Trading Symbols =====
    trading_symbols: List[str] = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP"
    ]
    
    # ===== QuantAI Agent Configuration =====
    trading_mode: str = "LIVE"  # LIVE | PAPER | BACKTEST
    
    # Signal Deduplication & Throttling
    signal_cooldown_minutes: int = 60  # Min time between signals for same symbol
    max_signals_per_hour: int = 5      # Max signals per hour per symbol
    max_trades_per_session: int = 3    # Max trades per session per symbol
    
    # Memory Settings
    short_term_memory_size: int = 100  # Recent signals to keep in memory
    
    # Trade State Thresholds
    excellent_score_threshold: int = 90   # EXCELLENT: 90-100
    acceptable_score_threshold: int = 70  # ACCEPTABLE: 70-89
    warning_score_threshold: int = 50     # WARNING: 50-69, <50 = INVALID
    
    # ===== Feature Flags =====
    enable_ai_analysis: bool = True
    enable_email_notifications: bool = True
    enable_trading: bool = True  # Master switch for trading
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow comma-separated values for lists
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            """Custom parser for environment variables."""
            if field_name == 'trading_symbols':
                # Parse comma-separated string into list
                return [s.strip() for s in raw_val.split(',') if s.strip()]
            return raw_val


# ===== Global Settings Instance =====
try:
    settings = Settings()
    print("✅ Configuration loaded successfully from .env")
    print(f"   MT5 Account: {settings.mt5_login}")
    print(f"   Trading Symbols: {len(settings.trading_symbols)} symbols")
    print(f"   API: {settings.api_host}:{settings.api_port}")
except Exception as e:
    print(f"❌ Failed to load configuration: {e}")
    print("\n⚠️  Please ensure:")
    print("   1. .env file exists in project root")
    print("   2. All required variables are set")
    print("   3. Values are in correct format")
    print("\nYou can copy .env.example to .env and fill in your credentials.")
    raise


# ===== Backward Compatibility Layer =====
# These aliases maintain compatibility with old config.py imports
MT5_LOGIN = settings.mt5_login
MT5_PASSWORD = settings.mt5_password
MT5_SERVER = settings.mt5_server
EMAILJS_SERVICE_ID = settings.emailjs_service_id
EMAILJS_TEMPLATE_ID = settings.emailjs_template_id
EMAILJS_PUBLIC_KEY = settings.emailjs_public_key
EMAILJS_PRIVATE_KEY = settings.emailjs_private_key
EMAILJS_USER_EMAIL = settings.emailjs_user_email
GOOGLE_API_KEY = settings.google_api_key
GOOGLE_PROJECT_ID = settings.google_project_id
