import streamlit as st
import pandas as pd
from extractor import extract_text_from_pdf, extract_fields
from matcher import match_fields

st.title("PO & Invoice Matcher")

po_file = st.file_uploader("Upload PO PDF", type=["pdf"])
inv_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

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

    if is_match:
        st.success("Documents Match! Added to matches.csv.")
        # Save to CSV
        df = pd.DataFrame([{
            "PO File": po_file.name,
            "Invoice File": inv_file.name,
            **{f"PO_{k}": v['po'] for k, v in results.items()},
            **{f"INV_{k}": v['invoice'] for k, v in results.items()},
        }])
        try:
            old = pd.read_csv("matches.csv")
            df = pd.concat([old, df], ignore_index=True)
        except FileNotFoundError:
            pass
        df.to_csv("matches.csv", index=False)
        st.download_button("Download Matches CSV", df.to_csv(index=False), "matches.csv")
    else:
        st.error("No Match Found.")
