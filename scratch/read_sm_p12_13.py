import fitz

doc = fitz.open("inter case scanario/Section B_ Strategic Management.pdf")
print("=== PAGE 12 ===")
print(doc[11].get_text("text"))
print("=== PAGE 13 ===")
print(doc[12].get_text("text"))
doc.close()
