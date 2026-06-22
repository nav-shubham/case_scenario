import fitz
import re

pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option_letter = re.compile(r"^\(([a-d])\)$")
pattern_option_inline = re.compile(r"^\(([a-d])\)\s+(.*)")

doc = fitz.open("inter case scanario/Original/Paper 1 Advanced Accounting.pdf")
page = doc[8]
text = page.get_text("text")
lines = text.split('\n')

state = "NONE"
current_case_no = None
case_desc_lines = []
current_q_no = None
current_q_text_lines = []
current_options = {}
current_opt_letter = None
current_opt_lines = []
questions = []

def save_current_option():
    global current_opt_letter, current_opt_lines, current_options
    print(f"  [DEBUG] save_current_option called. letter={current_opt_letter}, lines={current_opt_lines}")
    if current_opt_letter and current_opt_lines:
        opt_val = " ".join(current_opt_lines).strip()
        current_options[current_opt_letter] = opt_val
        print(f"    -> Saved option {current_opt_letter} = {opt_val}")
        current_opt_letter = None
        current_opt_lines = []

for line in lines:
    line = line.strip()
    if not line:
        continue
        
    print(f"Line: {repr(line)} [State: {state}]")
    
    case_match = pattern_case.search(line)
    if case_match:
        print(f"  -> Matched case scenario {case_match.group(1)}")
        current_case_no = case_match.group(1)
        state = "DESCRIPTION"
        continue
        
    if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in line.upper():
        print("  -> Matched answers trigger")
        state = "ANSWERS"
        continue
        
    if state == "DESCRIPTION":
        q_match = pattern_q_no.match(line)
        if q_match:
            print(f"  -> Matched question {q_match.group(1)}")
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
            print(f"  -> Matched option inline {current_opt_letter}")
        elif opt_match_letter:
            save_current_option()
            state = "OPTION"
            current_opt_letter = opt_match_letter.group(1)
            print(f"  -> Matched option letter {current_opt_letter}")
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
            print(f"  -> Matched option inline {current_opt_letter}")
        elif opt_match_letter:
            save_current_option()
            current_opt_letter = opt_match_letter.group(1)
            print(f"  -> Matched option letter {current_opt_letter}")
        elif q_match:
            print(f"  -> Matched next question {q_match.group(1)}")
            state = "QUESTION"
            current_q_no = q_match.group(1)
        else:
            current_opt_lines.append(line)
            print(f"  -> Appended to option lines: {line}")
doc.close()
