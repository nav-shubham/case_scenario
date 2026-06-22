import fitz

doc = fitz.open("inter case scanario/Paper 1 Advanced Accounting.pdf")
for page_num in range(8, 15):
    print(f"\n--- PAGE {page_num + 1} ---")
    text = doc[page_num].get_text("text")
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines:
        print(f"  {line}")
doc.close()
