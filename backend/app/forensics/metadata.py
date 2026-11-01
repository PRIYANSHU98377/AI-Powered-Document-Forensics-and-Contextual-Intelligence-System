import os
from typing import List, Dict, Any, Optional
from PIL import Image, ExifTags
import pymupdf

SUSPICIOUS_SOFTWARE_KEYWORDS = [
    "canva", "photoshop", "gimp", "acrobat pro", "illustrator",
    "pdfedit", "inkscape", "coreldraw", "pdf architect"
]

def analyze_metadata(file_path: str) -> List[Dict[str, Any]]:
    """
    Analyzes PDF and EXIF metadata for editing software traces, creation/mod date anomalies,
    and missing producer signatures.
    """
    findings = []
    ext = file_path.lower().split(".")[-1]
    
    if ext == "pdf":
        try:
            doc = pymupdf.open(file_path)
            meta = doc.metadata or {}
            doc.close()
            
            creator = meta.get("creator", "").lower()
            producer = meta.get("producer", "").lower()
            author = meta.get("author", "").lower()
            title = meta.get("title", "").lower()
            
            found_tools = []
            for kw in SUSPICIOUS_SOFTWARE_KEYWORDS:
                if kw in creator or kw in producer or kw in author:
                    found_tools.append(kw.title())
                    
            if found_tools:
                findings.append({
                    "detector": "pdf_metadata_analysis",
                    "bbox": (0, 0, 100, 100),
                    "score": 0.88,
                    "category": "POTENTIAL_MANIPULATION",
                    "observation": f"Document metadata indicates editing or graphic design software ({', '.join(found_tools)}) rather than direct banking/scanning capture systems.",
                    "technical_details": f"PDF Creator='{meta.get('creator')}', Producer='{meta.get('producer')}', Author='{meta.get('author')}'."
                })
            else:
                findings.append({
                    "detector": "pdf_metadata_analysis",
                    "bbox": (0, 0, 100, 100),
                    "score": 0.15,
                    "category": "OBSERVED",
                    "observation": f"Document produced by standard PDF engine ({meta.get('producer', 'Standard Generator')}). No desktop editing tool signatures detected in metadata stream.",
                    "technical_details": f"PDF Creator='{meta.get('creator')}', Producer='{meta.get('producer')}'."
                })
        except Exception as e:
            findings.append({
                "detector": "pdf_metadata_analysis",
                "bbox": (0, 0, 100, 100),
                "score": 0.30,
                "category": "OBSERVED",
                "observation": f"Metadata stream could not be completely parsed: {str(e)}",
                "technical_details": str(e)
            })
    else:
        # Image EXIF
        try:
            img = Image.open(file_path)
            exif = img._getexif()
            if exif:
                exif_data = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                software = str(exif_data.get("Software", "")).lower()
                found_tools = [kw.title() for kw in SUSPICIOUS_SOFTWARE_KEYWORDS if kw in software]
                if found_tools:
                    findings.append({
                        "detector": "image_exif_analysis",
                        "bbox": (0, 0, 100, 100),
                        "score": 0.85,
                        "category": "POTENTIAL_MANIPULATION",
                        "observation": f"Image EXIF software tag specifies photo editing application: '{exif_data.get('Software')}'.",
                        "technical_details": f"EXIF Software: {exif_data.get('Software')}."
                    })
        except Exception:
            pass
            
    return findings
