import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .models.database import init_db
from .api import cases, documents, findings, evidence, graph, dossier, audit

# Initialize database
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Document Forensics and Contextual Intelligence System"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router
app.include_router(cases.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(findings.router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence.router, prefix=settings.API_V1_PREFIX)
app.include_router(graph.router, prefix=settings.API_V1_PREFIX)
app.include_router(dossier.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)

# Static file serving for evidence and rendered images
if os.path.exists(settings.STORAGE_DIR):
    app.mount("/static/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")
if os.path.exists(settings.EVIDENCE_DIR):
    app.mount("/static/evidence", StaticFiles(directory=str(settings.EVIDENCE_DIR)), name="evidence")
if os.path.exists(settings.DATA_DIR):
    app.mount("/static/demo", StaticFiles(directory=str(settings.DATA_DIR)), name="demo")

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "online",
        "endpoints": {
            "cases": f"{settings.API_V1_PREFIX}/cases",
            "audit_verify": f"{settings.API_V1_PREFIX}/audit/verify",
            "docs": "/docs"
        },
        "disclaimer": "Automated findings are indicators for human review, not conclusions of fraud."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
