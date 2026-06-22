import os
import fitz
import re
import pandas as pd
import json

# Setup regexes
pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option_letter = re.compile(r"^\(([a-d])\)$")
pattern_option_inline = re.compile(r"^\(([a-d])\)\s+(.*)")
pattern_reason_anchor = re.compile(r"^\s*(?:Reason|Reasoning|Explanation|Calculation|Working)\s*(?::)?\s*$", re.IGNORECASE)

def clean_text(text):
    return text.replace('`', '₹').replace('\u20b9', '₹').strip()

def should_skip_line(line, line_upper):
    if "INSTITUTE OF CHARTERED" in line_upper:
        return True
    if "©" in line:
        return True
    if "CASE SCENARIO" in line_upper:
        return True
    if re.match(r"^\d+$", line_upper):
        return True
    return False

def extract_answers_from_pdf(filepath):
    """Helper to extract answers directly from the PDF in case the Excel doesn't exist."""
    print(f"    [+] Extracting answers directly from PDF: {os.path.basename(filepath)}")
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
            
            val_clean = clean_text(val_full)
            reason_clean = clean_text(reason_full)
            
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
                    opt_match = pattern_option.match(line) if 'pattern_option' in globals() else pattern_option_inline.match(line)
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
    return pd.DataFrame(extracted_data)

def load_answers(excel_path, pdf_path_fallback=None):
    """Loads answers from Excel, or falls back to parsing PDF directly if Excel is missing."""
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        # Standardize columns
        df.columns = [c.strip() for c in df.columns]
        
        # Standardize Case_Reference and Question_Number
        if 'Case_Reference' in df.columns and 'Question_Number' in df.columns and 'Correct_Option' in df.columns:
            # Check for Reasoning_or_Calculation or Value_or_Text
            reason_col = 'Reasoning_or_Calculation' if 'Reasoning_or_Calculation' in df.columns else None
            val_col = 'Value_or_Text' if 'Value_or_Text' in df.columns else None
            
            ans_map = {}
            for _, row in df.iterrows():
                case_ref = str(row['Case_Reference']).strip()
                try:
                    q_num = int(row['Question_Number'])
                except:
                    continue
                opt = str(row['Correct_Option']).strip().lower()
                
                val = str(row[val_col]).strip() if val_col and pd.notna(row[val_col]) else ""
                reason = str(row[reason_col]).strip() if reason_col and pd.notna(row[reason_col]) else ""
                
                ans_map[(case_ref, q_num)] = {
                    "correct_option": opt,
                    "value_text": val,
                    "reasoning": reason
                }
            return ans_map
    
    if pdf_path_fallback and os.path.exists(pdf_path_fallback):
        df = extract_answers_from_pdf(pdf_path_fallback)
        ans_map = {}
        for _, row in df.iterrows():
            case_ref = str(row['Case_Reference']).strip()
            q_num = int(row['Question_Number'])
            opt = str(row['Correct_Option']).strip().lower()
            val = str(row['Value_or_Text']).strip()
            reason = str(row['Reasoning_or_Calculation']).strip()
            
            ans_map[(case_ref, q_num)] = {
                "correct_option": opt,
                "value_text": val,
                "reasoning": reason
            }
        # Also save to Excel so it's there for future
        df.to_excel(excel_path, index=False)
        print(f"    [+] Saved fallback extracted answers to {excel_path}")
        return ans_map

    return {}

def parse_questions_from_pdf(filepath):
    doc = fitz.open(filepath)
    cases = []
    
    current_case_no = None
    state = "NONE"
    
    case_desc_lines = []
    current_q_no = None
    current_q_text_lines = []
    current_options = {}
    current_opt_letter = None
    current_opt_lines = []
    
    questions = []
    
    def save_current_option():
        nonlocal current_opt_letter, current_opt_lines, current_options
        if current_opt_letter and current_opt_lines:
            opt_val = clean_text(" ".join(current_opt_lines))
            current_options[current_opt_letter] = opt_val
            current_opt_letter = None
            current_opt_lines = []
            
    def save_current_question():
        nonlocal current_q_no, current_q_text_lines, current_options, questions
        save_current_option()
        if current_q_no and current_q_text_lines:
            q_text = clean_text(" ".join(current_q_text_lines))
            questions.append({
                "q_no": int(current_q_no),
                "question_text": q_text,
                "options": current_options.copy()
            })
            current_q_no = None
            current_q_text_lines = []
            current_options = {}
            
    def save_current_case():
        nonlocal current_case_no, case_desc_lines, questions, cases
        save_current_question()
        if current_case_no and len(questions) > 0:
            desc = clean_text(" ".join(case_desc_lines))
            cases.append({
                "case_no": int(current_case_no),
                "description": desc,
                "questions": questions.copy()
            })
        current_case_no = None
        case_desc_lines = []
        questions = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "INSTITUTE OF CHARTERED" in line.upper() or "©" in line:
                continue
            if line.upper() in ["CASE SCENARIOS", "CASE SCENARIO"]:
                continue
            if re.match(r"^\d+$", line):
                continue
                
            if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in line.upper():
                save_current_case()
                state = "ANSWERS"
                continue
                
            case_match = pattern_case.search(line)
            if case_match:
                save_current_case()
                current_case_no = case_match.group(1)
                state = "DESCRIPTION"
                continue
                
            if state == "DESCRIPTION":
                q_match = pattern_q_no.match(line)
                if q_match:
                    state = "QUESTION"
                    current_q_no = q_match.group(1)
                    continue
                if "ANSWER THE FOLLOWING QUESTIONS" in line.upper() or "MULTIPLE CHOICE QUESTIONS" in line.upper():
                    continue
                case_desc_lines.append(line)
                
            elif state == "QUESTION":
                opt_match_inline = pattern_option_inline.match(line)
                opt_match_letter = pattern_option_letter.match(line)
                
                if opt_match_inline:
                    save_current_option()
                    state = "OPTION"
                    current_opt_letter = opt_match_inline.group(1)
                    current_opt_lines.append(opt_match_inline.group(2))
                elif opt_match_letter:
                    save_current_option()
                    state = "OPTION"
                    current_opt_letter = opt_match_letter.group(1)
                else:
                    current_q_text_lines.append(line)
                    
            elif state == "OPTION":
                opt_match_inline = pattern_option_inline.match(line)
                opt_match_letter = pattern_option_letter.match(line)
                q_match = pattern_q_no.match(line)
                
                if opt_match_inline:
                    save_current_option()
                    current_opt_letter = opt_match_inline.group(1)
                    current_opt_lines.append(opt_match_inline.group(2))
                elif opt_match_letter:
                    save_current_option()
                    current_opt_letter = opt_match_letter.group(1)
                elif q_match:
                    save_current_question()
                    state = "QUESTION"
                    current_q_no = q_match.group(1)
                else:
                    current_opt_lines.append(line)
                    
    save_current_case()
    doc.close()
    return cases

def compile_database():
    database = {
        "Intermediate": [],
        "Final": []
    }
    
    # 1. CA Inter Config
    inter_folder = "data/intermediate"
    inter_files = [
        {"pdf": "Paper 1 Advanced Accounting.pdf", "excel": "Paper 1 Advanced Accounting_Answers.xlsx", "subject": "Paper 1: Advanced Accounting"},
        {"pdf": "Paper-2_ Corporate and Other Laws.pdf", "excel": "Paper-2_ Corporate and Other Laws_Answers.xlsx", "subject": "Paper 2: Corporate and Other Laws"},
        {"pdf": "Paper-4_ Cost and Management Accounting.pdf", "excel": "Paper-4_ Cost and Management Accounting_Answers.xlsx", "subject": "Paper 4: Cost and Management Accounting"},
        {"pdf": "Paper-5_ Auditing and Ethics.pdf", "excel": "Paper-5_ Auditing and Ethics_Answers.xlsx", "subject": "Paper 5: Auditing and Ethics"},
        {"pdf": "Section A_ Financial Management.pdf", "excel": "Section A_ Financial Management_Answers.xlsx", "subject": "Paper 6A: Financial Management"},
        {"pdf": "Section A_ Income-tax.pdf", "excel": "Section A_ Income-tax_Answers.xlsx", "subject": "Paper 3A: Income-tax"},
        {"pdf": "Section B_ Goods and Services Tax.pdf", "excel": "Section B_ Goods and Services Tax_Answers.xlsx", "subject": "Paper 3B: Goods and Services Tax"},
        {"pdf": "Section B_ Strategic Management.pdf", "excel": "Section B_ Strategic Management_Answers.xlsx", "subject": "Paper 6B: Strategic Management"}
    ]
    
    print("=== Processing CA Intermediate ===")
    for item in inter_files:
        pdf_path = os.path.join(inter_folder, "Original", item["pdf"])
        excel_path = os.path.join(inter_folder, "Answers", item["excel"])
        
        print(f"Processing {item['subject']}...")
        
        # Load correct answers map
        ans_map = load_answers(excel_path, pdf_path)
        
        # Parse questions
        cases = parse_questions_from_pdf(pdf_path)
        
        # Merge
        merged_cases = []
        for case in cases:
            case_ref = f"Case Scenario {case['case_no']}"
            merged_questions = []
            for q in case['questions']:
                ans_info = ans_map.get((case_ref, q['q_no']), {
                    "correct_option": "",
                    "value_text": "",
                    "reasoning": ""
                })
                merged_questions.append({
                    "q_no": q['q_no'],
                    "question_text": q['question_text'],
                    "options": q['options'],
                    "correct_option": ans_info["correct_option"],
                    "value_text": ans_info["value_text"],
                    "reasoning": ans_info["reasoning"]
                })
            merged_cases.append({
                "case_no": case['case_no'],
                "description": case['description'],
                "questions": merged_questions
            })
            
        database["Intermediate"].append({
            "subject": item["subject"],
            "pdf_file": item["pdf"],
            "cases": merged_cases
        })
        print(f"  [+] Merged {len(merged_cases)} case scenarios.")

    # 2. CA Final Config
    final_folder = "data/final"
    final_files = [
        {"pdf": "90961bos-aps4227-p1.pdf", "excel": "Case_Scenario_Answers.xlsx", "subject": "Paper 1: Financial Reporting"},
        {"pdf": "90962bos-aps4227-p2.pdf", "excel": "AFM_Tabular_Answers.xlsx", "subject": "Paper 2: Advanced Financial Management"},
        {"pdf": "90963bos-aps4227-p3.pdf", "excel": "Audit_Case_Scenario_Answers.xlsx", "subject": "Paper 3: Advanced Auditing, Assurance & Professional Ethics"},
        {"pdf": "90964bos-aps4227-p4.pdf", "excel": "DT_Case_Scenario_Answers.xlsx", "subject": "Paper 4: Direct Tax Laws & International Taxation"},
        {"pdf": "90965bos-aps4227-p5.pdf", "excel": "IDT_Case_Scenario_Answers.xlsx", "subject": "Paper 5: Indirect Tax Laws"}
    ]
    
    print("\n=== Processing CA Final ===")
    for item in final_files:
        pdf_path = os.path.join(final_folder, item["pdf"])
        excel_path = os.path.join(final_folder, item["excel"])
        
        print(f"Processing {item['subject']}...")
        
        # Load correct answers map (IDT fallback will be parsed automatically)
        ans_map = load_answers(excel_path, pdf_path)
        
        # Parse questions
        cases = parse_questions_from_pdf(pdf_path)
        
        # Merge
        merged_cases = []
        for case in cases:
            case_ref = f"Case Scenario {case['case_no']}"
            merged_questions = []
            for q in case['questions']:
                ans_info = ans_map.get((case_ref, q['q_no']), {
                    "correct_option": "",
                    "value_text": "",
                    "reasoning": ""
                })
                merged_questions.append({
                    "q_no": q['q_no'],
                    "question_text": q['question_text'],
                    "options": q['options'],
                    "correct_option": ans_info["correct_option"],
                    "value_text": ans_info["value_text"],
                    "reasoning": ans_info["reasoning"]
                })
            merged_cases.append({
                "case_no": case['case_no'],
                "description": case['description'],
                "questions": merged_questions
            })
            
        database["Final"].append({
            "subject": item["subject"],
            "pdf_file": item["pdf"],
            "cases": merged_cases
        })
        print(f"  [+] Merged {len(merged_cases)} case scenarios.")

    # Save to JSON database
    output_db_path = "web/exam_database.json"
    with open(output_db_path, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Success: Unified exam database saved to {output_db_path}")

    # Generate JS file directly
    output_js_path = "web/exam_database.js"
    with open(output_js_path, "w", encoding="utf-8") as f:
        f.write("window.EXAM_DATABASE = ")
        json.dump(database, f, ensure_ascii=False)
        f.write(";\n")
    print(f"[+] Success: exam_database.js generated successfully at {output_js_path}")

if __name__ == "__main__":
    compile_database()
