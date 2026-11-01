import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models.database import AuditEventModel
from .hash_chain import compute_payload_hash, compute_entry_hash, GENESIS_PREV_HASH

def verify_audit_chain(db: Session) -> Dict[str, Any]:
    """
    Verifies cryptographic integrity of the entire audit trail:
    1. Re-computes each event's payload_hash from its details_json.
    2. Checks that prev_hash matches the previous event's entry_hash (or GENESIS_PREV_HASH for event 0).
    3. Re-computes entry_hash and checks exact equality.
    Returns status, broken_at_id, details, and total verified events count.
    """
    events: List[AuditEventModel] = db.query(AuditEventModel).order_by(AuditEventModel.id.asc()).all()
    
    if not events:
        return {
            "is_valid": True,
            "total_events": 0,
            "message": "Audit chain is empty. Genesis state is clean.",
            "broken_event_id": None,
            "details": []
        }
        
    expected_prev = GENESIS_PREV_HASH
    
    for idx, ev in enumerate(events):
        # 1. Check prev_hash continuity
        if ev.prev_hash != expected_prev:
            return {
                "is_valid": False,
                "total_events": len(events),
                "verified_count": idx,
                "broken_event_id": ev.event_id,
                "broken_at_index": idx,
                "message": f"Hash chain broken at event #{ev.id} ({ev.event_id}): prev_hash {ev.prev_hash} does not match expected {expected_prev}",
                "reason": "PREV_HASH_MISMATCH"
            }
            
        # 2. Re-compute payload hash
        try:
            payload = json.loads(ev.details_json) if ev.details_json else {}
        except Exception as e:
            return {
                "is_valid": False,
                "total_events": len(events),
                "verified_count": idx,
                "broken_event_id": ev.event_id,
                "broken_at_index": idx,
                "message": f"Corrupt payload JSON in event #{ev.id}: {str(e)}",
                "reason": "CORRUPT_PAYLOAD"
            }
            
        expected_payload_hash = compute_payload_hash(payload)
        if ev.payload_hash != expected_payload_hash:
            return {
                "is_valid": False,
                "total_events": len(events),
                "verified_count": idx,
                "broken_event_id": ev.event_id,
                "broken_at_index": idx,
                "message": f"Payload tampering detected in event #{ev.id} ({ev.event_id}): payload_hash {ev.payload_hash} != computed {expected_payload_hash}",
                "reason": "PAYLOAD_TAMPERED"
            }
            
        # 3. Re-compute entry hash
        computed_entry = compute_entry_hash(
            prev_hash=ev.prev_hash,
            timestamp=ev.timestamp,
            actor=ev.actor,
            action=ev.action,
            payload_hash=ev.payload_hash
        )
        if ev.entry_hash != computed_entry:
            return {
                "is_valid": False,
                "total_events": len(events),
                "verified_count": idx,
                "broken_event_id": ev.event_id,
                "broken_at_index": idx,
                "message": f"Entry signature broken in event #{ev.id} ({ev.event_id}): entry_hash {ev.entry_hash} != recomputed {computed_entry}",
                "reason": "ENTRY_HASH_TAMPERED"
            }
            
        expected_prev = ev.entry_hash

    return {
        "is_valid": True,
        "total_events": len(events),
        "verified_count": len(events),
        "broken_event_id": None,
        "latest_hash": expected_prev,
        "message": f"Cryptographic integrity verified across all {len(events)} events in audit trail."
    }
