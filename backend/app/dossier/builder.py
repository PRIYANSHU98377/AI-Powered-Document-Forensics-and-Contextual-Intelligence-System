import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from ..core.config import settings
from ..models.database import CaseModel, DocumentModel, ExtractedFieldModel, FindingModel, EvidenceModel
from ..audit.verify import verify_audit_chain
from ..correlation.graph_builder import build_relationship_graph

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

def build_dossier_data(case_id: str, db: Session) -> Dict[str, Any]:
    case = db.query(CaseModel).filter(CaseModel.case_id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")
        
    docs = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    fields = db.query(ExtractedFieldModel).join(DocumentModel).filter(DocumentModel.case_id == case_id).all()
    findings = db.query(FindingModel).filter(FindingModel.case_id == case_id).all()
    evidence_items = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id).all()
    
    fields_by_doc = {}
    for f in fields:
        fields_by_doc.setdefault(f.document_id, []).append(f)
        
    audit_status = verify_audit_chain(db)
    
    # Generate graph PNG
    graph_img_path = str(settings.EVIDENCE_DIR / f"{case_id}_relationship_graph.png")
    build_relationship_graph(case_id, db, save_png_path=graph_img_path)
    
    return {
        "case": case,
        "documents": docs,
        "fields_by_doc": fields_by_doc,
        "findings": findings,
        "evidence_items": evidence_items,
        "audit_status": audit_status,
        "graph_image_path": graph_img_path if os.path.exists(graph_img_path) else None,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }

def export_dossier_html(case_id: str, db: Session) -> str:
    data = build_dossier_data(case_id, db)
    template = jinja_env.get_template("dossier.html.j2")
    return template.render(**data)

def export_dossier_json(case_id: str, db: Session) -> Dict[str, Any]:
    data = build_dossier_data(case_id, db)
    return {
        "case_id": data["case"].case_id,
        "name": data["case"].name,
        "overall_risk": data["case"].overall_risk,
        "generated_at": data["generated_at"],
        "documents": [
            {
                "document_id": d.document_id,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "confidence": d.doc_type_confidence,
                "file_size": d.file_size,
                "sha256": d.sha256_hash,
                "status": d.status
            }
            for d in data["documents"]
        ],
        "findings": [
            {
                "finding_id": f.finding_id,
                "document_id": f.document_id,
                "title": f.title,
                "category": f.category,
                "risk_level": f.risk_level,
                "confidence": f.confidence,
                "detector": f.detector,
                "observation": f.observation,
                "suspicious_view": f.suspicious_view,
                "innocent_view": f.innocent_view,
                "recommended_verification": f.recommended_verification,
                "formula_breakdown": f.formula_breakdown,
                "status": f.status,
                "reviewer_notes": f.reviewer_notes
            }
            for f in data["findings"]
        ],
        "audit_verification": data["audit_status"]
    }

def export_dossier_pdf(case_id: str, db: Session, output_path: str) -> str:
    """
    Renders professional multi-page PDF Dossier containing all required sections 7.1-7.6.
    Uses pure-Python ReportLab for 100% portable, reliable rendering.
    """
    data = build_dossier_data(case_id, db)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A")
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        "DocDisc",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )
    code_style = ParagraphStyle(
        "DocCode",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Courier",
        textColor=colors.HexColor("#0F172A")
    )
    
    elements = []
    
    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>DocDetective | Investigation Dossier</b><br/><font size=8 color='#64748B'>AI-Powered Forensic Intelligence & Contextual Audit</font>", title_style),
            Paragraph(f"<b>Case:</b> {data['case'].case_id}<br/><b>Risk:</b> <font color='{'#DC2626' if data['case'].overall_risk == 'HIGH' else '#16A34A'}'><b>{data['case'].overall_risk}</b></font><br/><b>Date:</b> {data['generated_at'][:10]}", body_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[360, 180])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor("#1E3A8A")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 10))
    
    # Mandatory Disclaimer Box
    disc_text = (
        "<b>MANDATORY FORENSIC PRINCIPLE & DISCLAIMER:</b><br/>"
        "Automated findings produced by DocDetective are objective indicators for human review, NOT definitive "
        "conclusions of fraud. OCR output is never treated as absolute ground truth. Every finding must be "
        "independently verified following institutional policy and standard digital evidence protocols (ISO/IEC 27037)."
    )
    disc_table = Table([[Paragraph(disc_text, disclaimer_style)]], colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(disc_table)
    elements.append(Spacer(1, 10))
    
    # 7.1 Document Overview
    elements.append(Paragraph("7.1 Document Overview", h2_style))
    doc_rows = [["Document ID", "Filename", "Doc Type", "Size (KB)", "SHA-256 Digest", "Status"]]
    for d in data["documents"]:
        doc_rows.append([
            Paragraph(d.document_id, code_style),
            Paragraph(f"<b>{d.filename}</b>", body_style),
            Paragraph(d.doc_type, body_style),
            Paragraph(f"{round(d.file_size / 1024, 1)}", body_style),
            Paragraph(d.sha256_hash[:18] + "...", code_style),
            Paragraph(d.status, body_style)
        ])
    t_docs = Table(doc_rows, colWidths=[80, 110, 85, 55, 130, 80])
    t_docs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_docs)
    elements.append(Spacer(1, 10))
    
    # 7.2 Extracted Information
    elements.append(Paragraph("7.2 Extracted Information & Structure", h2_style))
    fld_rows = [["Document", "Field Name", "Extracted Value", "Reliability", "Conf"]]
    for doc_rec in data["documents"]:
        doc_flds = data["fields_by_doc"].get(doc_rec.document_id, [])
        for fld in doc_flds[:6]:  # sample representative fields per doc
            fld_rows.append([
                Paragraph(doc_rec.filename, body_style),
                Paragraph(fld.label or fld.name, body_style),
                Paragraph(fld.value[:35] + ("..." if len(fld.value) > 35 else ""), body_style),
                Paragraph(f"{fld.reliability.upper()} (Agr: {int(fld.ocr_agreement*100)}%)", body_style),
                Paragraph(f"{int(fld.confidence * 100)}%", body_style)
            ])
    t_flds = Table(fld_rows, colWidths=[110, 100, 180, 100, 50])
    t_flds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_flds)
    elements.append(Spacer(1, 10))
    
    # 7.3 Contextual Analysis
    elements.append(Paragraph("7.3 Contextual Analysis & Cross-Document Correlations", h2_style))
    ctx_findings = [f for f in data["findings"] if f.category in ["INCONSISTENT", "POTENTIAL_MANIPULATION"]]
    if ctx_findings:
        ctx_rows = [["Severity", "Finding Title", "Contextual Observation"]]
        for f in ctx_findings:
            ctx_rows.append([
                Paragraph(f"<b>{f.category}</b><br/>Risk: {f.risk_level}", body_style),
                Paragraph(f"<b>{f.title}</b>", body_style),
                Paragraph(f.observation, body_style)
            ])
        t_ctx = Table(ctx_rows, colWidths=[90, 140, 310])
        t_ctx.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_ctx)
    else:
        elements.append(Paragraph("All intra-document rules and cross-document entity correlations passed with zero conflicts.", body_style))
    elements.append(Spacer(1, 10))
    
    # Relationship Graph Embed
    if data["graph_image_path"] and os.path.exists(data["graph_image_path"]):
        elements.append(Paragraph("Cross-Document Relationship Graph", h2_style))
        elements.append(RLImage(data["graph_image_path"], width=500, height=300))
        elements.append(Spacer(1, 10))
        
    # 7.4 Visual Forensics
    elements.append(Paragraph("7.4 Visual Forensic Findings", h2_style))
    vf_rows = [["Detector", "Category", "Score", "Technical Details"]]
    for f in data["findings"]:
        vf_rows.append([
            Paragraph(f.detector, code_style),
            Paragraph(f.category, body_style),
            Paragraph(f"{int(f.confidence*100)}%", body_style),
            Paragraph(f.technical_details or f.observation, body_style)
        ])
    t_vf = Table(vf_rows, colWidths=[120, 90, 50, 280])
    t_vf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_vf)
    elements.append(Spacer(1, 10))
    
    # 7.5 Evidence and Traceability
    elements.append(Paragraph("7.5 Evidence and Traceability", h2_style))
    for ev in data["evidence_items"][:5]:  # sample crops
        ev_p = [
            [
                Paragraph(f"<b>Evidence Ref:</b> {ev.evidence_id}<br/><b>Detector:</b> {ev.detector}<br/><b>Score:</b> {int(ev.score*100)}%<br/><b>Observation:</b> {ev.observation}", body_style)
            ]
        ]
        t_ev = Table(ev_p, colWidths=[540])
        t_ev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(t_ev)
        elements.append(Spacer(1, 4))
        
    # 7.6 Investigation Summary & Dual-View Analysis
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("7.6 Investigation Summary & Dual-View Analysis", h2_style))
    for f in data["findings"][:6]:
        dv_content = [
            [Paragraph(f"<b>{f.title}</b> (Ref: {f.finding_id}) - Severity: <b>{f.category}</b> ({f.risk_level})", body_style)],
            [Paragraph(f"<b>Fact:</b> {f.observation}", body_style)],
            [Paragraph(f"<font color='#B91C1C'><b>Suspicious Explanation:</b></font> {f.suspicious_view}", body_style)],
            [Paragraph(f"<font color='#15803D'><b>Innocent Explanation:</b></font> {f.innocent_view}", body_style)],
            [Paragraph(f"<b>Recommended Verification:</b> {f.recommended_verification}", body_style)]
        ]
        t_dv = Table(dv_content, colWidths=[540])
        t_dv.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#E2E8F0"))
        ]))
        elements.append(KeepTogether(t_dv))
        elements.append(Spacer(1, 6))

    # Audit Proof
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Audit Trail Integrity Verification Proof", h2_style))
    audit_text = (
        f"<b>Audit Chain Verification Status:</b> {data['audit_status']['message']}<br/>"
        f"<b>Total Chain Events:</b> {data['audit_status']['total_events']} Verified<br/>"
        f"<b>Latest Leaf Entry Hash:</b> {data['audit_status'].get('latest_hash', 'N/A')}<br/>"
        "<font size=7 color='#64748B'>Maintains cryptographic hash chain following ISO/IEC 27037 digital evidence preservation standards.</font>"
    )
    t_aud = Table([[Paragraph(audit_text, body_style)]], colWidths=[540])
    t_aud.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86EFAC")),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    elements.append(t_aud)
    
    doc.build(elements)
    return output_path
