import fitz  # PyMuPDF
import re

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        page_text = page.get_text()
        if not page_text.strip():
            # If no text, try OCR
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            page_text = pytesseract.image_to_string(img)
        text += page_text
    return text

def extract_fields(text, doc_type):
    fields = {}

    # --- PO Extraction ---
    if doc_type == "po":
        # PO Number
        po_match = re.search(r'Purchase Order No\s*:\s*([A-Za-z0-9\-\/]+)', text, re.I)
        if po_match:
            fields["po_number"] = po_match.group(1).strip()

        # Vendor (look for "Vendor Details" or "Vendor" or "Billed By")
        vendor_match = re.search(r'Vendor Details\s*:.*?\n([A-Z0-9 &\.\-]+)', text, re.I)
        if vendor_match:
            fields["vendor"] = vendor_match.group(1).strip()
        else:
            vendor_block = re.search(r'Vendor Details\s*:.*?(\n.*?)(?:Vendor GSTIN|P\.O\. Date)', text, re.I|re.S)
            if vendor_block:
                fields["vendor"] = vendor_block.group(1).replace('\n', ' ').strip()

        # Buyer (look for "Buyer", "Billed To", or your company name)
        buyer_match = re.search(r'(Buyer|Billed To)[^\n]*\n([^\n]+)', text, re.I)
        if buyer_match:
            fields["buyer"] = buyer_match.group(2).strip()
        else:
            # Try to extract your company name (example: Advik Autocomp Pvt. Ltd.)
            buyer_match2 = re.search(r'Advik Autocomp Pvt\. Ltd\.[^\n]*', text, re.I)
            if buyer_match2:
                fields["buyer"] = buyer_match2.group(0).strip()

        # Total Amount (look for "Total", "Total Amount", "Grand Total", "Amount Payable")
        amt_match = re.search(r'(Total Amount|Grand Total|Total|Amount Payable)[^\d]*([\d,]+\.\d{2})', text, re.I)
        if not amt_match:
            # Try to find the last number with 2 decimals (often the total)
            amounts = re.findall(r'([\d,]+\.\d{2})', text)
            if amounts:
                fields["amount"] = max([a.replace(',', '') for a in amounts], key=lambda x: float(x))
        else:
            fields["amount"] = amt_match.group(2).replace(',', '')

        # Total Quantity (look for "Total Qty", "Total Quantity", or sum all quantities in table)
        qty_match = re.search(r'(Total Qty|Total Quantity)[^\d]*([\d,]+)', text, re.I)
        if qty_match:
            fields["quantity"] = qty_match.group(2).replace(',', '')
        else:
            # Try to sum all quantities in a table (look for lines with qty)
            qtys = re.findall(r'\n\s*(\d{1,5})\s+[A-Za-z ]+\s+[A-Za-z ]+\s+[A-Za-z ]+\s+[\d,]+\.\d{2}', text)
            if qtys:
                fields["quantity"] = str(sum([int(q) for q in qtys]))

        # Date (look for "P.O. Date", "PO Date", "Date")
        date_match = re.search(r'(P\.O\. Date|PO Date|Date)[\s:]*([0-9]{2}[\/\.\-][0-9]{2}[\/\.\-][0-9]{4}|[A-Za-z]{3,9} \d{1,2}, \d{4})', text, re.I)
        if date_match:
            fields["date"] = date_match.group(2).strip()

    # --- Invoice Extraction ---
    elif doc_type == "invoice":
        # PO Number
        po_match = re.search(r'(PO No|PO Number|Purchase Order No)[\s:]*([A-Za-z0-9\-\/]+)', text, re.I)
        if po_match:
            fields["po_number"] = po_match.group(2).strip()

        # Invoice Number
        inv_match = re.search(r'(Invoice No|Invoice Number)[\s#:\-]*([A-Za-z0-9\-\/]+)', text, re.I)
        if inv_match:
            fields["invoice_number"] = inv_match.group(2).strip()

        # Vendor (Billed By)
        vendor_match = re.search(r'Billed By[^\n]*\n([^\n]+)', text, re.I)
        if vendor_match:
            fields["vendor"] = vendor_match.group(1).strip()

        # Buyer (Billed To)
        buyer_match = re.search(r'Billed To[^\n]*\n([^\n]+)', text, re.I)
        if buyer_match:
            fields["buyer"] = buyer_match.group(1).strip()

        # Total Amount (look for "Total (INR)", "Total Amount", "Grand Total", "Amount Payable")
        amt_match = re.search(r'(Total \(INR\)|Total Amount|Grand Total|Amount Payable)[^\d]*([\d,]+\.\d{2})', text, re.I)
        if not amt_match:
            amt_match = re.findall(r'([\d,]+\.\d{2})', text)
            if amt_match:
                fields["amount"] = amt_match[-1].replace(',', '')
        else:
            fields["amount"] = amt_match.group(2).replace(',', '')

        # Total Quantity (look for "Total Qty", "Total Quantity", or sum all quantities in table)
        qty_match = re.search(r'(Total Qty|Total Quantity)[^\d]*([\d,]+)', text, re.I)
        if qty_match:
            fields["quantity"] = qty_match.group(2).replace(',', '')
        else:
            qtys = re.findall(r'\n\s*(\d{1,5})\s+[A-Za-z ]+\s+[A-Za-z ]+\s+[A-Za-z ]+\s+[\d,]+\.\d{2}', text)
            if qtys:
                fields["quantity"] = str(sum([int(q) for q in qtys]))

        # Date (look for "Invoice Date", "Date")
        date_match = re.search(r'(Invoice Date|Date)[\s:]*([0-9]{2}[\/\.\-][0-9]{2}[\/\.\-][0-9]{4}|[A-Za-z]{3,9} \d{1,2}, \d{4})', text, re.I)
        if date_match:
            fields["date"] = date_match.group(2).strip()

    return fields
