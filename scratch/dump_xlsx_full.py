import pandas as pd

for filepath in ["Audit_Case_Scenario_Answers.xlsx", "DT_Case_Scenario_Answers.xlsx"]:
    try:
        df = pd.read_excel(filepath)
        print(f"=== {filepath} ===")
        print(df.head(10))
        print("-" * 50)
    except Exception as e:
        print(f"Error {filepath}: {e}")
