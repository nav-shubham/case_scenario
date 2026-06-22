import sys
sys.path.append(".")
from scratch.test_extractor import extract_answers

data = extract_answers("inter case scanario/Paper 1 Advanced Accounting.pdf")
import json
with open("scratch/debug_output.txt", "w", encoding="utf-8") as f:
    f.write("First 10 rows:\n")
    for i, row in enumerate(data[:10]):
        f.write(f"Row {i}: {row}\n")
print("[+] Written to scratch/debug_output.txt")
