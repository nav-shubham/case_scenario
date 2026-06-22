import os
import shutil

def move_file(src, dst):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.move(src, dst)
            print(f"Moved {src} -> {dst}")
        except Exception as e:
            print(f"Error moving {src}: {e}")
    else:
        print(f"Source not found: {src}")

# 1. Create target directories
os.makedirs("data/final", exist_ok=True)
os.makedirs("data/intermediate", exist_ok=True)
os.makedirs("scripts", exist_ok=True)
os.makedirs("web", exist_ok=True)

# 2. Move CA Final PDFs, Excels, and sliced PDFs
final_files = [
    "90961bos-aps4227-p1.pdf",
    "90962bos-aps4227-p2.pdf",
    "90963bos-aps4227-p3.pdf",
    "90964bos-aps4227-p4.pdf",
    "90965bos-aps4227-p5.pdf",
    "AFM_QB.pdf",
    "Audit_Pure_Question_Bank_Final.pdf",
    "DT_Pure_Question_Bank.pdf",
    "FR_Pure_Question_Bank_Final.pdf",
    "IDT_Pure_Question_Bank.pdf",
    "AFM_Tabular_Answers.xlsx",
    "Audit_Case_Scenario_Answers.xlsx",
    "Case_Scenario_Answers.xlsx",
    "DT_Case_Scenario_Answers.xlsx",
    "IDT_Case_Scenario_Answers.xlsx"
]

for filename in final_files:
    move_file(filename, f"data/final/{filename}")

# 3. Move CA Intermediate folder content
if os.path.exists("inter case scanario"):
    try:
        # Move all contents of inter case scanario to data/intermediate
        for item in os.listdir("inter case scanario"):
            src_path = os.path.join("inter case scanario", item)
            dst_path = os.path.join("data/intermediate", item)
            if os.path.exists(dst_path):
                if os.path.isdir(dst_path):
                    shutil.rmtree(dst_path)
                else:
                    os.remove(dst_path)
            shutil.move(src_path, dst_path)
        os.rmdir("inter case scanario")
        print("Moved 'inter case scanario' contents to 'data/intermediate'")
    except Exception as e:
        print(f"Error moving intermediate folder: {e}")

# 4. Move scripts
scripts = [
    "process_inter.py",
    "case_scanario.py",
    "extract_tabular_answers.py",
    "slice_questions.py",
    "main.py",
    "scratch/build_exam_db.py"
]

for script in scripts:
    filename = os.path.basename(script)
    move_file(script, f"scripts/{filename}")

# 5. Move web files
web_files = [
    "index.html",
    "style.css",
    "app.js",
    "exam_database.js",
    "exam_database.json"
]

for web_file in web_files:
    move_file(web_file, f"web/{web_file}")

print("Folder restructuring script finished.")
