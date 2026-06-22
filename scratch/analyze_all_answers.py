import os
import fitz
import re

folder = "inter case scanario"

for filename in os.listdir(folder):
    if not filename.endswith(".pdf") or filename == "Corrigendum.pdf":
        continue
    
    filepath = os.path.join(folder, filename)
    doc = fitz.open(filepath)
    print(f"\n=================== {filename} ===================")
    
    # Let's find where "ANSWERS TO MULTIPLE CHOICE QUESTIONS" or "ANSWERS TO CASE SCENARIO" starts
    found = False
    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text")
        if "ANSWERS TO MULTIPLE" in text.upper() or "ANSWERS TO CASE" in text.upper():
            print(f"Trigger found at page {page_num + 1}:")
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Print the first 25 lines of the answer section
            for i, line in enumerate(lines):
                if "ANSWERS TO MULTIPLE" in line.upper() or "ANSWERS TO CASE" in line.upper():
                    start_idx = max(0, i - 2)
                    end_idx = min(len(lines), i + 20)
                    for idx in range(start_idx, end_idx):
                        print(f"  Line {idx}: {repr(lines[idx])}")
                    found = True
                    break
            if found:
                break
    if not found:
        print("No answer section triggered in this document.")
    doc.close()
