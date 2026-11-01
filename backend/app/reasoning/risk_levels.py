from typing import Tuple
from ..models.schemas import RiskLevel, FindingCategory

def compute_explainable_risk(
    detector_score: float,
    category: FindingCategory,
    corroboration_count: int = 1,
    ocr_agreement: float = 1.0
) -> Tuple[RiskLevel, float, str]:
    """
    Computes explainable, deterministic risk scoring with mathematical transparency.
    Weights:
    - 45% detector confidence score
    - 25% multi-signal corroboration count (up to 3 independent signals)
    - 20% category severity weight (POTENTIAL_MANIPULATION=1.0, INCONSISTENT=0.6, OBSERVED=0.2)
    - 10% OCR divergence penalty
    Returns (RiskLevel, numeric_score_0_to_1, formula_breakdown_string).
    """
    cat_weights = {
        FindingCategory.POTENTIAL_MANIPULATION: 1.0,
        FindingCategory.INCONSISTENT: 0.6,
        FindingCategory.OBSERVED: 0.2
    }
    w_cat = cat_weights.get(category, 0.3)
    w_corrob = min(1.0, corroboration_count / 3.0)
    w_ocr_div = max(0.0, 1.0 - ocr_agreement)
    
    score = (
        0.45 * detector_score +
        0.25 * w_corrob +
        0.20 * w_cat +
        0.10 * w_ocr_div
    )
    score = round(min(0.99, max(0.05, score)), 2)
    
    if score >= 0.68 or category == FindingCategory.POTENTIAL_MANIPULATION:
        risk = RiskLevel.HIGH
    elif score >= 0.40 or category == FindingCategory.INCONSISTENT:
        risk = RiskLevel.MEDIUM
    else:
        risk = RiskLevel.LOW
        
    formula = (
        f"Score {score:.2f} = 0.45*({detector_score:.2f}) + 0.25*({w_corrob:.2f} corrob) + "
        f"0.20*({w_cat:.1f} severity) + 0.10*({w_ocr_div:.2f} ocr_div) -> Risk: {risk.value}"
    )
    return risk, score, formula

def aggregate_case_risk(findings_risk_list: list) -> RiskLevel:
    """
    Computes overall case-level risk ladder based on highest detected anomaly and count.
    """
    if any(r == RiskLevel.HIGH or r == "HIGH" for r in findings_risk_list):
        return RiskLevel.HIGH
    elif any(r == RiskLevel.MEDIUM or r == "MEDIUM" for r in findings_risk_list):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
