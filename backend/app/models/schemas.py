from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class FindingCategory(str, Enum):
    OBSERVED = "OBSERVED"
    INCONSISTENT = "INCONSISTENT"
    POTENTIAL_MANIPULATION = "POTENTIAL_MANIPULATION"

class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    NEEDS_INFO = "NEEDS_INFO"

class DocumentType(str, Enum):
    ID_CARD = "id_card"
    APPLICATION_FORM = "application_form"
    BANK_STATEMENT = "bank_statement"
    SALARY_SLIP = "salary_slip"
    UTILITY_BILL = "utility_bill"
    DECLARATION = "declaration"
    OTHER = "other"

class BoundingBox(BaseModel):
    page: int = 1
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    normalized_x: float = 0.0
    normalized_y: float = 0.0
    normalized_w: float = 0.0
    normalized_h: float = 0.0

class WordCandidate(BaseModel):
    text: str
    confidence: float
    engine: str

class ExtractedWord(BaseModel):
    text: str
    bbox: BoundingBox
    confidence: float
    ocr_agreement: float = 1.0
    raw_candidates: List[WordCandidate] = []
    reliability: str = "high"

class ExtractedField(BaseModel):
    field_id: str
    document_id: str
    page: int = 1
    name: str
    label: str
    value: str
    raw_value: str
    confidence: float = 0.95
    ocr_agreement: float = 1.0
    reliability: str = "high"
    bbox: Optional[BoundingBox] = None
    data_type: str = "string"
    raw_candidates: List[str] = []

class EvidenceItem(BaseModel):
    evidence_id: str
    case_id: str
    document_id: str
    page: int = 1
    detector: str
    bbox: Optional[BoundingBox] = None
    crop_path: Optional[str] = None
    overlay_path: Optional[str] = None
    score: float = 0.0
    status: FindingCategory = FindingCategory.OBSERVED
    observation: str = ""
    created_at: str = ""

class Finding(BaseModel):
    finding_id: str
    case_id: str
    document_id: str
    page: int = 1
    title: str
    category: FindingCategory
    risk_level: RiskLevel
    confidence: float
    detector: str
    observation: str
    technical_details: str
    suspicious_view: str
    innocent_view: str
    corroboration_count: int = 1
    formula_breakdown: str
    recommended_verification: str
    bbox: Optional[BoundingBox] = None
    evidence_id: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str = ""
    created_at: str = ""

class DocumentInfo(BaseModel):
    document_id: str
    case_id: str
    filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    doc_type: str = "other"
    doc_type_confidence: float = 0.0
    classification_reasons: List[str] = []
    page_count: int = 1
    status: str = "pending"  # uploaded, processing, completed, failed
    status_message: str = ""
    created_at: str = ""

class CaseInfo(BaseModel):
    case_id: str
    name: str
    description: str = ""
    created_at: str = ""
    status: str = "open"
    overall_risk: RiskLevel = RiskLevel.LOW
    documents: List[DocumentInfo] = []
    findings_count: int = 0

class AuditEvent(BaseModel):
    event_id: str
    timestamp: str
    actor: str
    action: str
    payload_hash: str
    prev_hash: str
    entry_hash: str
    details: Dict[str, Any] = {}

class RelationshipNode(BaseModel):
    id: str
    label: str
    type: str  # document, person, address, account, id_number, employer
    doc_id: Optional[str] = None
    properties: Dict[str, Any] = {}

class RelationshipEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # exact_match, tolerated_variation, conflict
    status: str  # green, amber, red
    details: str
    evidence_id: Optional[str] = None

class RelationshipGraph(BaseModel):
    nodes: List[RelationshipNode]
    edges: List[RelationshipEdge]

class ReviewUpdate(BaseModel):
    status: ReviewStatus
    reviewer_notes: str = ""
