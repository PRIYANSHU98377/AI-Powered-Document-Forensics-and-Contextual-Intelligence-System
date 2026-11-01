import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..models.database import get_db, EvidenceModel

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.get("/{evidence_id}")
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    return {
        "evidence_id": ev.evidence_id,
        "case_id": ev.case_id,
        "document_id": ev.document_id,
        "page": ev.page,
        "detector": ev.detector,
        "score": ev.score,
        "status": ev.status,
        "observation": ev.observation,
        "bbox": json.loads(ev.bbox_json) if ev.bbox_json else None,
        "has_crop": bool(ev.crop_path and os.path.exists(ev.crop_path)),
        "has_overlay": bool(ev.overlay_path and os.path.exists(ev.overlay_path))
    }

@router.get("/{evidence_id}/crop")
def get_evidence_crop(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence_id).first()
    if not ev or not ev.crop_path or not os.path.exists(ev.crop_path):
        raise HTTPException(status_code=404, detail="Evidence crop image not found")
    return FileResponse(ev.crop_path, media_type="image/png")

@router.get("/{evidence_id}/overlay")
def get_evidence_overlay(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence_id).first()
    if not ev or not ev.overlay_path or not os.path.exists(ev.overlay_path):
        raise HTTPException(status_code=404, detail="Evidence overlay image not found")
    return FileResponse(ev.overlay_path, media_type="image/png")
