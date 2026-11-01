import re
from typing import Tuple, List, Dict
from sqlalchemy.orm import Session
from ..models.schemas import DocumentType
from ..models.database import DocumentModel
from ..audit.hash_chain import AuditChain

CUES: Dict[DocumentType, Dict[str, any]] = {
    DocumentType.ID_CARD: {
        "keywords": ["identity card", "national identity", "national id", "citizen", "republic of", "cardholder sign"],
        "weight": 1.2
    },
    DocumentType.APPLICATION_FORM: {
        "keywords": ["application form", "loan application", "applicant personal information", "personal loan", "form 104", "tenure"],
        "weight": 1.1
    },
    DocumentType.BANK_STATEMENT: {
        "keywords": ["account statement", "opening balance", "closing balance", "quarterly statement", "debit (inr)", "credit (inr)", "savings account"],
        "weight": 1.3
    },
    DocumentType.SALARY_SLIP: {
        "keywords": ["payslip", "salary slip", "gross earnings", "net take-home", "basic salary", "house rent allowance", "hra", "provident fund"],
        "weight": 1.3
    },
    DocumentType.UTILITY_BILL: {
        "keywords": ["electricity", "water board", "meter reading", "energy charges", "consumer id", "units consumed", "demand note"],
        "weight": 1.2
    },
    DocumentType.DECLARATION: {
        "keywords": ["affidavit", "formal declaration", "solemnly declare", "deponent", "notary public", "undertaking"],
        "weight": 1.2
    }
}

def classify_text_and_layout(text: str) -> Tuple[str, float, List[str]]:
    """
    Hybrid heuristic classifier for document types based on text cues, regex patterns, and density.
    Returns (doc_type, confidence, reasons).
    """
    text_lower = text.lower()
    scores = {}
    triggered_cues = {}
    
    for dtype, cfg in CUES.items():
        score = 0.0
        cues_hit = []
        for kw in cfg["keywords"]:
            if kw in text_lower:
                score += 1.0 * cfg["weight"]
                cues_hit.append(f"Matched keyword '{kw}'")
                
        # Specialized regex checks
        if dtype == DocumentType.ID_CARD and re.search(r"id[-\s]?\d{4}[-\s]?\d{4}", text_lower):
            score += 2.0
            cues_hit.append("Matched National ID pattern format")
        elif dtype == DocumentType.BANK_STATEMENT and ("inr" in text_lower and "balance" in text_lower):
            score += 1.5
            cues_hit.append("Matched bank currency ledger format")
        elif dtype == DocumentType.SALARY_SLIP and ("deductions" in text_lower and "earnings" in text_lower):
            score += 2.0
            cues_hit.append("Matched payroll earnings-deductions layout structure")
        elif dtype == DocumentType.UTILITY_BILL and re.search(r"\bkwh\b|units", text_lower):
            score += 2.0
            cues_hit.append("Matched utility power consumption units (kWh)")
            
        scores[dtype.value] = score
        triggered_cues[dtype.value] = cues_hit
        
    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]
    
    if max_score < 1.0:
        return "other", 0.40, ["Insufficient matching keywords to reliably classify document"]
        
    confidence = min(0.98, round(0.50 + (max_score * 0.10), 2))
    return best_type, confidence, triggered_cues[best_type]

def classify_document(doc: DocumentModel, text: str, db: Session) -> Tuple[str, float, List[str]]:
    doc_type, conf, reasons = classify_text_and_layout(text)
    
    import json
    doc.doc_type = doc_type
    doc.doc_type_confidence = conf
    doc.classification_reasons = json.dumps(reasons)
    db.commit()
    
    AuditChain.record_event(
        db,
        action="DOCUMENT_CLASSIFIED",
        actor="system",
        payload={
            "document_id": doc.document_id,
            "filename": doc.filename,
            "doc_type": doc_type,
            "confidence": conf,
            "reasons": reasons
        }
    )
    return doc_type, conf, reasons
