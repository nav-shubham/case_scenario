import fitz
import re
import json

pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option_letter = re.compile(r"^\(([a-d])\)$")
pattern_option_inline = re.compile(r"^\(([a-d])\)\s+(.*)")

def clean_text(text):
    return text.replace('`', '₹').replace('\u20b9', '₹').strip()

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
            print(f"  [Option Saved] ({current_opt_letter}): {opt_val}")
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
            print(f"  [Question Saved] Q {current_q_no}: {q_text} with options {list(current_options.keys())}")
            current_q_no = None
            current_q_text_lines = []
            current_options = {}
            
    def save_current_case():
        nonlocal current_case_no, case_desc_lines, questions, cases
        save_current_question()
        if current_case_no:
            desc = clean_text(" ".join(case_desc_lines))
            cases.append({
                "case_no": int(current_case_no),
                "description": desc,
                "questions": questions.copy()
            })
            print(f"  [Case Saved] Case {current_case_no} with {len(questions)} questions.")
            current_case_no = None
            case_desc_lines = []
            questions = []

    for page_num in range(8, 12): # pages 9-12
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

parse_questions_from_pdf("inter case scanario/Original/Paper 1 Advanced Accounting.pdf")
