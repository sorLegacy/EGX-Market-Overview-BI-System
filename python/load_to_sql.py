import os
import pyodbc
import pandas as pd
import numpy as np

SERVER = r"LEGACY\LEGACY"
DATABASE = "Sigma_Cap"
DRIVER = "{ODBC Driver 17 for SQL Server}"

CONN_STR = (
    f"Driver={DRIVER};"
    f"Server={SERVER};"
    f"Database={DATABASE};"
    f"Trusted_Connection=yes;"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
COMPUTED_DIR = os.path.join(SCRIPT_DIR, "computed_data")
SQL_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "SQL")

def execute_ddl(cursor, conn):
    # Only run DDL if fact tables do not exist yet
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'fact_market_breadth'")
    exists = cursor.fetchone()[0] > 0
    if exists:
        return
        
    ddl_file = os.path.join(SQL_DIR, "03_create_computed_database_schema.sql")
    if not os.path.exists(ddl_file):
        return
    with open(ddl_file, "r", encoding="utf-8") as f:
        sql_script = f.read()

    batches = [b.strip() for b in sql_script.split("GO") if b.strip()]
    for batch in batches:
        try:
            cursor.execute(batch)
            conn.commit()
        except Exception as e:
            print(f"Error executing batch: {e}")

def load_data(cursor, conn):
    print("\n--- Populating Tables from computed_data ---")
    
    # 1. fact_daily_investor_summary
    f_sum = os.path.join(COMPUTED_DIR, "Fact_Daily_Investor_Summary.csv")
    if os.path.exists(f_sum):
        df = pd.read_csv(f_sum)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_daily_investor_summary AS target
            USING (SELECT ? AS trading_date, ? AS egyptian_pct, ? AS arab_pct, ? AS foreign_pct,
                          ? AS local_institutions_pct, ? AS retail_pct, ? AS institutional_pct) AS src
            ON (target.trading_date = src.trading_date)
            WHEN MATCHED THEN
                UPDATE SET target.egyptian_pct = src.egyptian_pct,
                           target.arab_pct = src.arab_pct,
                           target.foreign_pct = src.foreign_pct,
                           target.local_institutions_pct = src.local_institutions_pct,
                           target.retail_pct = src.retail_pct,
                           target.institutional_pct = src.institutional_pct
            WHEN NOT MATCHED THEN
                INSERT (trading_date, egyptian_pct, arab_pct, foreign_pct, local_institutions_pct, retail_pct, institutional_pct)
                VALUES (src.trading_date, src.egyptian_pct, src.arab_pct, src.foreign_pct, src.local_institutions_pct, src.retail_pct, src.institutional_pct);
            """
            cursor.execute(sql, (
                str(r["Date"]), float(r["Egyptian_Pct"]), float(r["Arab_Pct"]),
                float(r["Foreign_Pct"]), float(r["Local_Institutions_Pct"]),
                float(r["Retail_Pct"]), float(r["Institutional_Pct"])
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_daily_investor_summary")

    # 2. fact_investors_distribution
    f_inv = os.path.join(COMPUTED_DIR, "Dim_Investors_Distribution_Normalized.csv")
    if os.path.exists(f_inv):
        df = pd.read_csv(f_inv)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_investors_distribution AS target
            USING (SELECT ? AS trading_date, ? AS nationality, ? AS category, ? AS buy_value_mn,
                          ? AS sell_value_mn, ? AS net_value_mn, ? AS turnover_mn, ? AS trading_pct) AS src
            ON (target.trading_date = src.trading_date AND target.nationality = src.nationality AND target.category = src.category)
            WHEN MATCHED THEN
                UPDATE SET target.buy_value_mn = src.buy_value_mn,
                           target.sell_value_mn = src.sell_value_mn,
                           target.net_value_mn = src.net_value_mn,
                           target.turnover_mn = src.turnover_mn,
                           target.trading_pct = src.trading_pct
            WHEN NOT MATCHED THEN
                INSERT (trading_date, nationality, category, buy_value_mn, sell_value_mn, net_value_mn, turnover_mn, trading_pct)
                VALUES (src.trading_date, src.nationality, src.category, src.buy_value_mn, src.sell_value_mn, src.net_value_mn, src.turnover_mn, src.trading_pct);
            """
            cursor.execute(sql, (
                str(r["Date"]), str(r["Nationality"]), str(r["Category"]),
                float(r["Buy_Value_Mn"]), float(r["Sell_Value_Mn"]),
                float(r["Net_Value_Mn"]), float(r["Turnover_Mn"]), float(r["Trading_Pct"])
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_investors_distribution")

    # 3. fact_market_breadth
    f_mb = os.path.join(COMPUTED_DIR, "Fact_Market_Breadth.csv")
    if os.path.exists(f_mb):
        df = pd.read_csv(f_mb)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_market_breadth AS target
            USING (SELECT ? AS trading_date, ? AS advancing_count, ? AS declining_count,
                          ? AS unchanged_count, ? AS total_stocks, ? AS ad_ratio) AS src
            ON (target.trading_date = src.trading_date)
            WHEN MATCHED THEN
                UPDATE SET target.advancing_count = src.advancing_count,
                           target.declining_count = src.declining_count,
                           target.unchanged_count = src.unchanged_count,
                           target.total_stocks = src.total_stocks,
                           target.ad_ratio = src.ad_ratio
            WHEN NOT MATCHED THEN
                INSERT (trading_date, advancing_count, declining_count, unchanged_count, total_stocks, ad_ratio)
                VALUES (src.trading_date, src.advancing_count, src.declining_count, src.unchanged_count, src.total_stocks, src.ad_ratio);
            """
            cursor.execute(sql, (
                str(r["Date"]), int(r["Advancing"]), int(r["Declining"]),
                int(r["Unchanged"]), int(r["Total"]),
                float(r["AD_Ratio"]) if pd.notna(r["AD_Ratio"]) else None
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_market_breadth")

    # 4. fact_sector_activity
    f_sec = os.path.join(COMPUTED_DIR, "Fact_Sector_Activity.csv")
    if os.path.exists(f_sec):
        df = pd.read_csv(f_sec)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_sector_activity AS target
            USING (SELECT ? AS trading_date, ? AS sector_name, ? AS turnover_mn,
                          ? AS direct_market_share_pct, ? AS computed_market_share_pct) AS src
            ON (target.trading_date = src.trading_date AND target.sector_name = src.sector_name)
            WHEN MATCHED THEN
                UPDATE SET target.turnover_mn = src.turnover_mn,
                           target.direct_market_share_pct = src.direct_market_share_pct,
                           target.computed_market_share_pct = src.computed_market_share_pct
            WHEN NOT MATCHED THEN
                INSERT (trading_date, sector_name, turnover_mn, direct_market_share_pct, computed_market_share_pct)
                VALUES (src.trading_date, src.sector_name, src.turnover_mn, src.direct_market_share_pct, src.computed_market_share_pct);
            """
            cursor.execute(sql, (
                str(r["Date"]), str(r["Sector_Name"]), float(r["Turnover_Mn"]),
                float(r["Direct_Market_Share_Pct"]), float(r["Computed_Market_Share_Pct"]) if pd.notna(r["Computed_Market_Share_Pct"]) else None
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_sector_activity")

    # 5. fact_block_trades
    f_bt = os.path.join(COMPUTED_DIR, "Fact_Block_Trades.csv")
    if os.path.exists(f_bt):
        df = pd.read_csv(f_bt)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_block_trades AS target
            USING (SELECT ? AS trading_date, ? AS share_name, ? AS quantity, ? AS value_egp,
                          ? AS trade_count, ? AS avg_price, ? AS block_pct_of_market) AS src
            ON (target.trading_date = src.trading_date AND target.share_name = src.share_name 
                AND target.quantity = src.quantity AND target.value_egp = src.value_egp)
            WHEN MATCHED THEN
                UPDATE SET target.trade_count = src.trade_count,
                           target.avg_price = src.avg_price,
                           target.block_pct_of_market = src.block_pct_of_market
            WHEN NOT MATCHED THEN
                INSERT (trading_date, share_name, quantity, value_egp, trade_count, avg_price, block_pct_of_market)
                VALUES (src.trading_date, src.share_name, src.quantity, src.value_egp, src.trade_count, src.avg_price, src.block_pct_of_market);
            """
            cursor.execute(sql, (
                str(r["Date"]), str(r["Share_Name"]), int(r["Quantity"]),
                float(r["Value_EGP"]), int(r["Trade_Count"]),
                float(r["Avg_Price"]),
                float(r["Block_Pct_Of_Market"]) if pd.notna(r["Block_Pct_Of_Market"]) else None
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_block_trades")

    # 6. fact_market_indices
    f_idx = os.path.join(COMPUTED_DIR, "Fact_Market_Indices.csv")
    if os.path.exists(f_idx):
        df = pd.read_csv(f_idx)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_market_indices AS target
            USING (SELECT ? AS trading_date, ? AS index_name, ? AS last_value,
                          ? AS change_pts, ? AS change_pct) AS src
            ON (target.trading_date = src.trading_date AND target.index_name = src.index_name)
            WHEN MATCHED THEN
                UPDATE SET target.last_value = src.last_value,
                           target.change_pts = src.change_pts,
                           target.change_pct = src.change_pct
            WHEN NOT MATCHED THEN
                INSERT (trading_date, index_name, last_value, change_pts, change_pct)
                VALUES (src.trading_date, src.index_name, src.last_value, src.change_pts, src.change_pct);
            """
            cursor.execute(sql, (
                str(r["Date"]), str(r["Name"]), float(r["Last"]),
                float(r["Ch"]) if pd.notna(r["Ch"]) else None,
                float(r["Ch%"]) if pd.notna(r["Ch%"]) else None
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_market_indices")

    # 7. fact_stock_leaderboards
    f_lb = os.path.join(COMPUTED_DIR, "Fact_Stock_Leaderboards.csv")
    if os.path.exists(f_lb):
        df = pd.read_csv(f_lb)
        for _, r in df.iterrows():
            sql = """
            MERGE dbo.fact_stock_leaderboards AS target
            USING (SELECT ? AS trading_date, ? AS board_type, ? AS ticker, ? AS last_price,
                          ? AS change_pts, ? AS change_pct, ? AS turnover_mn, ? AS volume_mn,
                          ? AS high_price, ? AS low_price) AS src
            ON (target.trading_date = src.trading_date AND target.board_type = src.board_type AND target.ticker = src.ticker)
            WHEN MATCHED THEN
                UPDATE SET target.last_price = src.last_price,
                           target.change_pts = src.change_pts,
                           target.change_pct = src.change_pct,
                           target.turnover_mn = src.turnover_mn,
                           target.volume_mn = src.volume_mn,
                           target.high_price = src.high_price,
                           target.low_price = src.low_price
            WHEN NOT MATCHED THEN
                INSERT (trading_date, board_type, ticker, last_price, change_pts, change_pct, turnover_mn, volume_mn, high_price, low_price)
                VALUES (src.trading_date, src.board_type, src.ticker, src.last_price, src.change_pts, src.change_pct, src.turnover_mn, src.volume_mn, src.high_price, src.low_price);
            """
            to_val = float(r["T/O (Mn)"]) if "T/O (Mn)" in r and pd.notna(r["T/O (Mn)"]) else None
            vol_val = float(r["Volume"]) if "Volume" in r and pd.notna(r["Volume"]) else None
            hi_val = float(r["High"]) if "High" in r and pd.notna(r["High"]) else None
            lo_val = float(r["Low"]) if "Low" in r and pd.notna(r["Low"]) else None
            cursor.execute(sql, (
                str(r["Date"]), str(r["Board_Type"]), str(r["Name"]),
                float(r["Last"]) if pd.notna(r["Last"]) else None,
                float(r["Ch"]) if pd.notna(r["Ch"]) else None,
                float(r["Ch%"]) if pd.notna(r["Ch%"]) else None,
                to_val, vol_val, hi_val, lo_val
            ))
        conn.commit()
        print(f"Loaded {len(df)} rows into fact_stock_leaderboards")

def main():
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        print(f"Connected to SQL Server instance: {SERVER}, Database: {DATABASE}")
        execute_ddl(cursor, conn)
        load_data(cursor, conn)
        print("\nAll computed data successfully loaded into SQL Server!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    main()
