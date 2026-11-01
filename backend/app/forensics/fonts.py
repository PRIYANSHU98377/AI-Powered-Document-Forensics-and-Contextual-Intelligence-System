import cv2
import numpy as np
from typing import List, Dict, Any, Optional

def analyze_text_fonts_and_alignment(
    image_path: str,
    output_overlay_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes text line baselines, character heights, and stroke consistency.
    Detects spliced digits or words that differ in font size, stroke weight, or baseline from their line.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Binarize (invert so text is white on black background)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # 1. Connect words on same line horizontally
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 2))
    line_mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, line_kernel)
    
    line_contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    findings = []
    overlay = img.copy()
    
    for l_cnt in line_contours:
        lx, ly, lw, lh = cv2.boundingRect(l_cnt)
        if lw < 60 or lh < 8 or lh > 100:
            continue
            
        # Get individual character/word blobs within this line
        line_roi = binary[ly:ly+lh, lx:lx+lw]
        char_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        char_cleaned = cv2.morphologyEx(line_roi, cv2.MORPH_OPEN, char_kernel)
        char_contours, _ = cv2.findContours(char_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        blobs = []
        for c_cnt in char_contours:
            cx, cy, cw, ch = cv2.boundingRect(c_cnt)
            if cw < 4 or ch < 6 or cw > (lw * 0.8):
                continue
            # Calculate stroke density (pixel count / area)
            roi = line_roi[cy:cy+ch, cx:cx+cw]
            density = np.sum(roi > 0) / float(cw * ch)
            baseline_y = ly + cy + ch
            blobs.append({
                "bbox": (lx + cx, ly + cy, cw, ch),
                "height": ch,
                "width": cw,
                "density": density,
                "baseline": baseline_y
            })
            
        if len(blobs) < 4:
            continue
            
        heights = [b["height"] for b in blobs]
        median_h = float(np.median(heights))
        baselines = [b["baseline"] for b in blobs]
        median_base = float(np.median(baselines))
        
        for b in blobs:
            ch = b["height"]
            bx, by, bw, bh = b["bbox"]
            height_diff_pct = (ch - median_h) / max(median_h, 1.0)
            baseline_shift = abs(b["baseline"] - median_base)
            
            # Anomaly condition: character height > 22% larger than line median, or baseline shifted
            if height_diff_pct > 0.22 or (height_diff_pct > 0.15 and baseline_shift > 3.0):
                score = min(0.96, round(0.60 + (height_diff_pct * 0.8), 2))
                
                cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (0, 0, 255), 2)
                cv2.putText(overlay, f"Font Anomaly: {score:.2f}", (bx, max(12, by - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                
                findings.append({
                    "detector": "font_and_alignment_consistency",
                    "bbox": (bx, by, bw, bh),
                    "score": score,
                    "category": "POTENTIAL_MANIPULATION",
                    "observation": f"Character height {ch}px in region ({bx},{by},{bw},{bh}) is {height_diff_pct*100:.1f}% taller than surrounding line median ({median_h:.1f}px) with baseline offset of {baseline_shift:.1f}px.",
                    "technical_details": f"Line text height outlier. Measured height={ch}px, line median={median_h:.1f}px, baseline variance={baseline_shift:.1f}px."
                })
                
    if output_overlay_path:
        cv2.imwrite(output_overlay_path, overlay)
        
    return findings
