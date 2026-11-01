import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..models.database import get_db, AuditEventModel
from ..audit.verify import verify_audit_chain

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/events")
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    total = db.query(AuditEventModel).count()
    events = db.query(AuditEventModel).order_by(AuditEventModel.id.desc()).offset(offset).limit(limit).all()
    results = []
    for ev in events:
        results.append({
            "id": ev.id,
            "event_id": ev.event_id,
            "timestamp": ev.timestamp,
            "actor": ev.actor,
            "action": ev.action,
            "payload_hash": ev.payload_hash,
            "prev_hash": ev.prev_hash,
            "entry_hash": ev.entry_hash,
            "details": json.loads(ev.details_json or "{}")
        })
    return {"total": total, "events": results}

@router.get("/verify")
def verify_audit_integrity(db: Session = Depends(get_db)):
    """
    Verifies the cryptographic chain from genesis to leaf.
    Returns boolean is_valid, total_events, and details if broken.
    """
    return verify_audit_chain(db)

@router.post("/tamper-demo")
def tamper_database_demo(db: Session = Depends(get_db)):
    """
    Demonstration endpoint:
    Artificially modifies one event's details_json directly in SQLite
    to demonstrate immediate detection by verify_audit_chain.
    """
    ev = db.query(AuditEventModel).order_by(AuditEventModel.id.desc()).first()
    if not ev:
        raise HTTPException(status_code=400, detail="Audit chain is empty, no event to tamper")
        
    old_json = ev.details_json
    # Tamper with the row
    ev.details_json = json.dumps({"TAMPERED_INTRUSION": "Malicious direct SQL modification attempt", "timestamp": "FORGED"})
    db.commit()
    
    return {
        "tampered": True,
        "event_id": ev.event_id,
        "message": f"Event #{ev.id} payload directly altered in database without updating cryptographic hash. Run /audit/verify to observe detection."
    }
