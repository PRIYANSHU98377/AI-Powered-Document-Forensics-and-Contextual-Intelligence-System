from typing import List
from sqlalchemy.orm import Session
from ..models.database import FindingModel
from ..models.schemas import FindingCategory
from .risk_levels import compute_explainable_risk
from .llm_provider import generate_reasoning_explanation

def enrich_findings_with_dual_view(
    findings: List[FindingModel],
    db: Session
) -> List[FindingModel]:
    """
    Applies Dual-View Reasoning and explainable risk scoring to each finding.
    """
    for f in findings:
        cat_enum = FindingCategory(f.category) if f.category in [c.value for c in FindingCategory] else FindingCategory.OBSERVED
        
        # 1. Compute explainable risk & breakdown formula
        risk, score, formula = compute_explainable_risk(
            detector_score=f.confidence,
            category=cat_enum,
            corroboration_count=f.corroboration_count,
            ocr_agreement=1.0
        )
        f.risk_level = risk.value
        f.confidence = score
        f.formula_breakdown = formula
        
        # 2. Generate dual view (templates / LLM)
        views = generate_reasoning_explanation(
            detector_name=f.detector,
            observation=f.observation,
            evidence_id=f.evidence_id
        )
        f.suspicious_view = views["suspicious"]
        f.innocent_view = views["innocent"]
        f.recommended_verification = views["rec"]
        
    db.commit()
    return findings
