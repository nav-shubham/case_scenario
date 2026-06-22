import os
import pandas as pd

for filename in os.listdir("."):
    if filename.endswith(".xlsx"):
        filepath = filename
        try:
            df = pd.read_excel(filepath)
            print(f"=== {filename} ===")
            print(f"Columns: {list(df.columns)}")
            print(df.head(2))
            print("-" * 50)
        except Exception as e:
            print(f"Error {filename}: {e}")
