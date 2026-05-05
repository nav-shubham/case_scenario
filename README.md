# 📘 Case Scenario PDF Processing Toolkit

A Python-based automation toolkit to extract, clean, and transform ICAI-style PDF question banks into structured, analysis-ready formats.

---

## 🚀 What This Project Does

This project solves a very specific but powerful problem:

➡️ Converts unstructured PDF content into structured Excel datasets
➡️ Extracts MCQ answers with precision
➡️ Separates question banks from answer sections
➡️ Handles messy PDF formatting (₹ symbols, multi-line text, etc.)

---

## 🧠 Core Modules

### 1. Case Scenario Answer Extractor

📄 File: 

* Extracts MCQ answers from standard PDF format
* Detects:

  * Case Scenario number
  * Question number
  * Correct option
  * Value/Text
* Uses buffered logic to handle broken PDF lines

---

### 2. Tabular Answer Extractor

📄 File: 

* Designed for **table-format answer PDFs**
* Captures:

  * Case reference
  * Question number
  * Correct option
  * Detailed reasoning/calculation
* Uses state-machine logic for high accuracy

---

### 3. Question Bank Slicer

📄 File: 

* Extracts ONLY question pages from PDFs
* Removes answer sections intelligently
* Outputs a **clean question bank PDF**
* Includes compression optimization

---

## ⚙️ Tech Stack

* Python
* PyMuPDF (`fitz`)
* pandas
* pikepdf
* regex

---

## 📂 Project Structure

```
case_scanario/
│
├── case_scanario.py
├── extract_tabular_answers.py
├── slice_questions.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Setup Instructions

### 1. Clone Repo

```
git clone https://github.com/your-username/your-repo.git
cd case_scanario
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## ▶️ Usage

### Run Answer Extraction

```
python case_scanario.py
```

### Run Tabular Extraction

```
python extract_tabular_answers.py
```

### Slice Question Bank

```
python slice_questions.py
```

---

## 🎯 Use Cases

* CA / CMA / CS students
* PDF data extraction workflows
* Study automation systems
* Building question-answer datasets

---

## ⚡ Key Strength

This project is not just scripting — it uses:

✔ Stateful parsing
✔ Regex precision
✔ Structured data modeling
✔ Real-world messy PDF handling

---

## 🔥 Future Improvements

* GUI interface
* Batch processing for multiple PDFs
* Direct CSV export
* Integration with AI-based analysis

---

## 👤 Author

**Shubham Kadam**
(Chartered Accountant Student)

---

## ⭐ If You Found This Useful

Give this repo a star and use it to build smarter study systems 🚀
