# PO & Invoice Matcher

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
2. Start the app:
   ```
   streamlit run app.py
   ```
3. Upload your PO and Invoice PDFs, click "Match Documents", and download the results!

## How it Works

- Extracts text from PDFs using PyMuPDF.
- Uses spaCy to extract key fields (vendor, buyer, PO number, etc.).
- Compares fields with fuzzy logic.
- If matched, adds to `matches.csv` and allows download.


python -m venv venv
venv\Scripts\activate
.\venv\Scripts\Activate
