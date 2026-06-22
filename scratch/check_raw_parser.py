import sys
import os
sys.path.append(".")
from scratch.build_exam_db import parse_questions_from_pdf

pdf_path = os.path.abspath("inter case scanario/Original/Paper 1 Advanced Accounting.pdf")
cases = parse_questions_from_pdf(pdf_path)

print("Raw Cases parsed:", len(cases))
for c in cases[:3]:
    print(f"Case {c['case_no']} description snippet: {c['description'][:100]}")
    print(f"Case {c['case_no']} questions count: {len(c['questions'])}")
    for q in c['questions']:
        print(f"  Q {q['q_no']}: {q['question_text'][:50]}... Options: {list(q['options'].keys())}")
