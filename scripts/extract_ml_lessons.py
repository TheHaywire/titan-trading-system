import pickle
import pandas as pd
import numpy as np
import os

MODEL_PATH = "titan_system/ml/signal_model.pkl"

def extract_lessons():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        return

    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    
    model = data['model']
    feature_names = data['feature_names']
    
    # Get feature importance (gain)
    importances = model.feature_importance(importance_type='gain')
    feat_imp = pd.DataFrame({'feature': feature_names, 'importance': importances})
    feat_imp = feat_imp.sort_values(by='importance', ascending=False)
    
    print("="*60)
    print("🧠 ML INTELLIGENCE LESSONS (FROM 2,374 TRADES)")
    print("="*60)
    print(feat_imp)
    
    print("\n--- Top 3 Market Drivers ---")
    for i in range(min(3, len(feat_imp))):
        row = feat_imp.iloc[i]
        print(f"{i+1}. {row['feature'].upper()}: Accounted for {row['importance']:.2f} gain in predictive accuracy.")

if __name__ == "__main__":
    extract_lessons()
