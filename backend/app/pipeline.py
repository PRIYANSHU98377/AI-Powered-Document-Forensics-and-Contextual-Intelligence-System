import os
import json
import asyncio
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from .core.config import settings
from .models.database import CaseModel, DocumentModel, DocumentPageModel, ExtractedFieldModel, FindingModel
from .models.schemas import RiskLevel, FindingCategory
from .classification.classifier import classify_document
from .ocr.tesseract_engine import run_tesseract, is_tesseract_available
from .ocr.easyocr_engine import run_easyocr, is_easyocr_available
from .ocr.pymupdf_engine import run_pymupdf_text
from .ocr.fusion import fuse_word_streams
from .extraction.field_extractor import extract_fields_from_words
from .forensics.manager import run_document_forensics
from .context.intra_doc_rules import run_intra_doc_rules
from .correlation.cross_doc import run_cross_document_correlation
from .reasoning.dual_view import enrich_findings_with_dual_view
from .reasoning.risk_levels import aggregate_case_risk
from .audit.hash_chain import AuditChain

# Global progress tracker for SSE streams: case_id -> list of progress event dicts
CASE_PROGRESS: Dict[str, list] = {}

def push_progress(case_id: str, stage: str, progress_pct: int, message: str, doc_name: str = ""):
    ev = {
        "stage": stage,
        "progress_pct": progress_pct,
        "message": message,
        "document": doc_name
    }
    CASE_PROGRESS.setdefault(case_id, []).append(ev)

def execute_pipeline_for_case(case_id: str, db: Session):
    """
    Executes the comprehensive 10-stage forensics pipeline for all documents in a case.
    Stages:
    1. Classification
    2. Double-OCR (Tesseract + EasyOCR / PyMuPDF fusion)
    3. Structured Field Extraction
    4. Visual Forensics Suite
    5. Intra-Document Contextual Verification
    6. Cross-Document Entity Correlation
    7. Dual-View Reasoning & Risk Scoring
    8. Dossier & Evidence Materialization
    """
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        return
        
    docs = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    if not docs:
        push_progress(case_id, "Completed", 100, "No documents to process")
        return
        
    push_progress(case_id, "Pipeline Started", 5, f"Beginning automated forensics on {len(docs)} documents")
    
    total_docs = len(docs)
    for idx, doc in enumerate(docs):
        d_idx = idx + 1
        pct_base = int(10 + (d_idx / total_docs) * 55)
        
        # 1. OCR & Text Extraction
        push_progress(case_id, "OCR & Extraction", pct_base - 5, f"Running multi-engine OCR extraction on {doc.filename}", doc.filename)
        
        pages = db.query(DocumentPageModel).filter(DocumentPageModel.document_id == doc.document_id).order_by(DocumentPageModel.page_number).all()
        all_doc_words = []
        full_text_parts = []
        
        for p in pages:
            # Engine 1: PyMuPDF or Tesseract
            orig_path = str(settings.STORAGE_DIR / f"{doc.document_id}_orig.{doc.filename.split('.')[-1]}")
            p1_words = []
            if doc.filename.lower().endswith(".pdf"):
                p1_words = run_pymupdf_text(orig_path, p.page_number, scale_x=p.width/612.0, scale_y=p.height/792.0)
            if not p1_words:
                p1_words = run_tesseract(p.image_path)
                
            # Engine 2: EasyOCR or Tesseract
            p2_words = []
            if is_easyocr_available():
                p2_words = run_easyocr(p.image_path)
            elif not doc.filename.lower().endswith(".pdf") and is_tesseract_available():
                p2_words = run_tesseract(p.image_path)
                
            # Double-OCR Fusion
            fused_words = fuse_word_streams(p1_words, p2_words, p.page_number, p.width, p.height)
            all_doc_words.extend(fused_words)
            full_text_parts.append(" ".join(w.text for w in fused_words))
            
        full_text = "\n".join(full_text_parts)
        
        # 2. Classification
        push_progress(case_id, "Classification", pct_base - 2, f"Classifying document structure and type", doc.filename)
        doc_type, conf, reasons = classify_document(doc, full_text, db)
        
        # 3. Field Extraction
        push_progress(case_id, "Field Extraction", pct_base, f"Extracting schema fields for {doc_type}", doc.filename)
        extract_fields_from_words(doc.document_id, doc_type, all_doc_words, full_text, db)
        
        # 4. Visual Forensics Suite
        push_progress(case_id, "Visual Forensics", pct_base + 3, f"Running ELA, copy-move, noise, and font detectors", doc.filename)
        run_document_forensics(doc, db)
        
        # 5. Intra-Doc Contextual Rules
        push_progress(case_id, "Contextual Rules", pct_base + 5, f"Verifying internal arithmetic and field logic", doc.filename)
        run_intra_doc_rules(doc, db)
        
        doc.status = "completed"
        db.commit()

    # 6. Cross-Document Correlation
    push_progress(case_id, "Cross-Document Correlation", 75, "Matching entities across documents and identifying conflicts")
    run_cross_document_correlation(case_id, db)
    
    # 7. Dual-View Reasoning & Risk Scoring
    push_progress(case_id, "Dual-View Reasoning", 88, "Synthesizing suspicious vs innocent interpretations for all findings")
    all_findings = db.query(FindingModel).filter(FindingModel.case_id == case_id).all()
    enrich_findings_with_dual_view(all_findings, db)
    
    # 8. Overall Case Risk Calculation
    risk_levels = [f.risk_level for f in all_findings]
    overall_case_risk = aggregate_case_risk(risk_levels)
    case.overall_risk = overall_case_risk.value
    case.status = "analyzed"
    db.commit()
    
    # 9. Audit Event
    AuditChain.record_event(
        db,
        action="CASE_PIPELINE_COMPLETED",
        actor="system",
        payload={
            "case_id": case_id,
            "overall_risk": case.overall_risk,
            "total_documents": len(docs),
            "total_findings": len(all_findings),
            "potential_manipulations": sum(1 for f in all_findings if f.category == "POTENTIAL_MANIPULATION")
        }
    )
    
    push_progress(case_id, "Completed", 100, f"Analysis complete. Overall Case Risk: {case.overall_risk}")
