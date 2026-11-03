import os
import pandas as pd
import numpy as np

def clean_val(val):
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).replace(',', '').replace('%', '').strip()
    try:
        return float(s)
    except ValueError:
        return 0.0

def process_data(data_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. INVESTORS DISTRIBUTION (Scopes 1 & 2)
    # -------------------------------------------------------------
    inv_file = os.path.join(data_dir, "Investors_Distribution.csv")
    if os.path.exists(inv_file):
        df_raw = pd.read_csv(inv_file)
        
        # Columns mapping to (nationality, category)
        target_segments = [
            ("Egyptian Ret.", "Egyptian", "Retail"),
            ("Egyptian Inst.", "Egyptian", "Institutional"),
            ("Arab Ret.", "Arab", "Retail"),
            ("Arab Inst.", "Arab", "Institutional"),
            ("Foreign Ret.", "Foreign", "Retail"),
            ("Foreign Inst.", "Foreign", "Institutional")
        ]
        
        normalized_rows = []
        summary_rows = []
        
        for date_val, group in df_raw.groupby("Date"):
            metrics = {}
            for _, r in group.iterrows():
                trade_type = str(r["Trade"]).strip()
                if "Buy" in trade_type:
                    metrics["Buy"] = r
                elif "Sell" in trade_type:
                    metrics["Sell"] = r
                elif "Net" in trade_type:
                    metrics["Net"] = r
                elif "Turnover" in trade_type:
                    metrics["Turnover"] = r
                elif "%" in trade_type:
                    metrics["Trading_Pct"] = r
            
            day_total_buy = 0.0
            day_total_sell = 0.0
            day_total_to = 0.0
            
            # Segment level records
            for col_name, nat, cat in target_segments:
                b = clean_val(metrics.get("Buy", {}).get(col_name, 0.0))
                s = clean_val(metrics.get("Sell", {}).get(col_name, 0.0))
                # Net Buy/Sell = [Buy Value] - [Sell Value]
                computed_net = round(b - s, 2)
                t_over = clean_val(metrics.get("Turnover", {}).get(col_name, 0.0))
                pct = clean_val(metrics.get("Trading_Pct", {}).get(col_name, 0.0))
                
                normalized_rows.append({
                    "Date": str(date_val),
                    "Nationality": nat,
                    "Category": cat,
                    "Buy_Value_Mn": b,
                    "Sell_Value_Mn": s,
                    "Net_Value_Mn": computed_net,
                    "Turnover_Mn": t_over,
                    "Trading_Pct": pct
                })
            
            # Now let's calculate the daily investor computed aggregates:
            # - Egyptian Investors % = Egyptian Ret. % + Egyptian Inst. %
            # - Arab Investors % = Arab Ret. % + Arab Inst. %
            # - Foreign Investors % = Foreign Ret. % + Foreign Inst. %
            # - Local Institutions % = Egyptian Inst. %
            # - Retail vs Inst. Split = Total Ret. % vs Total Inst. %
            pct_row = metrics.get("Trading_Pct", {})
            eg_ret_pct = clean_val(pct_row.get("Egyptian Ret.", 0.0))
            eg_inst_pct = clean_val(pct_row.get("Egyptian Inst.", 0.0))
            arab_ret_pct = clean_val(pct_row.get("Arab Ret.", 0.0))
            arab_inst_pct = clean_val(pct_row.get("Arab Inst.", 0.0))
            for_ret_pct = clean_val(pct_row.get("Foreign Ret.", 0.0))
            for_inst_pct = clean_val(pct_row.get("Foreign Inst.", 0.0))
            tot_ret_pct = clean_val(pct_row.get("Total Ret.", 0.0))
            tot_inst_pct = clean_val(pct_row.get("Total Inst.", 0.0))
            
            summary_rows.append({
                "Date": str(date_val),
                "Egyptian_Pct": round(eg_ret_pct + eg_inst_pct, 2),
                "Arab_Pct": round(arab_ret_pct + arab_inst_pct, 2),
                "Foreign_Pct": round(for_ret_pct + for_inst_pct, 2),
                "Local_Institutions_Pct": round(eg_inst_pct, 2),
                "Retail_Pct": round(tot_ret_pct, 2),
                "Institutional_Pct": round(tot_inst_pct, 2)
            })
            
        df_norm = pd.DataFrame(normalized_rows)
        df_norm.to_csv(os.path.join(output_dir, "Dim_Investors_Distribution_Normalized.csv"), index=False)
        print(f"Generated Dim_Investors_Distribution_Normalized.csv: {len(df_norm)} rows")
        
        df_sum = pd.DataFrame(summary_rows)
        df_sum.to_csv(os.path.join(output_dir, "Fact_Daily_Investor_Summary.csv"), index=False)
        print(f"Generated Fact_Daily_Investor_Summary.csv: {len(df_sum)} rows")

    # -------------------------------------------------------------
    # 2. MARKET BREADTH (Scope 3)
    # Advancing, Declining, Unchanged, AD_Ratio
    # -------------------------------------------------------------
    breadth_file = os.path.join(data_dir, "Market_Breadth.csv")
    if os.path.exists(breadth_file):
        df_mb = pd.read_csv(breadth_file)
        # Ensure AD_Ratio computed: [Advancing Stocks] / [Declining Stocks]
        df_mb["Advancing"] = pd.to_numeric(df_mb["Advancing"], errors="coerce").fillna(0).astype(int)
        df_mb["Declining"] = pd.to_numeric(df_mb["Declining"], errors="coerce").fillna(0).astype(int)
        df_mb["Unchanged"] = pd.to_numeric(df_mb["Unchanged"], errors="coerce").fillna(0).astype(int)
        df_mb["Total"] = df_mb["Advancing"] + df_mb["Declining"] + df_mb["Unchanged"]
        df_mb["AD_Ratio"] = np.where(df_mb["Declining"] > 0, (df_mb["Advancing"] / df_mb["Declining"]).round(4), np.nan)
        df_mb.to_csv(os.path.join(output_dir, "Fact_Market_Breadth.csv"), index=False)
        print(f"Generated Fact_Market_Breadth.csv: {len(df_mb)} rows")

    # -------------------------------------------------------------
    # 3. SECTOR ACTIVITY (Scope 4)
    # Sector Name, Sector Turnover, Sector Market Share %
    # -------------------------------------------------------------
    sector_file = os.path.join(data_dir, "Sector_Activity.csv")
    if os.path.exists(sector_file):
        df_sec = pd.read_csv(sector_file)
        # Standardize columns
        df_sec["Turnover_Mn"] = df_sec["T/O (EGP Mn)"].apply(clean_val)
        df_sec["Mkt_Pct"] = df_sec["Mkt %"].apply(clean_val)
        
        # Also re-verify/compute market share per day
        computed_secs = []
        for date_val, group in df_sec.groupby("Date"):
            total_sec_to = group["Turnover_Mn"].sum()
            g = group.copy()
            g["Computed_Market_Share_Pct"] = (g["Turnover_Mn"] / total_sec_to * 100).round(2)
            computed_secs.append(g)
            
        df_sec_final = pd.concat(computed_secs, ignore_index=True)
        # Rename neatly
        df_sec_final = df_sec_final[["Date", "Sector Name", "Turnover_Mn", "Mkt_Pct", "Computed_Market_Share_Pct"]].rename(
            columns={"Sector Name": "Sector_Name", "Mkt_Pct": "Direct_Market_Share_Pct"}
        )
        df_sec_final.to_csv(os.path.join(output_dir, "Fact_Sector_Activity.csv"), index=False)
        print(f"Generated Fact_Sector_Activity.csv: {len(df_sec_final)} rows")

    # -------------------------------------------------------------
    # 4. BLOCK TRADES (Scope 5)
    # Ticker, Quantity, Value EGP, Deals, Avg Price, Block % of Market
    # -------------------------------------------------------------
    bt_file = os.path.join(data_dir, "Block_Trades.csv")
    if os.path.exists(bt_file):
        df_bt = pd.read_csv(bt_file)
        df_bt["Quantity"] = df_bt["Qty."].apply(clean_val).astype(np.int64)
        df_bt["Value_EGP"] = df_bt["Value EGP"].apply(clean_val)
        df_bt["Trade_Count"] = pd.to_numeric(df_bt["Count"], errors="coerce").fillna(1).astype(int)
        
        # Avg Block Deal Price = Value EGP / Qty.
        df_bt["Avg_Price"] = np.where(df_bt["Quantity"] > 0, (df_bt["Value_EGP"] / df_bt["Quantity"]).round(4), 0.0)
        
        # Get total daily market turnover in EGP from Sector_Activity
        daily_market_to = {}
        if os.path.exists(sector_file):
            for date_val, grp in pd.read_csv(sector_file).groupby("Date"):
                daily_market_to[str(date_val)] = grp["T/O (EGP Mn)"].apply(clean_val).sum() * 1_000_000 # EGP
                
        # Block % of Market = Block Value / Total Market Turnover
        def calc_block_mkt_pct(row):
            d = str(row["Date"])
            tot_to = daily_market_to.get(d, 0.0)
            if tot_to > 0:
                return round((row["Value_EGP"] / tot_to) * 100, 4)
            return np.nan
            
        df_bt["Block_Pct_Of_Market"] = df_bt.apply(calc_block_mkt_pct, axis=1)
        
        df_bt_final = df_bt[["Date", "Share Name", "Quantity", "Value_EGP", "Trade_Count", "Avg_Price", "Block_Pct_Of_Market"]].rename(
            columns={"Share Name": "Share_Name"}
        )
        df_bt_final.to_csv(os.path.join(output_dir, "Fact_Block_Trades.csv"), index=False)
        print(f"Generated Fact_Block_Trades.csv: {len(df_bt_final)} rows")

    # -------------------------------------------------------------
    # 5. MARKET INDICES & LEADERBOARDS
    # -------------------------------------------------------------
    idx_file = os.path.join(data_dir, "Indices.csv")
    if os.path.exists(idx_file):
        df_idx = pd.read_csv(idx_file)
        df_idx.to_csv(os.path.join(output_dir, "Fact_Market_Indices.csv"), index=False)
        print(f"Generated Fact_Market_Indices.csv: {len(df_idx)} rows")

    boards = ["Turnover", "Volume", "Best Performers", "Worst Performers", "Largest Fluctuation"]
    all_boards = []
    for b in boards:
        b_file = os.path.join(data_dir, f"{b}.csv")
        if os.path.exists(b_file):
            b_df = pd.read_csv(b_file)
            b_df["Board_Type"] = b
            all_boards.append(b_df)
    if all_boards:
        df_lb = pd.concat(all_boards, ignore_index=True)
        df_lb.to_csv(os.path.join(output_dir, "Fact_Stock_Leaderboards.csv"), index=False)
        print(f"Generated Fact_Stock_Leaderboards.csv: {len(df_lb)} rows")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
    src = os.path.join(script_dir, "data")
    dest = os.path.join(script_dir, "computed_data")
    process_data(src, dest)
