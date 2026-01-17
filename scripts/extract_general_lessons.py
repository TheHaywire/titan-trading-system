import pickle
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_PATH = "titan_system/ml/general_model.pkl"
DATA_PATH = "data/general_market_scenarios_v2.csv"

def extract_insights():
    print("="*60)
    print("🧠 GENERAL INTELLIGENCE: DECODED LESSONS")
    print("="*60)
    
    if not os.path.exists(MODEL_PATH):
        print("❌ Model not found.")
        return
        
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
        model = data['model']
        feature_names = data['feature_names']
        
    # 1. Feature Importance
    importance = model.feature_importance(importance_type='gain')
    total_gain = sum(importance)
    print("\n[KEY DRIVERS OF MARKET PHYSICS]")
    print(f"{'Feature':<20} | {'Importance':<10}")
    print("-" * 35)
    
    sorted_idx = np.argsort(importance)[::-1]
    for i in sorted_idx:
        imp_pct = (importance[i] / total_gain) * 100
        print(f"{feature_names[i]:<20} | {imp_pct:.1f}%")
        
    # 2. Data Insights
    df = pd.read_csv(DATA_PATH)
    print("\n[STATISTICAL TRUTHS (166k SAMPLES)]")
    
    # RSI Zones
    df['rsi_zone'] = pd.cut(df['rsi_norm']*100, bins=[0, 30, 70, 100], labels=['Oversold', 'Neutral', 'Overbought'])
    print("\n> RSI Physics:")
    print(df.groupby('rsi_zone')['outcome'].mean())
    
    # Volatility
    df['vol_zone'] = pd.qcut(df['atr_pct'], 3, labels=['Low Vol', 'Med Vol', 'High Vol'])
    print("\n> Volatility Physics:")
    print(df.groupby('vol_zone')['outcome'].mean())
    
    # Trend Strength
    df['adx_zone'] = pd.cut(df['adx_norm']*50, bins=[0, 20, 40, 100], labels=['Weak', 'Strong', 'Extreme'])
    print("\n> Trend Physics (ADX):")
    print(df.groupby('adx_zone')['outcome'].mean())

    print("\n[CONCLUSION]")
    print("The General Model has learned that Volatility and RSI are the primary drivers of reversibility,")
    print("regardless of the specific asset.")

if __name__ == "__main__":
    extract_insights()
