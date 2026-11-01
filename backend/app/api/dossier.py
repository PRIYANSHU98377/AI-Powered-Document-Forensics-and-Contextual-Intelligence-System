import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.database import get_db, CaseModel
from ..dossier.builder import export_dossier_html, export_dossier_json, export_dossier_pdf
from ..audit.hash_chain import AuditChain

router = APIRouter(tags=["dossier"])

@router.get("/cases/{case_id}/dossier/html", response_class=HTMLResponse)
def view_dossier_html(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    html = export_dossier_html(case_id, db)
    return HTMLResponse(content=html)

@router.get("/cases/{case_id}/dossier/json")
def get_dossier_json(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return export_dossier_json(case_id, db)

@router.get("/cases/{case_id}/dossier/pdf")
def download_dossier_pdf(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    pdf_filename = f"dossier_{case_id}.pdf"
    pdf_path = str(settings.DATA_DIR / pdf_filename)
    export_dossier_pdf(case_id, db, pdf_path)
    
    AuditChain.record_event(
        db,
        action="DOSSIER_EXPORTED",
        actor="investigator",
        payload={"case_id": case_id, "format": "PDF", "file": pdf_filename}
    )
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"DocDetective_Dossier_{case_id}.pdf"
    )
