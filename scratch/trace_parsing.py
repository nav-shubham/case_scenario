import fitz
import re
import sys
sys.path.append(".")
from scratch.test_extractor import should_skip_line, pattern_case, pattern_q_no, pattern_option

doc = fitz.open("inter case scanario/Paper 1 Advanced Accounting.pdf")
# Page 13 is page index 12
page = doc[12]
text = page.get_text("text")
lines = text.split('\n')

current_case = "Case Scenario 2"
is_answer_section = True
current_q_no = "1"
current_opt = "b"
current_val = "` 4,50,000 (deferred tax liability)"
reasoning_lines = []

print("=== TRACING PAGE 13 LINE-BY-LINE ===")
for line in lines:
    line = line.strip()
    if not line:
        continue
    
    print(f"Line: {repr(line)}")
    q_match = pattern_q_no.match(line)
    if q_match:
        print(f"  -> MATCHED Q NO: {q_match.group(1)}")
        print(f"  -> WOULD SAVE CURRENT: q_no={current_q_no}, opt={current_opt}, val={current_val}, reasoning={reasoning_lines}")
        current_q_no = q_match.group(1)
        current_opt = None
        current_val = ""
        reasoning_lines = []
        continue
        
    if current_q_no and not current_opt:
        opt_match = pattern_option.match(line)
        if opt_match:
            current_opt = opt_match.group(1)
            current_val = opt_match.group(2)
            print(f"  -> MATCHED OPTION: opt={current_opt}, val={current_val}")
            continue
            
    if current_opt:
        skip = should_skip_line(line)
        print(f"  -> IS IN OPTION: skip={skip}")
        if skip:
            continue
        reasoning_lines.append(line)
        print(f"  -> APPENDED TO REASONING: {line}")
doc.close()
