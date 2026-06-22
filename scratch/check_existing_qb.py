import fitz

doc = fitz.open("Audit_Pure_Question_Bank_Final.pdf")
print("=== Audit_Pure_Question_Bank_Final.pdf ===")
for page_num in range(len(doc)):
    text = doc[page_num].get_text("text")
    if "ANSWERS TO MULTIPLE" in text.upper():
        print(f"ANSWERS TO MULTIPLE found at page {page_num + 1}")
doc.close()
