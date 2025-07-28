import fitz  # PyMuPDF
import re
from PIL import Image
import io
import pytesseract
import logging

# Setup logging for error handling
logging.basicConfig(level=logging.INFO)

def extract_text_from_pdf(file):
    """
    Extract text from a PDF file. If no text is found, OCR is performed.
    """
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            page_text = page.get_text()
            if not page_text.strip():  # If no text is found, perform OCR
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                page_text = pytesseract.image_to_string(img)
                logging.info(f"OCR triggered for page {page.number}")  # Log OCR usage
            text += page_text
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_fields(text, doc_type):
    """
    Extracts key fields from text, depending on the document type (PO or Invoice).
    """
    fields = {}
    try:
        # --- PO Extraction ---
        if doc_type == "po":
            po_match = re.search(r'Purchase Order No\s*:\s*([A-Za-z0-9\-\/]+)', text, re.I)
            if po_match:
                fields["po_number"] = po_match.group(1).strip()

            vendor_match = re.search(r'Vendor Details\s*:.*?\n([A-Z0-9 &\.\-]+)', text, re.I)
            if vendor_match:
                fields["vendor"] = vendor_match.group(1).strip()

            amt_match = re.search(r'(Total Amount|Grand Total|Total|Amount Payable)[^\d]*([\d,]+\.\d{2})', text, re.I)
            if amt_match:
                fields["amount"] = amt_match.group(2).replace(',', '')

            # Try to extract GST and non-GST amounts (CGST and SGST)
            gst_match = re.search(r'GST[\s]*([\d,]+\.\d{2})', text, re.I)
            if gst_match:
                fields["gst_amount"] = gst_match.group(1).replace(',', '')

            # Quantity
            qty_match = re.search(r'(Total Qty|Total Quantity)[^\d]*([\d,]+)', text, re.I)
            if qty_match:
                fields["quantity"] = qty_match.group(2).replace(',', '')

            # Date
            date_match = re.search(r'(P\.O\. Date|PO Date|Date)[\s:]*([0-9]{2}[\/\.\-][0-9]{2}[\/\.\-][0-9]{4}|[A-Za-z]{3,9} \d{1,2}, \d{4})', text, re.I)
            if date_match:
                fields["date"] = date_match.group(2).strip()

        # --- Invoice Extraction ---
        elif doc_type == "invoice":
            po_match = re.search(r'(PO No|PO Number|Purchase Order No)[\s:]*([A-Za-z0-9\-\/]+)', text, re.I)
            if po_match:
                fields["po_number"] = po_match.group(2).strip()

            inv_match = re.search(r'(Invoice No|Invoice Number)[\s#:\-]*([A-Za-z0-9\-\/]+)', text, re.I)
            if inv_match:
                fields["invoice_number"] = inv_match.group(2).strip()

            vendor_match = re.search(r'Billed By[^\n]*\n([^\n]+)', text, re.I)
            if vendor_match:
                fields["vendor"] = vendor_match.group(1).strip()

            amt_match = re.search(r'(Total \(INR\)|Total Amount|Grand Total|Amount Payable)[^\d]*([\d,]+\.\d{2})', text, re.I)
            if amt_match:
                fields["amount"] = amt_match.group(2).replace(',', '')

            # Try to extract GST and non-GST amounts (CGST and SGST)
            gst_match = re.search(r'GST[\s]*([\d,]+\.\d{2})', text, re.I)
            if gst_match:
                fields["gst_amount"] = gst_match.group(1).replace(',', '')

            # Quantity
            qty_match = re.search(r'(Total Qty|Total Quantity)[^\d]*([\d,]+)', text, re.I)
            if qty_match:
                fields["quantity"] = qty_match.group(2).replace(',', '')

            date_match = re.search(r'(Invoice Date|Date)[\s:]*([0-9]{2}[\/\.\-][0-9]{2}[\/\.\-][0-9]{4}|[A-Za-z]{3,9} \d{1,2}, \d{4})', text, re.I)
            if date_match:
                fields["date"] = date_match.group(2).strip()

        # Error Handling for Missing Fields
        if not fields:
            logging.error("No fields extracted from document.")
        
    except Exception as e:
        logging.error(f"Error extracting fields: {e}")
    
    # Validate that all necessary fields are extracted (po_number, vendor, amount, date)
    missing_fields = []
    required_fields = ["po_number", "vendor", "amount", "date"]
    for field in required_fields:
        if not fields.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        logging.error(f"Missing fields: {', '.join(missing_fields)}")
        return {}

    return fields
