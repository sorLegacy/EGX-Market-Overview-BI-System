import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# 1. Fetch Page and Date
URL = "https://www.sigma-cap.com/main/x_market_page.overview?u_sess="
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")
date = pd.to_datetime("today").strftime("%Y-%m-%d")


# 2. General Helper for tblS2 Tables (Same approach as original)
def parse_tbls2_table(table_tag, date_val):
    header_tr = table_tag.find("tr", class_="trheading")
    if not header_tr:
        return pd.DataFrame()
    
    headers = [td.get_text(strip=True) for td in header_tr.find_all("td")]
    num_cols = len(headers)
    
    # Get data cells (skipping the header cells)
    data_tds = table_tag.find_all("td")[num_cols:]
    cell_values = [td.get_text(strip=True) for td in data_tds]
    
    # Chunk into rows
    rows = [cell_values[i:i + num_cols] for i in range(0, len(cell_values), num_cols)]
    df = pd.DataFrame(rows, columns=headers)
    
    # Clean numbers (remove commas and %)
    for col in df.columns:
        if col != "Name":
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df["Date"] = date_val
    return df


# 3. Individual Table Extraction Functions

def scrape_indices(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[0], date_val)


def scrape_turnover(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[1], date_val)


def scrape_volume(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[2], date_val)


def scrape_best_performers(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[3], date_val)


def scrape_worst_performers(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[4], date_val)


def scrape_largest_fluctuation(soup, date_val):
    tables = soup.find_all("table", class_="tblS2")
    return parse_tbls2_table(tables[5], date_val)


def scrape_investors_distribution(soup, date_val):
    all_tables = soup.find_all("table")
    t15 = all_tables[15]
    headers = [
        "Trade",
        "Egyptian Ret.",
        "Egyptian Inst.",
        "Arab Ret.",
        "Arab Inst.",
        "Foreign Ret.",
        "Foreign Inst.",
        "Total Ret.",
        "Total Inst."
    ]
    data_rows = []
    for r in t15.find_all("tr")[2:]:
        tds = [td.get_text(strip=True) for td in r.find_all(["td", "th"])]
        if len(tds) == 9 and tds[0] in ["Buy (M)", "Sell (M)", "Net (M)", "Turnover (M)", "Trading %"]:
            data_rows.append(tds)
    df = pd.DataFrame(data_rows, columns=headers)
    df["Date"] = date_val
    return df


def scrape_block_trades(soup, date_val):
    all_tables = soup.find_all("table")
    t16 = all_tables[16]
    t16_rows = t16.find_all("tr")
    headers = [td.get_text(strip=True) for td in t16_rows[0].find_all(["td", "th"]) if td.get_text(strip=True)]
    data_rows = []
    for r in t16_rows[1:]:
        tds = [td.get_text(strip=True) for td in r.find_all(["td", "th"]) if td.get_text(strip=True)]
        if len(tds) == len(headers):
            data_rows.append(tds)
    df = pd.DataFrame(data_rows, columns=headers)
    df["Date"] = date_val
    return df


def scrape_sector_activity(soup, date_val):
    all_tables = soup.find_all("table")
    t17 = all_tables[17]
    t17_rows = t17.find_all("tr")
    headers = [td.get_text(strip=True) for td in t17_rows[0].find_all(["td", "th"]) if td.get_text(strip=True)]
    data_rows = []
    for r in t17_rows[1:]:
        tds = [td.get_text(strip=True) for td in r.find_all(["td", "th"]) if td.get_text(strip=True)]
        if len(tds) == len(headers):
            data_rows.append(tds)
    df = pd.DataFrame(data_rows, columns=headers)
    df["Date"] = date_val
    return df


def scrape_market_breadth(soup, date_val):
    body = soup.find("div", id="adv_dec_body")
    if not body:
        return pd.DataFrame()

    values = []
    for span in body.find_all("span", style="float:right;")[0:3]:
        num_span = span.find_all("span", class_="num")
        values.append(int(num_span[0].get_text(strip=True)) if num_span else 0)

    # Total = Advancing + Declining + Unchanged
    values.append(values[0] + values[1] + values[2])

    headers = []
    for div in body.find_all("div", class_="chart_desc")[0:4]:
        headers.append("".join(char for char in div.get_text(strip=True) if char.isalpha()))

    data = dict(zip(headers, values))
    # Calculate Advance/Decline Ratio (Advancing / Declining) as per Scope 3 requirements
    data["AD_Ratio"] = round(values[0] / values[1], 2) if values[1] > 0 else None
    data["Date"] = date_val
    return pd.DataFrame([data])


# 4. Safe Append / Update Function (Prevents Duplication by Date)
def is_market_closed_or_unchanged(new_dfs, data_dir, today_date):
    indices_path = os.path.join(data_dir, "Indices.csv")
    if not os.path.exists(indices_path) or os.path.getsize(indices_path) == 0:
        return False, None
    try:
        existing_df = pd.read_csv(indices_path)
        if "Date" not in existing_df.columns or "Last" not in existing_df.columns:
            return False, None
        
        # Get prior recorded dates (excluding today)
        prior_dates = sorted([str(d) for d in existing_df["Date"].dropna().unique() if str(d) != str(today_date)])
        if not prior_dates:
            return False, None
        
        last_date = prior_dates[-1]
        prev_indices = existing_df[existing_df["Date"].astype(str) == last_date].sort_values("Name").reset_index(drop=True)
        curr_indices = new_dfs["Indices"].sort_values("Name").reset_index(drop=True)
        
        if len(prev_indices) == len(curr_indices) and len(curr_indices) > 0:
            cols = [c for c in ["Last", "Ch", "Ch%"] if c in prev_indices.columns and c in curr_indices.columns]
            prev_vals = prev_indices[cols].round(2).to_dict()
            curr_vals = curr_indices[cols].round(2).to_dict()
            if prev_vals == curr_vals:
                return True, last_date
    except Exception as e:
        print(f"Market comparison error: {e}")
    return False, None


def save_or_append_csv(df, file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            existing_df = pd.read_csv(file_path)
            
            # If the file already has rows for today's Date, remove them first to prevent duplicates
            if "Date" in existing_df.columns and "Date" in df.columns:
                target_dates = [str(d) for d in df["Date"].unique()]
                existing_df = existing_df[~existing_df["Date"].astype(str).isin(target_dates)]
            
            # Combine historical days with today's new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv(file_path, index=False)
            print(f"Updated {os.path.basename(file_path)} | Total rows: {len(combined_df)}")
        except PermissionError:
            print(f"WARNING: Permission denied for {os.path.basename(file_path)}. Please close Excel if it is open!")
        except Exception as e:
            df.to_csv(file_path, index=False)
            print(f"Overwrote {os.path.basename(file_path)} | Rows: {len(df)}")
    else:
        df.to_csv(file_path, index=False)
        print(f"Created {os.path.basename(file_path)} | Rows: {len(df)}")


# 5. Scrape All Tables & Save / Append
if __name__ == "__main__":
    dfs = {
        "Indices": scrape_indices(soup, date),
        "Turnover": scrape_turnover(soup, date),
        "Volume": scrape_volume(soup, date),
        "Best Performers": scrape_best_performers(soup, date),
        "Worst Performers": scrape_worst_performers(soup, date),
        "Largest Fluctuation": scrape_largest_fluctuation(soup, date),
        "Investors_Distribution": scrape_investors_distribution(soup, date),
        "Block_Trades": scrape_block_trades(soup, date),
        "Sector_Activity": scrape_sector_activity(soup, date),
        "Market_Breadth": scrape_market_breadth(soup, date),
    }

    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Check if market data today is identical to the previous trading day (e.g. weekend or holiday)
    is_unchanged, prev_date = is_market_closed_or_unchanged(dfs, data_dir, date)
    if is_unchanged:
        print(f"[SKIP] Market data today ({date}) is identical to previous trading day ({prev_date}).")
        print("Market was closed (weekend/holiday). Skipping save to CSV and database.")
        exit(0)

    for name, df in dfs.items():
        csv_path = os.path.join(data_dir, f"{name}.csv")
        save_or_append_csv(df, csv_path)
