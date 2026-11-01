from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.database import get_db, CaseModel
from ..correlation.graph_builder import build_relationship_graph

router = APIRouter(tags=["graph"])

@router.get("/cases/{case_id}/graph")
def get_case_relationship_graph(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return build_relationship_graph(case_id, db)
