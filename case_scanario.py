import fitz
import pandas as pd
import re

def extract_case_answers_v2(pdf_path, output_excel_path):
    print("Initiating Buffered Extraction Logic...")
    doc = fitz.open(pdf_path)
    extracted_data = []

    # State Trackers
    current_case = "Independent MCQs / General" 
    is_answer_section = False
    pending_q_no = None  # The buffer to hold the isolated "1.", "2.", etc.

    # Precision Regex Patterns
    pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
    
    # Matches ONLY a number followed by a period on its own line (e.g., "1.")
    pattern_q_no = re.compile(r"^(\d+)\.$")
    
    # Matches "Option (d): [Value]"
    pattern_option = re.compile(r"^Option\s+\(([a-d])\)(?::\s*(.*))?", re.IGNORECASE)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 1. State Change: New Case Scenario
            case_match = pattern_case.search(line)
            if case_match:
                current_case = f"Case Scenario {case_match.group(1)}"
                is_answer_section = False  
                pending_q_no = None  # Flush buffer on section change
                continue

            # 2. Trigger: Enter Answer Zone
            if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in line.upper():
                is_answer_section = True
                pending_q_no = None
                continue

            # 3. Buffered Data Extraction
            if is_answer_section:
                
                # Step 3A: Catch the isolated Question Number and buffer it
                q_match = pattern_q_no.match(line)
                if q_match:
                    pending_q_no = q_match.group(1)
                    continue  # Move to the next line to find the option

                # Step 3B: If we have a buffered Question Number, hunt for its Option
                if pending_q_no:
                    opt_match = pattern_option.search(line)
                    if opt_match:
                        correct_option = opt_match.group(1).lower()
                        raw_value = opt_match.group(2).strip() if opt_match.group(2) else ""
                        
                        # Data Cleansing: Fix the Rupee font artifact
                        clean_value = raw_value.replace('`', '₹').strip()

                        extracted_data.append({
                            "Case_Reference": current_case,
                            "Question_Number": pending_q_no,
                            "Correct_Option": correct_option,
                            "Value_or_Text": clean_value
                        })
                        
                        # Flush the buffer after a successful capture
                        pending_q_no = None 
                        continue

    # Compiling the Refined Intelligence
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        df.to_excel(output_excel_path, index=False)
        print(f"[+] Success: {len(df)} data points converted into structured logic.")
        print(f"[+] Output saved to: {output_excel_path}")
    else:
        print("[-] System Alert: Pipeline executed, but no data passed the regex filters.")

# EXECUTION TRIGGER
# Replace with your actual file paths
extract_case_answers_v2("90965bos-aps4227-p5.pdf", "IDT_Case_Scenario_Answers.xlsx")
