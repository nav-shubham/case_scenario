import fitz
import pikepdf
import re
import os

def execute_spatial_question_bank_pipeline(input_pdf, output_pdf):
    print("Initiating Spatial-Aware Question Bank Pipeline...")
    
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"System Error: {e}")
        return

    qb_pages = []
    qb_active = False
    
    pattern_case = re.compile(r"^\s*CASE\s+SCENARIO\s+\d+", re.IGNORECASE | re.MULTILINE)
    answer_trigger = "ANSWERS TO MULTIPLE CHOICE QUESTIONS"

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").upper()
        
        case_mentions = len(pattern_case.findall(text))
        if case_mentions > 3:
            continue  # Index Bypass
            
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
    
    print(f"Original pages: {len(fitz.open(input_pdf))}")
    print(f"Mapped question pages ({len(qb_pages)}): {qb_pages}")
    
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

execute_spatial_question_bank_pipeline(
    "inter case scanario/Paper 1 Advanced Accounting.pdf",
    "scratch/Paper 1 Advanced Accounting_Pure_Question_Bank.pdf"
)
