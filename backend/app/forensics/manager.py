import os
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any
import cv2
from PIL import Image
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.database import DocumentModel, DocumentPageModel, FindingModel, EvidenceModel
from ..models.schemas import BoundingBox, FindingCategory, RiskLevel, ReviewStatus
from ..audit.hash_chain import AuditChain
from .ela import detect_ela_anomalies
from .noise import analyze_noise_residual
from .copymove import detect_copy_move
from .fonts import analyze_text_fonts_and_alignment
from .background import detect_background_discontinuity
from .metadata import analyze_metadata
from .signature import extract_signature_regions, check_pasted_signature_edges

def run_document_forensics(
    doc: DocumentModel,
    db: Session
) -> List[FindingModel]:
    """
    Executes complete visual and digital forensics suite for all pages of a document.
    Generates annotated overlays, cropped evidence images, and records findings in DB.
    """
    findings_created = []
    
    # 1. Digital Metadata Analysis (on original file)
    orig_path = settings.STORAGE_DIR / f"{doc.document_id}_orig.{doc.filename.split('.')[-1]}"
    if os.path.exists(orig_path):
        meta_results = analyze_metadata(str(orig_path))
        for m in meta_results:
            ev_id = f"ev_{uuid.uuid4().hex[:10]}"
            f_id = f"fnd_{uuid.uuid4().hex[:10]}"
            
            # Evidence
            ev = EvidenceModel(
                evidence_id=ev_id,
                case_id=doc.case_id,
                document_id=doc.document_id,
                page=1,
                detector=m["detector"],
                bbox_json=json.dumps({"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}),
                crop_path="",
                overlay_path="",
                score=m["score"],
                status=m["category"],
                observation=m["observation"]
            )
            db.add(ev)
            
            f_model = FindingModel(
                finding_id=f_id,
                case_id=doc.case_id,
                document_id=doc.document_id,
                page=1,
                title="Metadata Tooling Trace" if m["category"] == "POTENTIAL_MANIPULATION" else "Document Metadata Signature",
                category=m["category"],
                risk_level="HIGH" if m["category"] == "POTENTIAL_MANIPULATION" else "LOW",
                confidence=m["score"],
                detector=m["detector"],
                observation=m["observation"],
                technical_details=m["technical_details"],
                suspicious_view="Metadata signatures contain references to interactive design/editing software rather than direct print/scan capture pipelines.",
                innocent_view="Document may have been combined, rotated, or converted for convenience using desktop publishing or PDF software before submission.",
                corroboration_count=1,
                formula_breakdown=f"Detector confidence: {m['score']:.2f}. Baseline weight: 1.0.",
                recommended_verification="Request raw digital statement generated directly from bank portal or verify with issuing institution.",
                bbox_json=json.dumps({"page": 1, "x": 0, "y": 0, "w": 100, "h": 100}),
                evidence_id=ev_id,
                status="PENDING"
            )
            db.add(f_model)
            findings_created.append(f_model)

    # 2. Page-level Image Forensics
    pages = db.query(DocumentPageModel).filter(DocumentPageModel.document_id == doc.document_id).order_by(DocumentPageModel.page_number).all()
    
    for page in pages:
        p_num = page.page_number
        p_path = page.image_path
        if not os.path.exists(p_path):
            continue
            
        cv_img = cv2.imread(p_path)
        if cv_img is None:
            continue
        ph, pw, _ = cv_img.shape
        
        # Detector overlays
        ela_overlay = str(settings.EVIDENCE_DIR / f"{doc.document_id}_p{p_num}_ela.png")
        noise_overlay = str(settings.EVIDENCE_DIR / f"{doc.document_id}_p{p_num}_noise.png")
        copymove_overlay = str(settings.EVIDENCE_DIR / f"{doc.document_id}_p{p_num}_copymove.png")
        fonts_overlay = str(settings.EVIDENCE_DIR / f"{doc.document_id}_p{p_num}_fonts.png")
        bg_overlay = str(settings.EVIDENCE_DIR / f"{doc.document_id}_p{p_num}_bg.png")
        
        # Run individual detectors
        all_detections = []
        all_detections.extend(detect_ela_anomalies(p_path, output_overlay_path=ela_overlay))
        all_detections.extend(analyze_noise_residual(p_path, output_overlay_path=noise_overlay))
        all_detections.extend(detect_copy_move(p_path, output_overlay_path=copymove_overlay))
        all_detections.extend(analyze_text_fonts_and_alignment(p_path, output_overlay_path=fonts_overlay))
        all_detections.extend(detect_background_discontinuity(p_path, output_overlay_path=bg_overlay))
        
        # Signature specific analysis
        sig_regions = extract_signature_regions(p_path)
        for s in sig_regions:
            is_pasted, p_score, p_obs = check_pasted_signature_edges(s["crop"])
            if is_pasted:
                all_detections.append({
                    "detector": "pasted_signature_edge_analysis",
                    "bbox": s["bbox"],
                    "score": p_score,
                    "category": "POTENTIAL_MANIPULATION",
                    "observation": p_obs,
                    "technical_details": "Signature perimeter boundary inspection. Detected rectangular clipping gradient and luminance step."
                })
                
        # Process and record each detection
        for det in all_detections:
            bx, by, bw, bh = det["bbox"]
            ev_id = f"ev_{uuid.uuid4().hex[:10]}"
            f_id = f"fnd_{uuid.uuid4().hex[:10]}"
            
            # Crop evidence image with padding
            pad = 12
            cx1 = max(0, bx - pad)
            cy1 = max(0, by - pad)
            cx2 = min(pw, bx + bw + pad)
            cy2 = min(ph, by + bh + pad)
            crop_np = cv_img[cy1:cy2, cx1:cx2]
            
            crop_filename = f"{doc.document_id}_p{p_num}_{ev_id}_crop.png"
            crop_path = settings.EVIDENCE_DIR / crop_filename
            if crop_np.size > 0:
                cv2.imwrite(str(crop_path), crop_np)
                
            # Pick best overlay path for this detector
            active_overlay = ela_overlay if "ela" in det["detector"] else (
                copymove_overlay if "copy_move" in det["detector"] else (
                    fonts_overlay if "font" in det["detector"] else bg_overlay
                )
            )
            
            bbox_dict = {
                "page": p_num,
                "x": round(float(bx), 1),
                "y": round(float(by), 1),
                "w": round(float(bw), 1),
                "h": round(float(bh), 1),
                "normalized_x": round(float(bx) / pw, 4),
                "normalized_y": round(float(by) / ph, 4),
                "normalized_w": round(float(bw) / pw, 4),
                "normalized_h": round(float(bh) / ph, 4),
            }
            
            # Create Evidence record
            ev = EvidenceModel(
                evidence_id=ev_id,
                case_id=doc.case_id,
                document_id=doc.document_id,
                page=p_num,
                detector=det["detector"],
                bbox_json=json.dumps(bbox_dict),
                crop_path=str(crop_path),
                overlay_path=str(active_overlay),
                score=det["score"],
                status=det["category"],
                observation=det["observation"]
            )
            db.add(ev)
            
            # Category & Risk
            category = det["category"]
            risk = "HIGH" if category == "POTENTIAL_MANIPULATION" and det["score"] > 0.70 else (
                "MEDIUM" if category == "POTENTIAL_MANIPULATION" else "LOW"
            )
            
            # Dual view templates
            if "font" in det["detector"]:
                title = "Font & Baseline Outlier Detected"
                suspicious = "Character/digit differs in font height, weight, and baseline from adjacent text on the same line, consistent with spliced numerical alteration."
                innocent = "Different font or sizing could originate from template formatting, form fill alignment, or dynamic typesetting engine styles."
                rec = "Inspect original digital file or verify specific financial line item against employer payroll register."
            elif "copy_move" in det["detector"]:
                title = "Cloned Graphic / Stamp Pattern"
                suspicious = "Multiple matching keypoints with identical spatial displacement indicate a duplicated or transplanted seal/stamp."
                innocent = "Official forms occasionally print repetitive graphic markers, repetitive company watermarks, or boilerplate security icons."
                rec = "Examine physical impression of notary seal/embossment or request verification from notary registry."
            elif "background" in det["detector"]:
                title = "Background Luminance / Whitening Discontinuity"
                suspicious = "Rectangular region exhibits distinct luminance transition and texture suppression characteristic of whitening or pasted overlay."
                innocent = "Document scanner sensor calibration variation, table cell fill styling, or JPEG block boundary artifacts."
                rec = "Request direct e-statement download from banking institution or inspect physical document paper."
            elif "signature" in det["detector"]:
                title = "Signature Boundary Discontinuity"
                suspicious = "Signature stroke area bounded by artificial rectangular perimeter and background delta, consistent with pasted signature."
                innocent = "Signer may have uploaded a digital signature image into an electronic PDF form field."
                rec = "Verify signature in-person with biometric attendance or original handwritten card."
            else:
                title = "Compression / Sensor Noise Anomaly"
                suspicious = "Localized error/noise rate deviates significantly from document average, indicating differential compression history."
                innocent = "Uneven lighting, scanning glass dust, or multi-generation JPEG re-compression."
                rec = "Acquire higher resolution direct scan."
                
            f_model = FindingModel(
                finding_id=f_id,
                case_id=doc.case_id,
                document_id=doc.document_id,
                page=p_num,
                title=title,
                category=category,
                risk_level=risk,
                confidence=det["score"],
                detector=det["detector"],
                observation=det["observation"],
                technical_details=det["technical_details"],
                suspicious_view=suspicious,
                innocent_view=innocent,
                corroboration_count=1,
                formula_breakdown=f"Detector: {det['detector']}, raw score={det['score']:.2f}, category={category}.",
                recommended_verification=rec,
                bbox_json=json.dumps(bbox_dict),
                evidence_id=ev_id,
                status="PENDING"
            )
            db.add(f_model)
            findings_created.append(f_model)
            
    db.commit()
    
    # Audit log
    AuditChain.record_event(
        db,
        action="VISUAL_FORENSICS_COMPLETED",
        actor="system",
        payload={
            "document_id": doc.document_id,
            "findings_count": len(findings_created),
            "potential_manipulations": sum(1 for f in findings_created if f.category == "POTENTIAL_MANIPULATION")
        }
    )
    return findings_created
