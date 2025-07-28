from rapidfuzz import fuzz
import re
import logging

def normalize_text(text):
    """
    Normalize the text by converting it to lowercase and removing non-alphanumeric characters.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_amount(amount):
    """
    Normalize the amount by removing non-numeric characters and converting it to float.
    """
    if not amount:
        return 0
    if isinstance(amount, float) or isinstance(amount, int):
        return float(amount)
    amount = re.sub(r'[^\d.]', '', str(amount))
    try:
        return float(amount)
    except:
        return 0

def normalize_quantity(qty):
    """
    Normalize quantity by removing non-numeric characters and converting to integer.
    """
    if not qty:
        return 0
    qty = re.sub(r'[^\d]', '', qty)
    try:
        return int(qty)
    except:
        return 0

def match_fields(po_fields, inv_fields, threshold=70):
    """
    Compare the extracted fields between PO and Invoice using fuzzy matching and return the results.
    """
    results = {}
    total_score = 0  # Initialize total score

    # Handle missing fields by assigning default values
    for field in ["vendor", "amount", "date", "supplier", "address"]:
        if field not in po_fields or not po_fields[field]:
            po_fields[field] = "-"  # Default value for missing fields in PO

        if field not in inv_fields or not inv_fields[field]:
            inv_fields[field] = "-"  # Default value for missing fields in Invoice

    # Vendor Matching (3 points if matches)
    po_vendor = normalize_text(po_fields.get("vendor", ""))
    inv_vendor = normalize_text(inv_fields.get("vendor", ""))
    vendor_score = fuzz.partial_ratio(po_vendor, inv_vendor)
    results["vendor"] = {"po": po_fields.get("vendor", ""), "invoice": inv_fields.get("vendor", ""), "score": vendor_score}
    if vendor_score > 95:
        total_score += 2  # 2 points for vendor match over 95%
    elif vendor_score > 80:
        total_score += 1  # 1 point for vendor match over 80%

    # PO Number Matching (3 points if matches)
    po_number = normalize_text(po_fields.get("po_number", ""))
    inv_po_number = normalize_text(inv_fields.get("po_number", ""))
    po_number_score = fuzz.ratio(po_number, inv_po_number)
    results["po_number"] = {"po": po_fields.get("po_number", ""), "invoice": inv_fields.get("po_number", ""), "score": po_number_score}
    if po_number_score == 100:
        total_score += 3  # 3 points for PO number match

    # Amount Matching (Including GST) (3 points if matches)
    po_amt = normalize_amount(po_fields.get("amount", ""))
    inv_amt = normalize_amount(inv_fields.get("amount", ""))
    gst_po = normalize_amount(po_fields.get("gst_amount", ""))
    gst_inv = normalize_amount(inv_fields.get("gst_amount", ""))
    
    # If GST is found, add GST to PO and compare to Invoice total
    po_total = po_amt + gst_po * 2  # Multiply GST by 2 to match both CGST and SGST
    inv_total = inv_amt + gst_inv * 2
    amount_score = 100 if abs(po_total - inv_total) < 1 else 0  # Small tolerance allowed for amounts
    results["amount"] = {"po": po_fields.get("amount", ""), "invoice": inv_fields.get("amount", ""), "score": amount_score}
    if amount_score == 100:
        total_score += 3  # 3 points for amount match with GST consideration

    # Quantity Matching (2 points if matches)
    po_qty = normalize_quantity(po_fields.get("quantity", ""))
    inv_qty = normalize_quantity(inv_fields.get("quantity", ""))
    qty_score = 100 if po_qty == inv_qty else 0
    results["quantity"] = {"po": po_fields.get("quantity", ""), "invoice": inv_fields.get("quantity", ""), "score": qty_score}
    if qty_score == 100:
        total_score += 2  # 2 points for quantity match

    # Date Matching (optional, you can add fuzzy date comparison if needed)
    po_date = normalize_text(po_fields.get("date", ""))
    inv_date = normalize_text(inv_fields.get("date", ""))
    date_score = fuzz.partial_ratio(po_date, inv_date)
    results["date"] = {"po": po_fields.get("date", ""), "invoice": inv_fields.get("date", ""), "score": date_score}

    # Final Decision: If score > 300, it's a match
    is_match = total_score >= 300

    # Log the final score for debugging purposes
    logging.info(f"Total match score: {total_score}")
    logging.info(f"Match decision: {'Match' if is_match else 'No Match'}")

    return is_match, results
