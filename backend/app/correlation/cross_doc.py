import uuid
import json
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.database import DocumentModel, ExtractedFieldModel, FindingModel, EvidenceModel
from ..audit.hash_chain import AuditChain
from .entity_matching import match_names, match_dob, match_address, match_ids, MatchResult

def run_cross_document_correlation(
    case_id: str,
    db: Session
) -> List[FindingModel]:
    """
    Correlates extracted entities across all documents within an investigation case.
    Identifies exact matches, tolerated transcription variants, and critical entity conflicts.
    """
    docs = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    if len(docs) < 2:
        return []
        
    doc_fields: Dict[str, Dict[str, ExtractedFieldModel]] = {}
    for d in docs:
        fields = db.query(ExtractedFieldModel).filter(ExtractedFieldModel.document_id == d.document_id).all()
        doc_fields[d.document_id] = {f.name: f for f in fields}
        
    findings_created = []
    
    # 1. CROSS-DOCUMENT DOB CONFLICT (e.g. ID Card vs Application Form)
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            d1, d2 = docs[i], docs[j]
            f1_dob = doc_fields[d1.document_id].get("dob")
            f2_dob = doc_fields[d2.document_id].get("dob")
            
            if f1_dob and f2_dob:
                res, score, expl = match_dob(f1_dob.value, f2_dob.value)
                if res == MatchResult.CONFLICT:
                    f_id = f"fnd_{uuid.uuid4().hex[:10]}"
                    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
                    
                    bbox_data = json.loads(f1_dob.bbox_json) if f1_dob.bbox_json else {"page": 1, "x": 260, "y": 275, "w": 140, "h": 25}
                    
                    ev = EvidenceModel(
                        evidence_id=ev_id,
                        case_id=case_id,
                        document_id=d1.document_id,
                        page=f1_dob.page,
                        detector="cross_doc_dob_correlator",
                        bbox_json=json.dumps(bbox_data),
                        score=0.95,
                        status="POTENTIAL_MANIPULATION",
                        observation=f"Date of Birth conflict: '{f1_dob.value}' on {d1.filename} contradicts '{f2_dob.value}' on {d2.filename}."
                    )
                    db.add(ev)
                    
                    f = FindingModel(
                        finding_id=f_id,
                        case_id=case_id,
                        document_id=d1.document_id,
                        page=f1_dob.page,
                        title="Cross-Document Date of Birth Conflict",
                        category="POTENTIAL_MANIPULATION",
                        risk_level="HIGH",
                        confidence=0.95,
                        detector="cross_doc_dob_correlator",
                        observation=f"Critical identity attribute mismatch: {d1.filename} states DOB '{f1_dob.value}', whereas {d2.filename} states '{f2_dob.value}'.",
                        technical_details=f"Field 1 ({d1.filename}): {f1_dob.value}. Field 2 ({d2.filename}): {f2_dob.value}. Strict date match delta != 0.",
                        suspicious_view="A submitted document may belong to an impostor or was modified to meet age/tenure eligibility requirements.",
                        innocent_view="Clerical keying error at identity registration, or date format confusion (e.g. DD/MM vs MM/DD).",
                        corroboration_count=2,
                        formula_breakdown="High-severity identity conflict. Cross-doc contradiction weight: 1.0.",
                        recommended_verification="Mandate physical biometric ID verification or fetch digital record directly from national identity registry.",
                        bbox_json=json.dumps(bbox_data),
                        evidence_id=ev_id,
                        status="PENDING"
                    )
                    db.add(f)
                    findings_created.append(f)

    # 2. CROSS-DOCUMENT ADDRESS CONFLICT (e.g. Utility Bill vs Application / ID)
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            d1, d2 = docs[i], docs[j]
            # Check fields named 'address' or 'service_address'
            f1_addr = doc_fields[d1.document_id].get("address") or doc_fields[d1.document_id].get("service_address")
            f2_addr = doc_fields[d2.document_id].get("address") or doc_fields[d2.document_id].get("service_address")
            
            if f1_addr and f2_addr:
                res, score, expl = match_address(f1_addr.value, f2_addr.value)
                if res == MatchResult.CONFLICT:
                    f_id = f"fnd_{uuid.uuid4().hex[:10]}"
                    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
                    
                    bbox_data = json.loads(f1_addr.bbox_json) if f1_addr.bbox_json else {"page": 1, "x": 40, "y": 230, "w": 300, "h": 40}
                    
                    ev = EvidenceModel(
                        evidence_id=ev_id,
                        case_id=case_id,
                        document_id=d1.document_id,
                        page=f1_addr.page,
                        detector="cross_doc_address_correlator",
                        bbox_json=json.dumps(bbox_data),
                        score=0.88,
                        status="POTENTIAL_MANIPULATION",
                        observation=f"Address conflict: '{f1_addr.value}' on {d1.filename} does not match '{f2_addr.value}' on {d2.filename}. {expl}."
                    )
                    db.add(ev)
                    
                    f = FindingModel(
                        finding_id=f_id,
                        case_id=case_id,
                        document_id=d1.document_id,
                        page=f1_addr.page,
                        title="Cross-Document Residential Address Discrepancy",
                        category="POTENTIAL_MANIPULATION",
                        risk_level="HIGH",
                        confidence=0.88,
                        detector="cross_doc_address_correlator",
                        observation=f"Address mismatch: {d1.filename} lists '{f1_addr.value}', while {d2.filename} lists '{f2_addr.value}'. {expl}.",
                        technical_details=f"Fuzzy token score={score:.2f}. Expl={expl}.",
                        suspicious_view="Utility bill may belong to a third party or applicant furnished fabricated proof of address.",
                        innocent_view="Applicant recently relocated, owns multiple properties, or utility bill is registered to a landlord/family member.",
                        corroboration_count=1,
                        formula_breakdown=f"Address similarity score: {score:.2f} (Threshold < 0.60).",
                        recommended_verification="Request rental agreement, recent property tax receipt, or conduct field address verification.",
                        bbox_json=json.dumps(bbox_data),
                        evidence_id=ev_id,
                        status="PENDING"
                    )
                    db.add(f)
                    findings_created.append(f)

    # 3. NAME VARIATION AUDIT (Check for tolerated variations vs conflicts)
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            d1, d2 = docs[i], docs[j]
            f1_name = (
                doc_fields[d1.document_id].get("full_name") or
                doc_fields[d1.document_id].get("applicant_name") or
                doc_fields[d1.document_id].get("employee_name") or
                doc_fields[d1.document_id].get("account_holder") or
                doc_fields[d1.document_id].get("consumer_name") or
                doc_fields[d1.document_id].get("deponent_name")
            )
            f2_name = (
                doc_fields[d2.document_id].get("full_name") or
                doc_fields[d2.document_id].get("applicant_name") or
                doc_fields[d2.document_id].get("employee_name") or
                doc_fields[d2.document_id].get("account_holder") or
                doc_fields[d2.document_id].get("consumer_name") or
                doc_fields[d2.document_id].get("deponent_name")
            )
            if f1_name and f2_name:
                res, score, expl = match_names(f1_name.value, f2_name.value)
                if res == MatchResult.TOLERATED_VARIATION:
                    # Record neutral OBSERVED finding (NOT manipulation, benign explanation)
                    f_id = f"fnd_{uuid.uuid4().hex[:10]}"
                    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
                    bbox_data = json.loads(f1_name.bbox_json) if f1_name.bbox_json else {"page": 1, "x": 100, "y": 100, "w": 150, "h": 25}
                    
                    f = FindingModel(
                        finding_id=f_id,
                        case_id=case_id,
                        document_id=d1.document_id,
                        page=f1_name.page,
                        title="Tolerated Name Formatting Variation",
                        category="OBSERVED",
                        risk_level="LOW",
                        confidence=score,
                        detector="entity_name_matcher",
                        observation=f"Tolerated name variation observed between '{f1_name.value}' ({d1.filename}) and '{f2_name.value}' ({d2.filename}): {expl}.",
                        technical_details=f"Lexical similarity: {score*100:.1f}%. Metaphone phonetic match confirmed.",
                        suspicious_view="Applicant name differs across submitted records.",
                        innocent_view="Common practice of abbreviating middle name or using initials on utility bills / payroll documents.",
                        corroboration_count=1,
                        formula_breakdown=f"Similarity score {score:.2f} >= 0.85 tolerance threshold.",
                        recommended_verification="Standard document processing; no escalation required.",
                        bbox_json=json.dumps(bbox_data),
                        evidence_id=ev_id,
                        status="PENDING"
                    )
                    db.add(f)
                    findings_created.append(f)

    db.commit()
    
    AuditChain.record_event(
        db,
        action="CROSS_DOC_CORRELATION_COMPLETED",
        actor="system",
        payload={
            "case_id": case_id,
            "documents_analyzed": len(docs),
            "findings_created": len(findings_created)
        }
    )
    return findings_created
