import pandas as pd
df = pd.read_excel("Audit_Case_Scenario_Answers.xlsx")
for idx, row in df.head(5).iterrows():
    print(dict(row))
