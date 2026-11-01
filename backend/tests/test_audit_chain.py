import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.database import Base, AuditEventModel
from backend.app.audit.hash_chain import AuditChain, GENESIS_PREV_HASH
from backend.app.audit.verify import verify_audit_chain

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_audit_chain_creation_and_verification(db_session):
    # Empty chain verification
    result = verify_audit_chain(db_session)
    assert result["is_valid"] is True
    assert result["total_events"] == 0

    # Add 4 sequential events
    ev1 = AuditChain.record_event(
        db_session,
        action="DOCUMENT_UPLOADED",
        actor="analyst@example.com",
        payload={"filename": "id_card.png", "sha256": "abc123def456"}
    )
    assert ev1.prev_hash == GENESIS_PREV_HASH

    ev2 = AuditChain.record_event(
        db_session,
        action="PIPELINE_STEP_COMPLETED",
        actor="system",
        payload={"step": "CLASSIFICATION", "doc_type": "id_card"}
    )
    assert ev2.prev_hash == ev1.entry_hash

    ev3 = AuditChain.record_event(
        db_session,
        action="FINDING_GENERATED",
        actor="system",
        payload={"finding_id": "f-101", "risk": "MEDIUM"}
    )
    assert ev3.prev_hash == ev2.entry_hash

    ev4 = AuditChain.record_event(
        db_session,
        action="HUMAN_REVIEW_DECISION",
        actor="reviewer_jane",
        payload={"finding_id": "f-101", "decision": "CONFIRMED"}
    )
    assert ev4.prev_hash == ev3.entry_hash

    # Verify chain validity
    verification = verify_audit_chain(db_session)
    assert verification["is_valid"] is True
    assert verification["total_events"] == 4
    assert verification["verified_count"] == 4
    assert verification["broken_event_id"] is None

def test_audit_chain_tamper_detection_payload(db_session):
    # Record events
    ev1 = AuditChain.record_event(db_session, action="STEP_1", payload={"val": 100})
    ev2 = AuditChain.record_event(db_session, action="STEP_2", payload={"val": 200})
    ev3 = AuditChain.record_event(db_session, action="STEP_3", payload={"val": 300})

    # Tamper with row 2's details_json directly in the database
    ev2.details_json = json.dumps({"val": 999999})
    db_session.commit()

    # Verification must catch payload tampering
    res = verify_audit_chain(db_session)
    assert res["is_valid"] is False
    assert res["broken_event_id"] == ev2.event_id
    assert res["reason"] == "PAYLOAD_TAMPERED"

def test_audit_chain_tamper_detection_entry_hash(db_session):
    ev1 = AuditChain.record_event(db_session, action="UPLOAD", payload={"user": "bob"})
    ev2 = AuditChain.record_event(db_session, action="REVIEW", payload={"status": "approved"})

    # Tamper entry hash
    ev2.entry_hash = "deadbeef" * 8
    db_session.commit()

    res = verify_audit_chain(db_session)
    assert res["is_valid"] is False
    assert res["broken_event_id"] == ev2.event_id
    assert res["reason"] == "ENTRY_HASH_TAMPERED"
