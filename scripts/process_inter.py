import os
import fitz
import pikepdf
import re
import pandas as pd

# Define Regex Patterns
pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option = re.compile(r"^Option\s+\(([a-d])\)(?::\s*|\s+)?(.*)", re.IGNORECASE)
pattern_reason_anchor = re.compile(r"^\s*(?:Reason|Reasoning|Explanation|Calculation|Working)\s*(?::)?\s*$", re.IGNORECASE)

def should_skip_line(line, line_upper):
    if "INSTITUTE OF CHARTERED" in line_upper:
        return True
    if "©" in line:
        return True
    
    subjects = [
        "ADVANCED ACCOUNTING", "STRATEGIC MANAGEMENT", "FINANCIAL MANAGEMENT",
        "INCOME-TAX", "GOODS AND SERVICES TAX", "AUDITING AND ETHICS",
        "CORPORATE AND OTHER LAWS", "COST AND MANAGEMENT ACCOUNTING"
    ]
    for sub in subjects:
        if sub in line_upper:
            return True
            
    if "CASE SCENARIO" in line_upper:
        return True
        
    if re.match(r"^\d+$", line_upper):
        return True
        
    return False

def extract_answers_to_excel(input_pdf, output_excel):
    print(f"  [+] Extracting answers from {os.path.basename(input_pdf)}...")
    doc = fitz.open(input_pdf)
    extracted_data = []
    
    current_case = "Independent MCQs / General"
    is_answer_section = False
    current_q_no = None
    current_opt = None
    current_val = ""
    option_value_lines = []
    reasoning_lines = []
    in_reason = False
    
    def save_current():
        nonlocal current_case, current_q_no, current_opt, current_val, option_value_lines, reasoning_lines, in_reason
        if current_q_no and current_opt:
            val_full = (current_val + " " + " ".join(option_value_lines)).strip()
            reason_full = " | ".join(reasoning_lines).strip()
            
            # Clean character artifacts
            val_clean = val_full.replace('`', '₹').replace('\u20b9', '₹').strip()
            reason_clean = reason_full.replace('`', '₹').replace('\u20b9', '₹').strip()
            
            # Clean double spaces
            val_clean = re.sub(r'\s+', ' ', val_clean)
            reason_clean = re.sub(r'\s+', ' ', reason_clean)
            
            extracted_data.append({
                "Case_Reference": current_case,
                "Question_Number": int(current_q_no),
                "Correct_Option": current_opt.lower(),
                "Value_or_Text": val_clean,
                "Reasoning_or_Calculation": reason_clean
            })
            
            current_q_no = None
            current_opt = None
            current_val = ""
            option_value_lines = []
            reasoning_lines = []
            in_reason = False

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            case_match = pattern_case.search(line)
            if case_match:
                save_current()
                current_case = f"Case Scenario {case_match.group(1)}"
                is_answer_section = False
                continue
                
            if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in line.upper():
                save_current()
                is_answer_section = True
                continue
                
            if is_answer_section:
                q_match = pattern_q_no.match(line)
                if q_match:
                    save_current()
                    current_q_no = q_match.group(1)
                    continue
                    
                if current_q_no and not current_opt:
                    opt_match = pattern_option.match(line)
                    if opt_match:
                        current_opt = opt_match.group(1)
                        current_val = opt_match.group(2) if opt_match.group(2) else ""
                        continue
                        
                if current_opt:
                    if pattern_reason_anchor.match(line):
                        in_reason = True
                        continue
                        
                    line_upper = line.upper().strip()
                    if should_skip_line(line, line_upper):
                        continue
                        
                    if in_reason:
                        reasoning_lines.append(line)
                    else:
                        option_value_lines.append(line)
                        
    save_current()
    doc.close()
    
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        # Reorder/select columns to match expected output structure
        df = df[["Case_Reference", "Question_Number", "Correct_Option", "Value_or_Text", "Reasoning_or_Calculation"]]
        df.to_excel(output_excel, index=False)
        print(f"  [+] Saved {len(df)} answers to {output_excel}")
    else:
        print(f"  [-] No answers extracted for {input_pdf}")

def slice_questions_pdf(input_pdf, output_pdf):
    print(f"  [+] Slicing questions from {os.path.basename(input_pdf)}...")
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"  [-] Error loading {input_pdf}: {e}")
        return

    qb_pages = []
    qb_active = False
    
    pattern_case_page = re.compile(r"^\s*CASE\s+SCENARIO\s+\d+", re.IGNORECASE | re.MULTILINE)
    answer_trigger = "ANSWERS TO MULTIPLE CHOICE QUESTIONS"

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").upper()
        
        case_mentions = len(pattern_case_page.findall(text))
        if case_mentions > 3:
            continue  # Bypass index pages
            
        has_case = case_mentions > 0
        answer_idx = text.find(answer_trigger)
        has_answers = answer_idx != -1
        is_pure_answer_page = has_answers and answer_idx < 200
        
        if has_case:
            qb_active = True
            
        if qb_active:
            if has_answers:
                if is_pure_answer_page:
                    qb_active = False
                else:
                    if page_num not in qb_pages:
                        qb_pages.append(page_num)
                    qb_active = False
            else:
                if page_num not in qb_pages:
                    qb_pages.append(page_num)
                
    doc.close()

    if not qb_pages:
        print(f"  [-] Slicing failed: No question pages identified in {input_pdf}")
        return

    temp_name = "temp_qb_uncompressed.pdf"
    temp_doc = fitz.open(input_pdf)
    temp_doc.select(qb_pages)
    temp_doc.save(temp_name, garbage=4, clean=True)
    temp_doc.close()
    
    with pikepdf.open(temp_name) as pdf:
        pdf.save(
            output_pdf, 
            object_stream_mode=pikepdf.ObjectStreamMode.generate, 
            compress_streams=True
        )
        
    if os.path.exists(temp_name):
        os.remove(temp_name)
    
    size_kb = os.path.getsize(output_pdf) / 1024
    print(f"  [+] Saved pure question bank ({len(qb_pages)} pages, {size_kb:.1f} KB) to {output_pdf}")

def main():
    folder = "data/intermediate"
    original_folder = os.path.join(folder, "Original")
    answers_folder = os.path.join(folder, "Answers")
    qb_folder = os.path.join(folder, "Pure Question Bank")
    
    if not os.path.exists(original_folder):
        print(f"[-] Directory {original_folder} does not exist.")
        return
        
    os.makedirs(answers_folder, exist_ok=True)
    os.makedirs(qb_folder, exist_ok=True)

    files = [f for f in os.listdir(original_folder) if f.endswith(".pdf") and f != "Corrigendum.pdf"]
    print(f"Found {len(files)} target PDF files to process in '{original_folder}' folder.")
    
    for idx, filename in enumerate(files, 1):
        input_path = os.path.join(original_folder, filename)
        base_name = os.path.splitext(filename)[0]
        
        # Setup outputs in their respective folders
        output_pdf = os.path.join(qb_folder, f"{base_name}_Pure_Question_Bank.pdf")
        output_excel = os.path.join(answers_folder, f"{base_name}_Answers.xlsx")
        
        print(f"\n[{idx}/{len(files)}] Processing '{filename}'...")
        
        # Step 1: Slicing into pure question bank
        slice_questions_pdf(input_path, output_pdf)
        
        # Step 2: Answer and Reasoning extraction to Excel
        extract_answers_to_excel(input_path, output_excel)

if __name__ == "__main__":
    main()
