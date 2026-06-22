import os
import fitz
import re

folder = "inter case scenario"
# Wait, let's check folder name exactly - it is "inter case scanario" with an 'a' (user typed scanario and list_dir showed "inter case scanario").
folder = "inter case scanario"

for filename in os.listdir(folder):
    if not filename.endswith(".pdf"):
        continue
    filepath = os.path.join(folder, filename)
    try:
        doc = fitz.open(filepath)
        print(f"=== {filename} ({len(doc)} pages) ===")
        
        # Check first 5 pages for CASE SCENARIO or general info
        text_start = ""
        for i in range(min(5, len(doc))):
            text_start += doc[i].get_text("text")
            
        case_scenarios = re.findall(r"CASE\s+SCENARIO\s+(\d+)", text_start, re.IGNORECASE)
        print(f"First 5 pages CASE SCENARIO mentions: {case_scenarios}")
        
        # Search for answer triggers
        answer_pages = []
        tabular_headers = []
        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")
            if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in text.upper():
                answer_pages.append((page_num + 1, "MCQ trigger"))
            match = re.search(r"ANSWERS\s+TO\s+CASE\s+SCENARIO\s+(\d+)", text, re.IGNORECASE)
            if match:
                tabular_headers.append((page_num + 1, match.group(0)))
                
        if answer_pages:
            print(f"MCQ answer sections found at pages: {answer_pages}")
        if tabular_headers:
            print(f"Tabular answer headers found at pages: {tabular_headers[:10]}")
            
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    print()
