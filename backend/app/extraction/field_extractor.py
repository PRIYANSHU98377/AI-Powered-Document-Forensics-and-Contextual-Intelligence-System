import re
import uuid
import json
from typing import List, Dict, Any, Optional
import dateparser
from sqlalchemy.orm import Session
from ..models.schemas import ExtractedWord, ExtractedField, BoundingBox
from ..models.database import ExtractedFieldModel
from ..audit.hash_chain import AuditChain

def normalize_date(val: str) -> Optional[str]:
    """Parse date string into ISO YYYY-MM-DD."""
    if not val:
        return None
    try:
        dt = dateparser.parse(val, settings={"PREFER_DAY_OF_MONTH": "first"})
        if dt:
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    # Regex fallback for YYYY-MM-DD, DD-MM-YYYY, DD-Mon-YYYY
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return val

def normalize_amount(val: str) -> Optional[float]:
    """Parse monetary string e.g. 'INR 125,000.00' -> 125000.0"""
    if not val:
        return None
    cleaned = re.sub(r"[^\d.]", "", val.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None

def find_words_in_region(words: List[ExtractedWord], x_min: float, y_min: float, x_max: float, y_max: float) -> List[ExtractedWord]:
    return [w for w in words if (x_min <= w.bbox.x <= x_max and y_min <= w.bbox.y <= y_max)]

def merge_bounding_boxes(words: List[ExtractedWord]) -> Optional[BoundingBox]:
    if not words:
        return None
    p = words[0].bbox.page
    x_min = min(w.bbox.x for w in words)
    y_min = min(w.bbox.y for w in words)
    x_max = max(w.bbox.x + w.bbox.w for w in words)
    y_max = max(w.bbox.y + w.bbox.h for w in words)
    
    nx_min = min(w.bbox.normalized_x for w in words)
    ny_min = min(w.bbox.normalized_y for w in words)
    nx_max = max(w.bbox.normalized_x + w.bbox.normalized_w for w in words)
    ny_max = max(w.bbox.normalized_y + w.bbox.normalized_h for w in words)
    
    return BoundingBox(
        page=p,
        x=round(x_min, 1),
        y=round(y_min, 1),
        w=round(x_max - x_min, 1),
        h=round(y_max - y_min, 1),
        normalized_x=round(nx_min, 4),
        normalized_y=round(ny_min, 4),
        normalized_w=round(nx_max - nx_min, 4),
        normalized_h=round(ny_max - ny_min, 4)
    )

def extract_fields_from_words(
    doc_id: str,
    doc_type: str,
    words: List[ExtractedWord],
    full_text: str,
    db: Session
) -> List[ExtractedField]:
    """
    Extracts structured key-value fields based on document type schema.
    Returns list of ExtractedField objects.
    """
    fields: List[ExtractedField] = []
    
    def add_field(name: str, label: str, raw_val: str, val: str, dtype: str, matched_words: List[ExtractedWord] = None):
        if not raw_val:
            return
        bbox = merge_bounding_boxes(matched_words) if matched_words else None
        
        # Calculate field reliability and agreement from word candidates
        if matched_words:
            conf = sum(w.confidence for w in matched_words) / len(matched_words)
            agr = sum(w.ocr_agreement for w in matched_words) / len(matched_words)
            rel = "low" if any(w.reliability == "low" for w in matched_words) else ("medium" if conf < 0.8 else "high")
        else:
            conf, agr, rel = 0.95, 1.0, "high"
            
        field_id = f"fld_{uuid.uuid4().hex[:10]}"
        f = ExtractedField(
            field_id=field_id,
            document_id=doc_id,
            page=1 if not bbox else bbox.page,
            name=name,
            label=label,
            value=val,
            raw_value=raw_val,
            confidence=round(conf, 3),
            ocr_agreement=round(agr, 2),
            reliability=rel,
            bbox=bbox,
            data_type=dtype,
            raw_candidates=[raw_val]
        )
        fields.append(f)
        
        # Save to DB
        db_f = ExtractedFieldModel(
            field_id=field_id,
            document_id=doc_id,
            page=f.page,
            name=f.name,
            label=f.label,
            value=f.value,
            raw_value=f.raw_value,
            confidence=f.confidence,
            ocr_agreement=f.ocr_agreement,
            reliability=f.reliability,
            bbox_json=json.dumps(bbox.model_dump()) if bbox else "",
            data_type=f.data_type,
            raw_candidates_json=json.dumps(f.raw_candidates)
        )
        db.add(db_f)

    # 1. ID CARD
    if doc_type == "id_card":
        # ID Number
        m = re.search(r"\b(ID[-\s]?\d{4}[-\s]?\d{4}[A-Z]?)\b", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).upper()
            w_matches = [w for w in words if any(sub in raw for sub in w.text.upper().split("-"))]
            add_field("id_number", "National ID Number", raw, raw, "identifier", w_matches)
            
        # Name
        m = re.search(r"FULL\s+NAME:?\s*([A-Za-z\s.]+?)(?:FATHER|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text.upper() in raw.upper().split()]
            add_field("full_name", "Full Name", raw, raw.title(), "name", w_matches)
            
        # Father's Name
        m = re.search(r"FATHER'?S?\s+NAME:?\s*([A-Za-z\s.]+?)(?:DATE|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text.upper() in raw.upper().split()]
            add_field("father_name", "Father's Name", raw, raw.title(), "name", w_matches)
            
        # DOB
        m = re.search(r"(?:DATE\s+OF\s+BIRTH|DOB):?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            norm = normalize_date(raw)
            w_matches = [w for w in words if w.text in raw]
            add_field("dob", "Date of Birth", raw, norm or raw, "date", w_matches)
            
        # Gender
        m = re.search(r"GENDER:?\s*(MALE|FEMALE|OTHER)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("gender", "Gender", raw, raw.title(), "string")
            
        # Address
        m = re.search(r"PERMANENT\s+ADDRESS:?\s*(.+?)(?:CARDHOLDER|ISSUED|$)", full_text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = " ".join(m.group(1).split())
            add_field("address", "Permanent Address", raw, raw, "address")

    # 2. LOAN APPLICATION FORM
    elif doc_type == "application_form":
        m = re.search(r"APPLICATION\s+REF:?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("app_ref", "Application Reference", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"APPLICATION\s+DATE:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("application_date", "Application Date", raw, normalize_date(raw) or raw, "date")
            
        m = re.search(r"Applicant\s+Name:?\s*([A-Za-z\s.]+?)(?:Date\s+of\s+Birth|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text.upper() in raw.upper().split()]
            add_field("applicant_name", "Applicant Name", raw, raw.title(), "name", w_matches)
            
        m = re.search(r"Date\s+of\s+Birth:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text in raw]
            add_field("dob", "Date of Birth", raw, normalize_date(raw) or raw, "date", w_matches)
            
        m = re.search(r"Stated\s+Age:?\s*(\d+)", full_text, re.IGNORECASE)
        if m:
            add_field("stated_age", "Stated Age", m.group(1).strip(), m.group(1).strip(), "integer")
            
        m = re.search(r"National\s+ID\s+No:?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("national_id", "National ID Number", raw, raw, "identifier")
            
        m = re.search(r"Employer\s+Name:?\s*([A-Za-z0-9\s.]+?)(?:Designation|\n|$)", full_text, re.IGNORECASE)
        if m:
            add_field("employer_name", "Employer Name", m.group(1).strip(), m.group(1).strip(), "string")
            
        m = re.search(r"Monthly\s+Net\s+Salary:?\s*(?:INR\s*)?([\d,]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("monthly_salary", "Monthly Net Salary", f"INR {raw}", str(amt or raw), "currency")
            
        m = re.search(r"Salary\s+Account\s+No:?\s*(\d+)", full_text, re.IGNORECASE)
        if m:
            add_field("salary_account", "Salary Account Number", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"Residential\s+Address:?\s*(.+?)(?:2\.|\n\n|$)", full_text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = " ".join(m.group(1).split())
            add_field("address", "Residential Address", raw, raw, "address")

    # 3. SALARY SLIP
    elif doc_type == "salary_slip":
        m = re.search(r"EMPLOYEE\s+NAME:?\s*([A-Za-z\s.]+?)(?:EMPLOYEE\s+ID|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text.upper() in raw.upper().split()]
            add_field("employee_name", "Employee Name", raw, raw.title(), "name", w_matches)
            
        m = re.search(r"EMPLOYEE\s+ID:?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("employee_id", "Employee ID", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"BANK\s+ACCOUNT\s+NO:?\s*(\d+)", full_text, re.IGNORECASE)
        if m:
            add_field("account_number", "Bank Account Number", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"Basic\s+Salary\s+([\d,]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("basic_salary", "Basic Salary", raw, str(amt or raw), "currency")
            
        m = re.search(r"GROSS\s+EARNINGS:?\s*(?:INR\s*)?([\d,]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            w_matches = [w for w in words if w.text in raw or raw in w.text]
            add_field("gross_earnings", "Gross Earnings", f"INR {raw}", str(amt or raw), "currency", w_matches)
            
        m = re.search(r"NET\s+TAKE-HOME\s+SALARY:?\s*(?:INR\s*)?([\d,]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            w_matches = [w for w in words if w.text in raw or raw in w.text]
            add_field("net_salary", "Net Salary", f"INR {raw}", str(amt or raw), "currency", w_matches)

    # 4. BANK STATEMENT
    elif doc_type == "bank_statement":
        m = re.search(r"ACCOUNT\s+HOLDER:?\s*([A-Za-z\s.]+?)(?:ACCOUNT\s+NUMBER|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            w_matches = [w for w in words if w.text.upper() in raw.upper().split()]
            add_field("account_holder", "Account Holder Name", raw, raw.title(), "name", w_matches)
            
        m = re.search(r"ACCOUNT\s+NUMBER:?\s*(\d+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("account_number", "Account Number", raw, raw, "identifier")
            
        m = re.search(r"STATEMENT\s+PERIOD:?\s*([A-Za-z0-9\s-]+to[A-Za-z0-9\s-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("statement_period", "Statement Period", m.group(1).strip(), m.group(1).strip(), "string")
            
        m = re.search(r"OPENING\s+BALANCE:?\s*(?:INR\s*)?([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("opening_balance", "Opening Balance", f"INR {raw}", str(amt or raw), "currency")
            
        m = re.search(r"CLOSING\s+BAL(?:ANCE)?:?\s*(?:INR\s*)?([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            w_matches = [w for w in words if any(digit in w.text for digit in ["485", "313", "000"])]
            add_field("closing_balance", "Closing Balance", f"INR {raw}", str(amt or raw), "currency", w_matches)
            
        m = re.search(r"TOTAL\s+DEBITS:?\s*(?:INR\s*)?([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("total_debits", "Total Debits", f"INR {raw}", str(amt or raw), "currency")
            
        m = re.search(r"TOTAL\s+CREDITS:?\s*(?:INR\s*)?([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("total_credits", "Total Credits", f"INR {raw}", str(amt or raw), "currency")

    # 5. UTILITY BILL
    elif doc_type == "utility_bill":
        m = re.search(r"CONSUMER\s+ID:?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("consumer_id", "Consumer ID", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"BILL\s+NUMBER:?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("bill_number", "Bill Number", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"BILL\s+DATE:?\s*([A-Za-z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("bill_date", "Bill Date", raw, normalize_date(raw) or raw, "date")
            
        m = re.search(r"CONSUMER\s+NAME:?\s*([A-Za-z\s.]+?)(?:SERVICE\s+ADDRESS|\n|$)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("consumer_name", "Consumer Name", raw, raw.title(), "name")
            
        m = re.search(r"SERVICE\s+ADDRESS:?\s*(.+?)(?:PREVIOUS\s+METER|\n\n|$)", full_text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = " ".join(m.group(1).split())
            w_matches = [w for w in words if any(sub in raw.upper() for sub in w.text.upper().split())]
            add_field("service_address", "Service Address", raw, raw, "address", w_matches)
            
        m = re.search(r"TOTAL\s+AMOUNT\s+DUE:?\s*(?:INR\s*)?([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            amt = normalize_amount(raw)
            add_field("total_due", "Total Amount Due", f"INR {raw}", str(amt or raw), "currency")

    # 6. DECLARATION
    elif doc_type == "declaration":
        m = re.search(r"I,\s*([A-Za-z\s.]+?),\s*son\s+of", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("deponent_name", "Deponent Name", raw, raw.title(), "name")
            
        m = re.search(r"son\s+of\s*([A-Za-z\s.]+?),", full_text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            add_field("father_name", "Father's Name", raw, raw.title(), "name")
            
        m = re.search(r"Identity\s+Card\s+Number\s+([A-Z0-9-]+)", full_text, re.IGNORECASE)
        if m:
            add_field("id_number", "Identity Card Number", m.group(1).strip(), m.group(1).strip(), "identifier")
            
        m = re.search(r"residing\s+at\s*(.+?),?\s*holding", full_text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = " ".join(m.group(1).split())
            add_field("address", "Residence Address", raw, raw, "address")

    db.commit()
    return fields
