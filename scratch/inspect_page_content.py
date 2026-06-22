import fitz

def inspect_page(filepath, page_num):
    doc = fitz.open(filepath)
    print(f"=== {filepath} Page {page_num} ===")
    print(doc[page_num - 1].get_text("text"))
    print("-" * 50)

# Let's inspect Paper 1 Advanced Accounting.pdf at page 10, 11
inspect_page("inter case scanario/Paper 1 Advanced Accounting.pdf", 10)
inspect_page("inter case scanario/Paper 1 Advanced Accounting.pdf", 11)

# Let's inspect Section A_ Financial Management.pdf at page 11
inspect_page("inter case scanario/Section A_ Financial Management.pdf", 11)
