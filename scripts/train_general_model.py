import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.ml.signal_filter import SignalFilter

DATA_PATH = "data/general_market_scenarios_v2.csv"

def train_general_model():
    print("="*60)
    print("🧠 TITAN HYBRID INTELLIGENCE: GENERAL PHYSICS TRAINING")
    print("="*60)
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file {DATA_PATH} not found.")
        print("Run scripts/generate_synthetic_training_data.py first.")
        return
        
    print(f"📂 Loading Synthetic Dataset: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"   Loaded {len(df)} samples.")
    
    # Feature Validation
    required_features = [
        'rsi_norm', 'adx_norm', 'ema_diff', 'atr_pct', 'range_position',
        'direction_buy', 'hour_sin', 'hour_cos', 
        'session_london', 'session_ny', 'candlestick_score'
    ]
    
    # Add missing dummy columns if needed (regime etc) to match Personal Model Schema
    # The General Simulation didn't calculate regimes perfectly, so we'll mock them 
    # as 0 (not used heavily by General model anyway, which focuses on Physics)
    for col in ['regime_trending', 'regime_mean_rev', 'regime_high_vol', 'score_norm']:
        if col not in df.columns:
            df[col] = 0
            
    print("⚙️  Training LightGBM [General] Model...")
    
    sf = SignalFilter()
    accuracy = sf.train(df, target_col='outcome', model_type='general')
    
    print("-" * 60)
    print(f"✅ GENERAL MODEL TRAINED")
    print(f"   Test Accuracy: {accuracy:.2%}")
    print(f"   Saved to: titan_system/ml/general_model.pkl")
    print("="*60)
    print("🚀 HYBRID INTELLIGENCE ACTIVATED: Pure History + General Physics")

if __name__ == "__main__":
    train_general_model()
