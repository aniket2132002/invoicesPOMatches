from rapidfuzz import fuzz
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_amount(amount):
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
    if not qty:
        return 0
    qty = re.sub(r'[^\d]', '', qty)
    try:
        return int(qty)
    except:
        return 0

def match_fields(po_fields, inv_fields, threshold=70):
    results = {}

    # Vendor
    po_vendor = normalize_text(po_fields.get("vendor", ""))
    inv_vendor = normalize_text(inv_fields.get("vendor", ""))
    vendor_score = fuzz.partial_ratio(po_vendor, inv_vendor)
    results["vendor"] = {"po": po_fields.get("vendor", ""), "invoice": inv_fields.get("vendor", ""), "score": vendor_score}

    # Buyer
    po_buyer = normalize_text(po_fields.get("buyer", ""))
    inv_buyer = normalize_text(inv_fields.get("buyer", ""))
    buyer_score = fuzz.partial_ratio(po_buyer, inv_buyer)
    results["buyer"] = {"po": po_fields.get("buyer", ""), "invoice": inv_fields.get("buyer", ""), "score": buyer_score}

    # PO Number
    po_number = normalize_text(po_fields.get("po_number", ""))
    inv_po_number = normalize_text(inv_fields.get("po_number", ""))
    po_number_score = fuzz.ratio(po_number, inv_po_number)
    results["po_number"] = {"po": po_fields.get("po_number", ""), "invoice": inv_fields.get("po_number", ""), "score": po_number_score}

    # Amount
    po_amt = normalize_amount(po_fields.get("amount", ""))
    inv_amt = normalize_amount(inv_fields.get("amount", ""))
    amount_score = 100 if abs(po_amt - inv_amt) < 1 else 0  # allow small rounding
    results["amount"] = {"po": po_fields.get("amount", ""), "invoice": inv_fields.get("amount", ""), "score": amount_score}

    # Quantity
    po_qty = normalize_quantity(po_fields.get("quantity", ""))
    inv_qty = normalize_quantity(inv_fields.get("quantity", ""))
    qty_score = 100 if po_qty == inv_qty and po_qty != 0 else 0
    results["quantity"] = {"po": po_fields.get("quantity", ""), "invoice": inv_fields.get("quantity", ""), "score": qty_score}

    # Date (optional, you can add fuzzy date comparison if needed)
    po_date = normalize_text(po_fields.get("date", ""))
    inv_date = normalize_text(inv_fields.get("date", ""))
    date_score = fuzz.partial_ratio(po_date, inv_date)
    results["date"] = {"po": po_fields.get("date", ""), "invoice": inv_fields.get("date", ""), "score": date_score}

    # Decide match: all scores above threshold (except amount, quantity, which are strict)
    is_match = (
        vendor_score >= threshold and
        buyer_score >= threshold and
        po_number_score >= threshold and
        amount_score == 100 and
        qty_score == 100
        # Optionally add: and date_score >= threshold
    )

    return is_match, results
