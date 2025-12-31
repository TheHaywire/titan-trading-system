"""Pytest configuration and shared fixtures."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlc_data():
    """
    Generate sample OHLC (Open, High, Low, Close) data for testing strategies.
    
    Returns 300 hourly candles starting from 2024-01-01.
    """
    dates = pd.date_range(start='2024-01-01', periods=300, freq='H')
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate realistic price data with trend
    base_price = 1.1000
    trend = np.linspace(0, 0.02, 300)  # Slight uptrend
    noise = np.cumsum(np.random.randn(300) * 0.0005)
    close_prices = base_price + trend + noise
    
    df = pd.DataFrame({
        'time': dates,
        'open': close_prices + np.random.randn(300) * 0.0002,
        'high': close_prices + np.abs(np.random.randn(300) * 0.0003),
        'low': close_prices - np.abs(np.random.randn(300) * 0.0003),
        'close': close_prices,
        'tick_volume': np.random.randint(100, 1000, 300),
        'spread': np.random.randint(1, 5, 300),
        'real_volume': np.random.randint(1000, 10000, 300)
    })
    
    return df


@pytest.fixture
def sample_trending_data():
    """Generate OHLC data with strong uptrend (high ADX)."""
    dates = pd.date_range(start='2024-01-01', periods=300, freq='H')
    
    np.random.seed(123)
    
    # Strong uptrend
    base_price = 1.1000
    trend = np.linspace(0, 0.05, 300)  # Strong 5% trend
    noise = np.cumsum(np.random.randn(300) * 0.0002)  # Less noise
    close_prices = base_price + trend + noise
    
    df = pd.DataFrame({
        'time': dates,
        'open': close_prices - np.random.rand(300) * 0.0001,
        'high': close_prices + np.random.rand(300) * 0.0002,
        'low': close_prices - np.random.rand(300) * 0.0002,
        'close': close_prices,
        'tick_volume': np.random.randint(200, 1500, 300),
        'spread': np.random.randint(1, 3, 300),
        'real_volume': np.random.randint(2000, 15000, 300)
    })
    
    return df


@pytest.fixture
def sample_ranging_data():
    """Generate OHLC data that's ranging (low ADX)."""
    dates = pd.date_range(start='2024-01-01', periods=300, freq='H')
    
    np.random.seed(456)
    
    # Ranging market with mean reversion
    base_price = 1.1000
    noise = np.sin(np.linspace(0, 20, 300)) * 0.01  # Oscillating
    noise += np.random.randn(300) * 0.0005  # Random noise
    close_prices = base_price + noise
    
    df = pd.DataFrame({
        'time': dates,
        'open': close_prices + np.random.randn(300) * 0.0002,
        'high': close_prices + np.abs(np.random.randn(300) * 0.0003),
        'low': close_prices - np.abs(np.random.randn(300) * 0.0003),
        'close': close_prices,
        'tick_volume': np.random.randint(50, 500, 300),
        'spread': np.random.randint(2, 6, 300),
        'real_volume': np.random.randint(500, 5000, 300)
    })
    
    return df


@pytest.fixture
def mock_account_info():
    """Mock MT5 account info."""
    return {
        'balance': 10000.0,
        'equity': 10050.0,
        'margin': 100.0,
        'free_margin': 9950.0,
        'margin_level': 10050.0,
        'profit': 50.0,
        'positions': []
    }


@pytest.fixture
def mock_account_with_positions():
    """Mock MT5 account info with open positions."""
    return {
        'balance': 10000.0,
        'equity': 10150.0,
        'margin': 500.0,
        'free_margin': 9650.0,
        'margin_level': 20.3,
        'profit': 150.0,
        'positions': [
            {'symbol': 'EURUSD', 'volume': 0.1, 'type': 'buy', 'profit': 50.0},
            {'symbol': 'GBPUSD', 'volume': 0.1, 'type': 'sell', 'profit': 100.0},
        ]
    }


@pytest.fixture
def strategy_config():
    """Default strategy configuration for testing."""
    return {
        'fast_period': 50,
        'slow_period': 200,
        'rsi_period': 14,
        'adx_threshold': 25
    }
