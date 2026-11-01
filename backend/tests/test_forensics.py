import os
import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.forensics.ela import detect_ela_anomalies
from backend.app.forensics.copymove import detect_copy_move
from backend.app.forensics.fonts import analyze_text_fonts_and_alignment
from backend.app.forensics.background import detect_background_discontinuity
from backend.app.forensics.metadata import analyze_metadata

TAMPERED_DIR = settings.DATA_DIR / "demo_case_tampered"
GENUINE_DIR = settings.DATA_DIR / "demo_case_genuine"

def test_metadata_detector():
    tampered_decl = TAMPERED_DIR / "declaration.pdf"
    findings = analyze_metadata(str(tampered_decl))
    assert len(findings) > 0
    # Must flag Adobe Acrobat Pro / Canva
    manipulations = [f for f in findings if f["category"] == "POTENTIAL_MANIPULATION"]
    assert len(manipulations) >= 1
    assert "Canva" in manipulations[0]["observation"] or "Adobe" in manipulations[0]["observation"]

def test_font_outlier_detector():
    tampered_salary = TAMPERED_DIR / "salary_slip.png"
    findings = analyze_text_fonts_and_alignment(str(tampered_salary))
    assert len(findings) > 0
    font_anomalies = [f for f in findings if f["category"] == "POTENTIAL_MANIPULATION"]
    assert len(font_anomalies) >= 1
    assert any("height" in f["observation"].lower() for f in font_anomalies)

def test_background_discontinuity_detector():
    # Convert first page of bank statement to image to test background detector
    import pymupdf
    pdf_path = str(TAMPERED_DIR / "bank_statement.pdf")
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    test_img = str(settings.DATA_DIR / "test_bank_p1.png")
    pix.save(test_img)
    doc.close()
    
    findings = detect_background_discontinuity(test_img)
    assert len(findings) >= 1
    assert any("whitening" in f["observation"].lower() or "luminance" in f["observation"].lower() for f in findings)
    if os.path.exists(test_img):
        os.remove(test_img)

def test_copy_move_detector():
    import pymupdf
    pdf_path = str(TAMPERED_DIR / "declaration.pdf")
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    test_img = str(settings.DATA_DIR / "test_decl_p1.png")
    pix.save(test_img)
    doc.close()
    
    findings = detect_copy_move(test_img)
    assert len(findings) >= 1
    assert any("cloned" in f["observation"].lower() or "copy-move" in f["detector"].lower() for f in findings)
    if os.path.exists(test_img):
        os.remove(test_img)
