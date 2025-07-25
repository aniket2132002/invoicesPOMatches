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
    try:
        # Extract text from both uploaded PO and Invoice PDFs
        po_text = extract_text_from_pdf(po_file)
        inv_text = extract_text_from_pdf(inv_file)

        # Extract fields from PO and Invoice using extractor
        po_fields = extract_fields(po_text, doc_type="po")
        inv_fields = extract_fields(inv_text, doc_type="invoice")

        # Display extracted fields
        st.write("PO Extracted Fields:", po_fields)
        st.write("Invoice Extracted Fields:", inv_fields)

        # Ensure that all necessary fields are present for comparison
        required_fields_po = ["po_number", "vendor", "amount", "date", "supplier", "address"]
        required_fields_inv = ["po_number", "invoice_number", "vendor", "amount", "date", "supplier", "address"]
        
        # Handle missing fields by assigning default values
        for field in required_fields_po:
            if field not in po_fields or not po_fields[field]:
                po_fields[field] = "-"  # Default value for missing fields

        for field in required_fields_inv:
            if field not in inv_fields or not inv_fields[field]:
                inv_fields[field] = "-"  # Default value for missing fields

        # Compare PO and Invoice fields using matcher logic
        is_match, results = match_fields(po_fields, inv_fields)

        st.subheader("Comparison Results")
        st.write(pd.DataFrame(results).T)  # Display the results in tabular format

        # Calculate the total score
        total_score = sum([v['score'] for k, v in results.items()])

        # Handle the total score logic
        if total_score > 300:
            st.success("Test Passed")
        else:
            st.error("Test Failed")

        # If quantity is 0, set the score to 0
        po_qty = po_fields.get("quantity", 0)
        inv_qty = inv_fields.get("quantity", 0)
        if po_qty == 0 or inv_qty == 0:
            st.write("Quantity is 0, hence no points for quantity comparison.")
            total_score -= 2  # Subtract points for quantity comparison when it is zero

        if is_match:
            st.success("Documents Match! Added to matches.csv.")

            # Prepare data to save to CSV
            df = pd.DataFrame([{
                "PO File": po_file.name,
                "Invoice File": inv_file.name,
                **{f"PO_{k}": v['po'] for k, v in results.items()},
                **{f"INV_{k}": v['invoice'] for k, v in results.items()},
                "Total Score": total_score
            }])

            try:
                # Try reading the existing matches.csv file
                old = pd.read_csv("matches.csv")
                df = pd.concat([old, df], ignore_index=True)
            except FileNotFoundError:
                # If matches.csv does not exist, pass
                st.warning("No existing matches.csv file found. Creating a new one.")
                pass

            # Save the updated dataframe to matches.csv
            df.to_csv("matches.csv", index=False)
            
            # Provide a button for downloading the matches CSV
            st.download_button("Download Matches CSV", df.to_csv(index=False), "matches.csv")
        else:
            st.error("No Match Found.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.write("Please ensure both PO and Invoice files are correctly uploaded and in a readable format.")
