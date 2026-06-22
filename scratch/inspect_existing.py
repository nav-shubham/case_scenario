import os
import fitz

for filename in os.listdir("."):
    if filename.endswith(".pdf") and not filename.startswith("9096"):
        filepath = filename
        try:
            doc = fitz.open(filepath)
            print(f"{filename}: {doc[0].get_text('text').strip().replace('\n', ' ')[:100]}")
            doc.close()
        except Exception as e:
            print(f"Error {filename}: {e}")
