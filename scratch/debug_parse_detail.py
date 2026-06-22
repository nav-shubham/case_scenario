import fitz
import re

pattern_case = re.compile(r"CASE\s+SCENARIO\s+(\d+)", re.IGNORECASE)
pattern_q_no = re.compile(r"^(\d+)\.$")
pattern_option_letter = re.compile(r"^\(([a-d])\)$")
pattern_option_inline = re.compile(r"^\(([a-d])\)\s+(.*)")

doc = fitz.open("inter case scanario/Original/Paper 1 Advanced Accounting.pdf")
print(f"Total pages: {len(doc)}")

state = "NONE"
current_case_no = None
case_desc_lines = []
current_q_no = None
current_q_text_lines = []
current_options = {}
current_opt_letter = None
current_opt_lines = []
questions = []

with open("scratch/parser_debug.txt", "w", encoding="utf-8") as f:
    for page_num in range(8, 11): # Pages 9 to 11
        f.write(f"\n--- PAGE {page_num + 1} ---\n")
        text = doc[page_num].get_text("text")
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            f.write(f"Line: {repr(line)} [State: {state}, Case: {current_case_no}, Q: {current_q_no}, Opt: {current_opt_letter}]\n")
            
            case_match = pattern_case.search(line)
            if case_match:
                f.write(f"  >> MATCHED CASE SCENARIO {case_match.group(1)}\n")
                current_case_no = case_match.group(1)
                state = "DESCRIPTION"
                continue
                
            if "ANSWERS TO MULTIPLE CHOICE QUESTIONS" in line.upper():
                f.write(f"  >> MATCHED ANSWERS TRIGGER\n")
                state = "ANSWERS"
                continue
                
            if state == "DESCRIPTION":
                q_match = pattern_q_no.match(line)
                if q_match:
                    f.write(f"  >> MATCHED Q NO {q_match.group(1)}\n")
                    state = "QUESTION"
                    current_q_no = q_match.group(1)
                    continue
                case_desc_lines.append(line)
                
            elif state == "QUESTION":
                opt_match_inline = pattern_option_inline.match(line)
                opt_match_letter = pattern_option_letter.match(line)
                if opt_match_inline:
                    f.write(f"  >> MATCHED OPTION INLINE {opt_match_inline.group(1)}\n")
                    state = "OPTION"
                    current_opt_letter = opt_match_inline.group(1)
                    current_opt_lines.append(opt_match_inline.group(2))
                elif opt_match_letter:
                    f.write(f"  >> MATCHED OPTION LETTER {opt_match_letter.group(1)}\n")
                    state = "OPTION"
                    current_opt_letter = opt_match_letter.group(1)
                else:
                    current_q_text_lines.append(line)
                    
            elif state == "OPTION":
                opt_match_inline = pattern_option_inline.match(line)
                opt_match_letter = pattern_option_letter.match(line)
                q_match = pattern_q_no.match(line)
                if opt_match_inline:
                    f.write(f"  >> MATCHED OPTION INLINE {opt_match_inline.group(1)}\n")
                    current_opt_letter = opt_match_inline.group(1)
                    current_opt_lines.append(opt_match_inline.group(2))
                elif opt_match_letter:
                    f.write(f"  >> MATCHED OPTION LETTER {opt_match_letter.group(1)}\n")
                    current_opt_letter = opt_match_letter.group(1)
                elif q_match:
                    f.write(f"  >> MATCHED Q NO {q_match.group(1)} (from option)\n")
                    state = "QUESTION"
                    current_q_no = q_match.group(1)
                else:
                    current_opt_lines.append(line)

doc.close()
print("[+] Wrote trace to scratch/parser_debug.txt")
