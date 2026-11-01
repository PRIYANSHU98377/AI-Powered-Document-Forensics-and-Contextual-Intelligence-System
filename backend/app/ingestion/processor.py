import hashlib
import uuid
import os
from pathlib import Path
from typing import Tuple, List
from PIL import Image
import pymupdf  # PyMuPDF
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.security import validate_magic_bytes
from ..models.database import DocumentModel, DocumentPageModel
from ..audit.hash_chain import AuditChain

class IngestionError(Exception):
    pass

def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def ingest_document(
    case_id: str,
    filename: str,
    content: bytes,
    db: Session
) -> Tuple[DocumentModel, List[str]]:
    """
    Ingests and normalizes an uploaded document.
    Validates file integrity, hashes original bytes, renders pages to images,
    and records an immutable audit event.
    Returns (document_record, list_of_page_image_paths).
    """
    # 1. Size check
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise IngestionError(f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE // (1024*1024)}MB)")
        
    # 2. Magic bytes validation
    is_valid, msg = validate_magic_bytes(content, filename)
    if not is_valid:
        raise IngestionError(f"File security rejection: {msg}")
        
    # 3. Hash computation
    sha256_hash = compute_sha256(content)
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # 4. Save original file read-only
    ext = filename.split(".")[-1].lower() if "." in filename else "bin"
    orig_path = settings.STORAGE_DIR / f"{document_id}_orig.{ext}"
    with open(orig_path, "wb") as f:
        f.write(content)
    # Set read-only permissions on original
    try:
        os.chmod(orig_path, 0o444)
    except Exception:
        pass
        
    page_image_paths = []
    page_count = 1
    
    # 5. Process pages into normalized images
    if ext == "pdf":
        try:
            doc_pdf = pymupdf.open(stream=content, filetype="pdf")
            page_count = len(doc_pdf)
            for pno in range(page_count):
                page = doc_pdf[pno]
                # Render to 150 DPI pixmap for crisp visual forensics & web display
                zoom = 150 / 72  # 72 is standard PDF point dpi
                mat = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                page_img_path = settings.STORAGE_DIR / f"{document_id}_p{pno+1}.png"
                pix.save(str(page_img_path))
                page_image_paths.append(str(page_img_path))
            doc_pdf.close()
        except Exception as e:
            raise IngestionError(f"Corrupt or unreadable PDF document: {str(e)}")
    else:
        # Standard image (PNG, JPG, TIFF)
        try:
            import io
            img = Image.open(io.BytesIO(content))
            img = img.convert("RGB")
            page_img_path = settings.STORAGE_DIR / f"{document_id}_p1.png"
            img.save(str(page_img_path), "PNG")
            page_image_paths.append(str(page_img_path))
            page_count = 1
        except Exception as e:
            raise IngestionError(f"Corrupt or unreadable image document: {str(e)}")
            
    # 6. Create database models
    doc_record = DocumentModel(
        document_id=document_id,
        case_id=case_id,
        filename=filename,
        file_size=len(content),
        mime_type=f"application/{ext}" if ext == "pdf" else f"image/{ext}",
        sha256_hash=sha256_hash,
        page_count=page_count,
        status="ingested",
        status_message="Ingestion and page rendering complete"
    )
    db.add(doc_record)
    db.flush()
    
    # Add page records
    for idx, p_path in enumerate(page_image_paths):
        with Image.open(p_path) as im:
            pw, ph = im.size
        p_model = DocumentPageModel(
            document_id=document_id,
            page_number=idx + 1,
            width=float(pw),
            height=float(ph),
            image_path=str(p_path)
        )
        db.add(p_model)
        
    db.commit()
    db.refresh(doc_record)
    
    # 7. Audit event
    AuditChain.record_event(
        db,
        action="DOCUMENT_INGESTED",
        actor="system",
        payload={
            "document_id": document_id,
            "case_id": case_id,
            "filename": filename,
            "sha256_hash": sha256_hash,
            "page_count": page_count,
            "file_size": len(content)
        }
    )
    
    return doc_record, page_image_paths
