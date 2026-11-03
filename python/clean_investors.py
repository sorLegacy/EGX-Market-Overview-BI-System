import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
csv_path = os.path.join(DATA_DIR, "Investors_Distribution.csv")

df = pd.read_csv(csv_path)

segments = [
    ("Egyptian Ret.", "Egyptian", "Retail"),
    ("Egyptian Inst.", "Egyptian", "Institutional"),
    ("Arab Ret.", "Arab", "Retail"),
    ("Arab Inst.", "Arab", "Institutional"),
    ("Foreign Ret.", "Foreign", "Retail"),
    ("Foreign Inst.", "Foreign", "Institutional"),
]

def clean_val(v):
    if pd.isna(v): return 0.0
    return float(str(v).replace(",", "").replace("%", "").strip())

records = []
for t_date in df["Date"].dropna().unique():
    t_date_str = str(t_date)
    day_df = df[df["Date"] == t_date].set_index("Trade")
    for col_name, nat, cat in segments:
        if col_name in day_df.columns:
            buy_val = clean_val(day_df.loc["Buy (M)", col_name]) if "Buy (M)" in day_df.index else 0.0
            sell_val = clean_val(day_df.loc["Sell (M)", col_name]) if "Sell (M)" in day_df.index else 0.0
            net_val = clean_val(day_df.loc["Net (M)", col_name]) if "Net (M)" in day_df.index else (buy_val - sell_val)
            turnover_val = clean_val(day_df.loc["Turnover (M)", col_name]) if "Turnover (M)" in day_df.index else (buy_val + sell_val)
            trading_pct = clean_val(day_df.loc["Trading %", col_name]) if "Trading %" in day_df.index else 0.0
            records.append({
                "Date": t_date_str,
                "Nationality": nat,
                "Category": cat,
                "Buy_Value_Mn": buy_val,
                "Sell_Value_Mn": sell_val,
                "Net_Value_Mn": net_val,
                "Turnover_Mn": turnover_val,
                "Trading_Pct": trading_pct
            })

clean_df = pd.DataFrame(records).drop_duplicates()
cleaned_csv_path = os.path.join(DATA_DIR, "Investors_Distribution_Cleaned.csv")
clean_df.to_csv(cleaned_csv_path, index=False)
print(f"Generated Investors_Distribution_Cleaned.csv with {len(clean_df)} rows across {clean_df['Date'].nunique()} dates.")
