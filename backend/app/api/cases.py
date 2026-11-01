import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..models.database import get_db, CaseModel, DocumentModel, FindingModel
from ..models.schemas import CaseInfo, RiskLevel
from ..pipeline import execute_pipeline_for_case, CASE_PROGRESS, push_progress
from ..audit.hash_chain import AuditChain

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("", response_model=Dict[str, Any])
def create_case(payload: Dict[str, str], db: Session = Depends(get_db)):
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    name = payload.get("name", f"Investigation Case {datetime.now().strftime('%Y%m%d-%H%M')}")
    description = payload.get("description", "")
    
    case = CaseModel(
        case_id=case_id,
        name=name,
        description=description,
        status="open",
        overall_risk="LOW"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    AuditChain.record_event(
        db,
        action="CASE_CREATED",
        actor="investigator",
        payload={"case_id": case_id, "name": name}
    )
    
    return {
        "case_id": case.case_id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "overall_risk": case.overall_risk
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).all()
    results = []
    for c in cases:
        doc_count = db.query(DocumentModel).filter(DocumentModel.case_id == c.case_id).count()
        findings_count = db.query(FindingModel).filter(FindingModel.case_id == c.case_id).count()
        results.append({
            "case_id": c.case_id,
            "name": c.name,
            "description": c.description,
            "status": c.status,
            "overall_risk": c.overall_risk,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "document_count": doc_count,
            "findings_count": findings_count
        })
    return results

@router.get("/{case_id}", response_model=Dict[str, Any])
def get_case(case_id: str, db: Session = Depends(get_db)):
    c = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
        
    doc_count = db.query(DocumentModel).filter(DocumentModel.case_id == c.case_id).count()
    findings_count = db.query(FindingModel).filter(FindingModel.case_id == c.case_id).count()
    return {
        "case_id": c.case_id,
        "name": c.name,
        "description": c.description,
        "status": c.status,
        "overall_risk": c.overall_risk,
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "document_count": doc_count,
        "findings_count": findings_count
    }

@router.post("/{case_id}/process")
def process_case(case_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Reset progress
    CASE_PROGRESS[case_id] = []
    # Execute pipeline synchronously or in background
    execute_pipeline_for_case(case_id, db)
    return {"message": "Pipeline completed successfully", "case_id": case_id, "overall_risk": case.overall_risk}

@router.get("/{case_id}/progress")
def stream_case_progress(case_id: str):
    """
    Server-Sent Events (SSE) streaming live progress for the pipeline stepper.
    """
    def event_generator():
        sent_count = 0
        while True:
            events = CASE_PROGRESS.get(case_id, [])
            if sent_count < len(events):
                for ev in events[sent_count:]:
                    yield f"data: {json.dumps(ev)}\n\n"
                sent_count = len(events)
                if sent_count > 0 and events[-1]["progress_pct"] >= 100:
                    break
            import time
            time.sleep(0.5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    AuditChain.record_event(
        db,
        action="CASE_PURGED",
        actor="investigator",
        payload={"case_id": case_id, "data_retention_policy": "case_records_purged_audit_retained"}
    )
    return {"message": f"Case {case_id} purged successfully"}
