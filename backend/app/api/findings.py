import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..models.database import get_db, FindingModel
from ..models.schemas import ReviewUpdate
from ..audit.hash_chain import AuditChain

router = APIRouter(tags=["findings"])

@router.get("/cases/{case_id}/findings")
def list_findings(
    case_id: str,
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FindingModel).filter(FindingModel.case_id == case_id)
    if category:
        query = query.filter(FindingModel.category == category)
    if risk_level:
        query = query.filter(FindingModel.risk_level == risk_level)
    if document_id:
        query = query.filter(FindingModel.document_id == document_id)
        
    findings = query.order_by(FindingModel.id.asc()).all()
    results = []
    for f in findings:
        results.append({
            "finding_id": f.finding_id,
            "case_id": f.case_id,
            "document_id": f.document_id,
            "page": f.page,
            "title": f.title,
            "category": f.category,
            "risk_level": f.risk_level,
            "confidence": f.confidence,
            "detector": f.detector,
            "observation": f.observation,
            "technical_details": f.technical_details,
            "suspicious_view": f.suspicious_view,
            "innocent_view": f.innocent_view,
            "corroboration_count": f.corroboration_count,
            "formula_breakdown": f.formula_breakdown,
            "recommended_verification": f.recommended_verification,
            "bbox": json.loads(f.bbox_json) if f.bbox_json else None,
            "evidence_id": f.evidence_id,
            "status": f.status,
            "reviewer_notes": f.reviewer_notes,
            "created_at": f.created_at.isoformat() if f.created_at else ""
        })
    return results

@router.post("/findings/{finding_id}/review")
def review_finding(
    finding_id: str,
    payload: ReviewUpdate,
    db: Session = Depends(get_db)
):
    f = db.query(FindingModel).filter(FindingModel.finding_id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    prev_status = f.status
    f.status = payload.status.value
    if payload.reviewer_notes:
        f.reviewer_notes = payload.reviewer_notes
    db.commit()
    
    # Audit log
    AuditChain.record_event(
        db,
        action="HUMAN_REVIEW_ACTION",
        actor="reviewer",
        payload={
            "finding_id": finding_id,
            "case_id": f.case_id,
            "previous_status": prev_status,
            "new_status": f.status,
            "reviewer_notes": f.reviewer_notes
        }
    )
    return {"message": "Review recorded successfully", "finding_id": finding_id, "status": f.status}
