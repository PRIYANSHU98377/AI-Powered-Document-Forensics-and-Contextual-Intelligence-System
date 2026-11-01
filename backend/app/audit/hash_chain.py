import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.database import AuditEventModel

GENESIS_PREV_HASH = "0" * 64

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Produce deterministically ordered, whitespace-minimized JSON string.
    Essential for reproducible cryptographic hashing.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_payload_hash(payload: Dict[str, Any]) -> str:
    serialized = canonical_json(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def compute_entry_hash(prev_hash: str, timestamp: str, actor: str, action: str, payload_hash: str) -> str:
    """
    entry_hash = SHA-256(prev_hash + canonical header + payload_hash)
    """
    header = {
        "prev_hash": prev_hash,
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "payload_hash": payload_hash,
    }
    canonical = canonical_json(header)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

class AuditChain:
    """
    Tamper-evident append-only hash chain adhering to digital evidence preservation principles
    (inspired by ISO/IEC 27037: identification, collection, acquisition, and preservation of digital evidence).
    """
    
    @staticmethod
    def get_latest_hash(db: Session) -> str:
        latest = db.query(AuditEventModel).order_by(AuditEventModel.id.desc()).first()
        if latest:
            return latest.entry_hash
        return GENESIS_PREV_HASH

    @classmethod
    def record_event(
        cls,
        db: Session,
        action: str,
        actor: str = "system",
        payload: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> AuditEventModel:
        if payload is None:
            payload = {}
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
            
        prev_hash = cls.get_latest_hash(db)
        payload_hash = compute_payload_hash(payload)
        entry_hash = compute_entry_hash(prev_hash, timestamp, actor, action, payload_hash)
        
        event = AuditEventModel(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            actor=actor,
            action=action,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            details_json=json.dumps(payload, ensure_ascii=False)
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
