"""
Win Rate vs R:R Matrix (EPIC-03)
Generates the mathematical 'Edge Matrix' to show required win rates
for given R:R targets. Used for strategy validation.
"""

import pandas as pd
import numpy as np

def generate_edge_matrix():
    print("🧠 Generating Institutional Edge Matrix...")
    
    rr_ratios = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    win_rates = np.arange(0.10, 0.95, 0.05)
    
    data = []
    for wr in win_rates:
        row = {"Win Rate %": f"{wr*100:.0f}%"}
        for rr in rr_ratios:
            # Expectancy = (WR * Profit) - (LR * Loss)
            # Normalize Loss = 1 unit
            expectancy = (wr * rr) - ((1 - wr) * 1)
            row[f"R:R {rr}:1"] = "✅" if expectancy > 0 else "❌"
            # Add raw expectancy value for deep audit
            # row[f"Exp {rr}"] = round(expectancy, 2)
        data.append(row)

    df = pd.DataFrame(data)
    
    # Save as Markdown for GitHub documentation
    md_content = "# 📊 Institutional Edge Matrix\n\n"
    md_content += "This matrix defines the required win rate for various Risk:Reward ratios to achieve positive expectancy.\n\n"
    md_content += df.to_markdown(index=False)
    md_content += "\n\n*Key: ✅ = Positive Expectancy | ❌ = Negative Expectancy (Account Burn)*"
    
    with open("docs/institutional/EDGE_MATRIX.md", "w") as f:
        f.write(md_content)
    
    print("✅ Edge Matrix generated in docs/institutional/EDGE_MATRIX.md")

if __name__ == "__main__":
    generate_edge_matrix()
