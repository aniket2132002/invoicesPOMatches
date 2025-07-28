import streamlit as st
import pandas as pd
from extractor import extract_text_from_pdf, extract_fields
from matcher import match_fields
import logging

# Set up logging to capture detailed information
logging.basicConfig(level=logging.INFO)

st.title("PO & Invoice Matcher")

# File Uploaders for PO and Invoice PDFs
po_file = st.file_uploader("Upload PO PDF", type=["pdf"])
inv_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

# When the button is clicked
if st.button("Match Documents") and po_file and inv_file:
    po_text = extract_text_from_pdf(po_file)
    inv_text = extract_text_from_pdf(inv_file)
    po_fields = extract_fields(po_text, doc_type="po")
    inv_fields = extract_fields(inv_text, doc_type="invoice")

    st.write("PO Extracted Fields:", po_fields)
    st.write("Invoice Extracted Fields:", inv_fields)

    is_match, results = match_fields(po_fields, inv_fields)

    st.subheader("Comparison Results")
    st.write(pd.DataFrame(results).T)

    # Calculate extraction score based on extracted fields (background calculation only)
    def calculate_extraction_score(po_fields, inv_fields):
        """Calculate score based on field extraction success"""
        total_score = 0
        max_score = 0
        
        # Define required fields and their scores
        po_required_fields = {
            "po_number": 20,
            "vendor": 20, 
            "amount": 20,
            "date": 20,
            "gst_amount": 10,
            "quantity": 10
        }
        
        inv_required_fields = {
            "po_number": 20,
            "invoice_number": 20,
            "vendor": 20,
            "amount": 20,
            "date": 20,
            "gst_amount": 10,
            "quantity": 10
        }
        
        # Score PO fields (background calculation only)
        for field, score in po_required_fields.items():
            max_score += score
            if po_fields.get(field) and po_fields[field] != "" and po_fields[field] != "0":
                total_score += score
        
        # Score Invoice fields (background calculation only)
        for field, score in inv_required_fields.items():
            max_score += score
            if inv_fields.get(field) and inv_fields[field] != "" and inv_fields[field] != "0":
                total_score += score
        
        return total_score, max_score
    
    # Calculate extraction score
    extraction_score, max_possible_score = calculate_extraction_score(po_fields, inv_fields)
    percentage_score = (extraction_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    
    # Check if PO numbers match (critical requirement)
    po_number_match = False
    po_number_po = po_fields.get("po_number", "").strip()
    po_number_inv = inv_fields.get("po_number", "").strip()
    
    if po_number_po and po_number_inv and po_number_po == po_number_inv:
        po_number_match = True
    
    # Show analysis in frontend
    st.subheader("📊 Analysis Results")
    
    # Show score breakdown
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Extraction Score", f"{extraction_score}/{max_possible_score}")
    with col2:
        st.metric("Percentage", f"{percentage_score:.1f}%")
    with col3:
        if po_number_match:
            st.metric("PO Number Match", "✅ YES")
        else:
            st.metric("PO Number Match", "❌ NO")
    

    
    # Success criteria: PO numbers must match AND extraction score >= 50%
    if po_number_match and percentage_score >= 50:
        st.success("Documents Match! Added to matches.csv.")
        
        # Save to CSV (simple format like old)
        df = pd.DataFrame([{
            "PO File": po_file.name,
            "Invoice File": inv_file.name,
            **{f"PO_{k}": v for k, v in po_fields.items()},
            **{f"INV_{k}": v for k, v in inv_fields.items()},
        }])
        try:
            old = pd.read_csv("matches.csv")
            df = pd.concat([old, df], ignore_index=True)
        except FileNotFoundError:
            pass
        df.to_csv("matches.csv", index=False)
        
        st.download_button("Download Matches CSV", df.to_csv(index=False), "matches.csv")
        
    else:
        # Determine why it failed
        if not po_number_match:
            st.error("No Match Found. PO numbers do not match.")
        else:
            st.error("No Match Found. Insufficient field extraction.")
        
        # Still save to CSV but mark as failed
        df = pd.DataFrame([{
            "PO File": po_file.name,
            "Invoice File": inv_file.name,
            "Status": "FAILED",
            **{f"PO_{k}": v for k, v in po_fields.items()},
            **{f"INV_{k}": v for k, v in inv_fields.items()},
        }])
        try:
            old = pd.read_csv("matches.csv")
            df = pd.concat([old, df], ignore_index=True)
        except FileNotFoundError:
            pass
        df.to_csv("matches.csv", index=False)

