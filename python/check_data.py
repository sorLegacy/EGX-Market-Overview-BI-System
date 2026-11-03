import pandas as pd
import numpy as np
import os

data_dir = "Project 2/python/data"

print("--- Investors Distribution Analysis ---")
df_inv = pd.read_csv(os.path.join(data_dir, "Investors_Distribution.csv"))
print(df_inv.head(10))

print("\n--- Block Trades Analysis ---")
df_bt = pd.read_csv(os.path.join(data_dir, "Block_Trades.csv"))
print(df_bt.head(5))

print("\n--- Sector Activity Analysis ---")
df_sec = pd.read_csv(os.path.join(data_dir, "Sector_Activity.csv"))
print(df_sec.head(5))

print("\n--- Market Breadth Analysis ---")
df_mb = pd.read_csv(os.path.join(data_dir, "Market_Breadth.csv"))
print(df_mb.head(5))
