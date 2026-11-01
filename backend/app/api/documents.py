import os
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..models.database import get_db, CaseModel, DocumentModel, DocumentPageModel, ExtractedFieldModel
from ..ingestion.processor import ingest_document, IngestionError

router = APIRouter(tags=["documents"])

@router.post("/cases/{case_id}/documents")
async def upload_documents(
    case_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    uploaded = []
    errors = []
    
    for f in files:
        try:
            content = await f.read()
            doc_rec, page_paths = ingest_document(
                case_id=case_id,
                filename=f.filename,
                content=content,
                db=db
            )
            uploaded.append({
                "document_id": doc_rec.document_id,
                "filename": doc_rec.filename,
                "file_size": doc_rec.file_size,
                "sha256": doc_rec.sha256_hash,
                "page_count": doc_rec.page_count,
                "status": doc_rec.status
            })
        except IngestionError as ie:
            errors.append({"filename": f.filename, "error": str(ie)})
        except Exception as e:
            errors.append({"filename": f.filename, "error": f"Unexpected processing error: {str(e)}"})
            
    return {
        "case_id": case_id,
        "uploaded_count": len(uploaded),
        "uploaded": uploaded,
        "errors": errors
    }

@router.get("/cases/{case_id}/documents")
def list_case_documents(case_id: str, db: Session = Depends(get_db)):
    docs = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    results = []
    for d in docs:
        results.append({
            "document_id": d.document_id,
            "filename": d.filename,
            "file_size": d.file_size,
            "mime_type": d.mime_type,
            "sha256_hash": d.sha256_hash,
            "doc_type": d.doc_type,
            "doc_type_confidence": d.doc_type_confidence,
            "classification_reasons": json.loads(d.classification_reasons or "[]"),
            "page_count": d.page_count,
            "status": d.status
        })
    return results

@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    d = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
        
    pages = db.query(DocumentPageModel).filter(DocumentPageModel.document_id == document_id).all()
    return {
        "document_id": d.document_id,
        "case_id": d.case_id,
        "filename": d.filename,
        "file_size": d.file_size,
        "mime_type": d.mime_type,
        "sha256_hash": d.sha256_hash,
        "doc_type": d.doc_type,
        "doc_type_confidence": d.doc_type_confidence,
        "classification_reasons": json.loads(d.classification_reasons or "[]"),
        "page_count": d.page_count,
        "status": d.status,
        "pages": [
            {"page_number": p.page_number, "width": p.width, "height": p.height}
            for p in pages
        ]
    }

@router.get("/documents/{document_id}/fields")
def get_document_fields(document_id: str, db: Session = Depends(get_db)):
    fields = db.query(ExtractedFieldModel).filter(ExtractedFieldModel.document_id == document_id).all()
    results = []
    for f in fields:
        results.append({
            "field_id": f.field_id,
            "name": f.name,
            "label": f.label,
            "value": f.value,
            "raw_value": f.raw_value,
            "confidence": f.confidence,
            "ocr_agreement": f.ocr_agreement,
            "reliability": f.reliability,
            "page": f.page,
            "bbox": json.loads(f.bbox_json) if f.bbox_json else None,
            "data_type": f.data_type
        })
    return results

@router.get("/documents/{document_id}/pages/{page_num}/image")
def get_page_image(document_id: str, page_num: int, db: Session = Depends(get_db)):
    page = db.query(DocumentPageModel).filter(
        DocumentPageModel.document_id == document_id,
        DocumentPageModel.page_number == page_num
    ).first()
    if not page or not os.path.exists(page.image_path):
        raise HTTPException(status_code=404, detail="Page image not found")
    return FileResponse(page.image_path, media_type="image/png")
