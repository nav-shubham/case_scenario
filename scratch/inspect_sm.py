import fitz
import re

doc = fitz.open("inter case scanario/Section B_ Strategic Management.pdf")
print("=== Section B_ Strategic Management.pdf ===")
for page_num in range(min(15, len(doc))):
    text = doc[page_num].get_text("text")
    # Search for CASE or SCENARIO case-insensitively
    matches = re.findall(r"(case|scenario|answers)", text, re.IGNORECASE)
    if matches:
        print(f"Page {page_num + 1}: matches={matches}")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:10]:
            print(f"  {line}")
doc.close()
