import fitz
import re
import pandas as pd

pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option = re.compile(r"^Option\s+\(([a-d])\)(?::\s*|\s+)?(.*)", re.IGNORECASE)
pattern_reason_anchor = re.compile(r"^\s*(?:Reason|Reasoning|Explanation|Calculation|Working)\s*(?::)?\s*$", re.IGNORECASE)

def should_skip_line(line):
    line_upper = line.upper().strip()
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
        
    if line_upper in ["REASON:", "REASON", "REASON :"]:
        return True
        
    if re.match(r"^\d+$", line_upper):
        return True
        
    return False

def extract_answers(filepath):
    doc = fitz.open(filepath)
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
            
            # Replace artifacts
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
                        
                    if should_skip_line(line):
                        continue
                        
                    if in_reason:
                        reasoning_lines.append(line)
                    else:
                        option_value_lines.append(line)
                        
    save_current()
    doc.close()
    return extracted_data

if __name__ == "__main__":
    data = extract_answers("inter case scanario/Paper 1 Advanced Accounting.pdf")
    import json
    with open("scratch/debug_output_v3.txt", "w", encoding="utf-8") as f:
        for i, row in enumerate(data[:15]):
            f.write(f"Row {i}: {row}\n")
    print("[+] Wrote to scratch/debug_output_v3.txt")
