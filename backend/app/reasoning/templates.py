from typing import Dict, Any

TEMPLATES = {
    "font_and_alignment_consistency": {
        "suspicious": "Character/digit differs in font height, stroke weight, or baseline alignment from adjacent text on the same line, consistent with spliced numerical alteration (Evidence ID: {evidence_id}).",
        "innocent": "Typesetting font substitution, variable pitch numerical fonts, or document layout formatting variations between template header fields and dynamic entries.",
        "rec": "Request official computer-generated PDF directly from issuer or cross-verify salary against official income tax filings (e.g. Form 16 / ITR)."
    },
    "copy_move_detection": {
        "suspicious": "Multiple clusters of matching ORB keypoints with identical spatial displacement indicate duplicate stamp, seal, or graphic cloning (Evidence ID: {evidence_id}).",
        "innocent": "Pre-printed corporate stationery containing identical repetitive security watermarks, repeated form headers, or standard graphic motifs.",
        "rec": "Examine original physical document for wet-ink notary indentation or embossed seal texture."
    },
    "background_discontinuity_analysis": {
        "suspicious": "Rectangular region exhibits distinct luminance step transition and texture suppression characteristic of whitening or pasted overlay (Evidence ID: {evidence_id}).",
        "innocent": "Flatbed scanner sensor calibration artifact, uneven document illumination, or distinct table cell shading in original bank report format.",
        "rec": "Request direct electronic bank statement download with verified digital cryptographic signature."
    },
    "pdf_metadata_analysis": {
        "suspicious": "PDF metadata indicates compilation or modification by interactive graphic design software rather than direct system export (Evidence ID: {evidence_id}).",
        "innocent": "Applicant combined separate document scans, compressed file size, or adjusted page rotation using commercial PDF editing tools before upload.",
        "rec": "Request uncompressed direct digital download or original paper document for physical inspection."
    },
    "pasted_signature_edge_analysis": {
        "suspicious": "Signature stroke bounding area exhibits sharp rectangular clipping edges and background luminance discrepancy consistent with a pasted image (Evidence ID: {evidence_id}).",
        "innocent": "Signer inserted a saved personal signature graphic into an electronic PDF fillable form field rather than drawing with a stylus.",
        "rec": "Require in-person physical signature execution or biometric digital signature verification."
    },
    "cross_doc_dob_correlator": {
        "suspicious": "Date of Birth stated on identity card conflicts with Date of Birth on loan application form, indicating potential document substitution (Evidence ID: {evidence_id}).",
        "innocent": "Clerical data entry mistake during form submission, or date format confusion between DD-MM-YYYY and MM-DD-YYYY conventions.",
        "rec": "Perform real-time API verification against government national identity database."
    },
    "cross_doc_address_correlator": {
        "suspicious": "Residential address on utility invoice diverges from declared residential address on application, indicating potential fabricated address proof (Evidence ID: {evidence_id}).",
        "innocent": "Applicant maintains multiple residences, recently relocated, or utility bill is registered in name of family member or landlord.",
        "rec": "Request registered rental lease agreement, property ownership title, or conduct physical field address verification."
    },
    "ledger_arithmetic_verifier": {
        "suspicious": "Stated closing balance violates ledger arithmetic identity: Opening Balance + Total Credits - Total Debits != Closing Balance (Evidence ID: {evidence_id}).",
        "innocent": "Unlisted uncleared checks, ongoing transaction holds, interest adjustments not reflected in line items, or multi-page continuation statement.",
        "rec": "Obtain bank confirmation certificate or complete multi-month bank statement directly from bank portal."
    },
    "payroll_component_verifier": {
        "suspicious": "Gross salary exceeds sum of individual earnings breakdown components by a substantial margin (Evidence ID: {evidence_id}).",
        "innocent": "Variable incentive, quarterly retention allowance, or unitemized reimbursement rolled into gross earnings total.",
        "rec": "Inspect official employer salary certificate and matching monthly bank credit transaction."
    },
    "dob_age_verifier": {
        "suspicious": "Stated applicant age contradicts age calculated from provided Date of Birth (Evidence ID: {evidence_id}).",
        "innocent": "Applicant recorded age at time of previous application cycle or rounded age incorrectly.",
        "rec": "Verify applicant Date of Birth against official government birth registry."
    },
    "error_level_analysis": {
        "suspicious": "Localized compression error rate is significantly elevated relative to document baseline, suggesting secondary resaving of edited region (Evidence ID: {evidence_id}).",
        "innocent": "Uneven lighting, camera flash specular reflection, or multi-generation JPEG re-encoding across differing color regions.",
        "rec": "Acquire high-resolution lossless scan (PNG/TIFF) or inspect original physical document."
    },
    "noise_residual_analysis": {
        "suspicious": "Sensor noise residual standard deviation deviates from global document average, indicating spliced patch with foreign noise profile (Evidence ID: {evidence_id}).",
        "innocent": "Local scanner glass smudges, paper grain heterogeneity, or selective scanner auto-contrast adjustment.",
        "rec": "Request clean direct optical scan."
    }
}

def get_template_dual_view(detector_name: str, evidence_id: str = "") -> Dict[str, str]:
    tmpl = TEMPLATES.get(detector_name)
    if not tmpl:
        return {
            "suspicious": f"Anomaly detected by forensic detector {detector_name} (Evidence ID: {evidence_id}).",
            "innocent": "Potential image rendering artifact, non-standard layout formatting, or OCR transcription variance.",
            "rec": "Conduct manual human review and cross-examine supporting documentation."
        }
    return {
        "suspicious": tmpl["suspicious"].format(evidence_id=evidence_id or "N/A"),
        "innocent": tmpl["innocent"],
        "rec": tmpl["rec"]
    }
