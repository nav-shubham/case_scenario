import fitz
import re

doc = fitz.open("90963bos-aps4227-p3.pdf")
print("=== 90963bos-aps4227-p3.pdf ===")
answer_pages = []
case_pages = []
for page_num in range(len(doc)):
    text = doc[page_num].get_text("text").upper()
    if "ANSWERS TO MULTIPLE" in text:
        answer_pages.append(page_num + 1)
    if "CASE SCENARIO" in text:
        case_pages.append(page_num + 1)

print(f"Total pages: {len(doc)}")
print(f"CASE SCENARIO mentioned at pages: {case_pages[:20]}")
print(f"ANSWERS TO MULTIPLE mentioned at pages: {answer_pages}")
doc.close()
