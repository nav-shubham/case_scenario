import json
import os

json_path = "exam_database.json"
js_path = "exam_database.js"

if os.path.exists(json_path):
    print(f"Reading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Writing {js_path}...")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.EXAM_DATABASE = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")
        
    print("[+] Done! exam_database.js generated successfully.")
else:
    print("[-] Error: exam_database.json not found.")
