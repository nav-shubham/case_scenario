import fitz
import pandas as pd
import re

def extract_tabular_case_answers(pdf_path, output_excel_path):
    print("Initiating Tabular State-Machine Extraction...")
    doc = fitz.open(pdf_path)
    extracted_data = []

    # State Trackers
    current_case = None
    current_q = None
    current_opt = None
    current_text_buffer = []

    # Precision Regex Anchors
    # Matches the specific table header: "ANSWERS TO CASE SCENARIO 1"
    pattern_case_header = re.compile(r"ANSWERS\s+TO\s+CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
    
    # Matches an isolated number followed by a period: "1."
    pattern_q_no = re.compile(r"^(\d+)\.$")
    
    # Matches "(a)" or "(a) Some text"
    pattern_option = re.compile(r"^\(([a-d])\)(.*)", re.IGNORECASE)

    def save_buffered_data():
        """Helper to push the buffered data to our main array before resetting."""
        if current_case and current_q and current_opt:
            # Join multi-line text with a pipe separator for clean Excel formatting
            raw_text = " | ".join(current_text_buffer).strip()
            clean_text = raw_text.replace('`', '₹').replace('\u20b9', '₹')
            
            extracted_data.append({
                "Case_Reference": f"Case Scenario {current_case}",
                "Question_Number": current_q,
                "Correct_Option": current_opt,
                "Reasoning_or_Calculation": clean_text
            })

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Bypass visual table headers that clutter the data stream
            if line.upper() in ["QUESTION NO.", "ANSWER", "QUESTION", "NO."]:
                continue

            # 1. Anchor: New Case Scenario Table Detected
            case_match = pattern_case_header.search(line)
            if case_match:
                save_buffered_data()  # Save the final question of the previous case
                current_case = case_match.group(1)
                current_q = None
                current_opt = None
                current_text_buffer = []
                continue

            # 2. Anchor: Question Number Detected
            q_match = pattern_q_no.match(line)
            if q_match:
                save_buffered_data()  # Save the previous question
                current_q = q_match.group(1)
                current_opt = None
                current_text_buffer = []
                continue

            # 3. Anchor: Option Letter Detected (Only valid if we have an active question)
            if current_q:
                opt_match = pattern_option.search(line)
                
                # If we find an option and haven't set one yet for this question
                if opt_match and not current_opt:
                    current_opt = opt_match.group(1).lower()
                    remainder_text = opt_match.group(2).strip()
                    if remainder_text:
                        current_text_buffer.append(remainder_text)
                    continue

                # 4. Data Gathering: If we have an active option, all subsequent lines belong to it
                if current_opt:
                    current_text_buffer.append(line)

    # Final execution: push the very last buffered question in the document
    save_buffered_data()

    if extracted_data:
        df = pd.DataFrame(extracted_data)
        df.to_excel(output_excel_path, index=False)
        print(f"[+] Extraction complete. {len(df)} structured logic points secured.")
        print(f"[+] Output written to: {output_excel_path}")
    else:
        print("[-] System Alert: No tabular data matched the anchors.")

# EXECUTION TRIGGER
extract_tabular_case_answers("data/intermediate/Original/Section A_ Income-tax.pdf", "data/intermediate/Answers/DT_Tabular_Answers.xlsx")
