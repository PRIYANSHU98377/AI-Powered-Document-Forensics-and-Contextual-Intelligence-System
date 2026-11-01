import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from ..core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CaseModel(Base):
    __tablename__ = "cases"
    
    case_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="open")
    overall_risk = Column(String(32), default="LOW")
    
    documents = relationship("DocumentModel", back_populates="case", cascade="all, delete-orphan")
    findings = relationship("FindingModel", back_populates="case", cascade="all, delete-orphan")

class DocumentModel(Base):
    __tablename__ = "documents"
    
    document_id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(64), default="")
    sha256_hash = Column(String(64), nullable=False)
    doc_type = Column(String(64), default="other")
    doc_type_confidence = Column(Float, default=0.0)
    classification_reasons = Column(Text, default="[]")  # JSON list
    page_count = Column(Integer, default=1)
    status = Column(String(32), default="pending")
    status_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="documents")
    fields = relationship("ExtractedFieldModel", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("DocumentPageModel", back_populates="document", cascade="all, delete-orphan")

class DocumentPageModel(Base):
    __tablename__ = "document_pages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(64), ForeignKey("documents.document_id"), nullable=False, index=True)
    page_number = Column(Integer, default=1)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    image_path = Column(String(512), default="")
    
    document = relationship("DocumentModel", back_populates="pages")

class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(String(64), unique=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.document_id"), nullable=False, index=True)
    page = Column(Integer, default=1)
    name = Column(String(128), nullable=False)
    label = Column(String(128), default="")
    value = Column(Text, default="")
    raw_value = Column(Text, default="")
    confidence = Column(Float, default=1.0)
    ocr_agreement = Column(Float, default=1.0)
    reliability = Column(String(32), default="high")
    bbox_json = Column(Text, default="")  # JSON dict
    data_type = Column(String(32), default="string")
    raw_candidates_json = Column(Text, default="[]")  # JSON list
    
    document = relationship("DocumentModel", back_populates="fields")

class FindingModel(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(64), unique=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    document_id = Column(String(64), nullable=False, index=True)
    page = Column(Integer, default=1)
    title = Column(String(255), nullable=False)
    category = Column(String(64), default="OBSERVED")
    risk_level = Column(String(32), default="LOW")
    confidence = Column(Float, default=0.5)
    detector = Column(String(64), default="")
    observation = Column(Text, default="")
    technical_details = Column(Text, default="")
    suspicious_view = Column(Text, default="")
    innocent_view = Column(Text, default="")
    corroboration_count = Column(Integer, default=1)
    formula_breakdown = Column(Text, default="")
    recommended_verification = Column(Text, default="")
    bbox_json = Column(Text, default="")
    evidence_id = Column(String(64), default="")
    status = Column(String(32), default="PENDING")
    reviewer_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="findings")

class EvidenceModel(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, index=True)
    case_id = Column(String(64), nullable=False, index=True)
    document_id = Column(String(64), nullable=False, index=True)
    page = Column(Integer, default=1)
    detector = Column(String(64), default="")
    bbox_json = Column(Text, default="")
    crop_path = Column(String(512), default="")
    overlay_path = Column(String(512), default="")
    score = Column(Float, default=0.0)
    status = Column(String(64), default="OBSERVED")
    observation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditEventModel(Base):
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True)
    timestamp = Column(String(64), nullable=False)
    actor = Column(String(128), default="system")
    action = Column(String(128), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)
    details_json = Column(Text, default="{}")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
