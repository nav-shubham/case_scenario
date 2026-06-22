import sys
import pandas as pd
sys.path.append(".")
from scratch.test_extractor import extract_answers

data = extract_answers("inter case scanario/Paper 1 Advanced Accounting.pdf")
df = pd.DataFrame(data)

print("Rows with Reasoning:")
df_with_reason = df[df["Reasoning_or_Calculation"] != ""]
print(f"Total rows with reasoning: {len(df_with_reason)}")
if len(df_with_reason) > 0:
    print(df_with_reason.head(5))

print("\nValue_or_Text distribution (first 10):")
print(df[["Case_Reference", "Question_Number", "Correct_Option", "Value_or_Text"]].head(10))
