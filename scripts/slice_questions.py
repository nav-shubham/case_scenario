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
    
    # Strict start-of-line anchor for the case scenarios
    pattern_case = re.compile(r"^\s*CASE\s+SCENARIO\s+\d+", re.IGNORECASE | re.MULTILINE)
    answer_trigger = "ANSWERS TO MULTIPLE CHOICE QUESTIONS"

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").upper()
        
        case_mentions = len(pattern_case.findall(text))
        if case_mentions > 3:
            continue  # Index Bypass
            
        has_case = case_mentions > 0
        
        # Positional Measurement
        answer_idx = text.find(answer_trigger)
        has_answers = answer_idx != -1
        
        # Spatial Logic Gate: Is the header at the top of the page?
        # < 200 characters accounts for page numbers and book titles.
        is_pure_answer_page = has_answers and answer_idx < 200
        
        # --- Extraction State Machine ---
        if has_case:
            qb_active = True
            
        if qb_active:
            if has_answers:
                if is_pure_answer_page:
                    # Drop the page entirely and shut down extraction
                    qb_active = False
                else:
                    # It is a true transition page (Questions exist above the answers)
                    # Secure the page, then shut down extraction
                    if page_num not in qb_pages:
                        qb_pages.append(page_num)
                    qb_active = False
            else:
                # Standard Question Page
                if page_num not in qb_pages:
                    qb_pages.append(page_num)
                
    doc.close()

    # --- PHASE 2: SLICING & COMPRESSION ---
    if not qb_pages:
        print("[-] System Alert: Pipeline Failed. No target pages detected.")
        return

    print(f"Routing mapped. Generating {len(qb_pages)} pure battleground pages...\n")
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
    print(f"[+] Tactical Advantage Secured | Output: {output_pdf} ({size_kb:.1f} KB)")
    print("Pipeline Execution Complete. You are ready to train.")

# EXECUTION TRIGGER
input_file = "data/intermediate/Original/Section A_ Income-tax.pdf"
execute_spatial_question_bank_pipeline(
    input_file, 
    "data/intermediate/Pure Question Bank/DT_Pure_Question_Bank_Inter.pdf"
)
