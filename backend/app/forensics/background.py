import cv2
import numpy as np
from typing import List, Dict, Any, Optional

def detect_background_discontinuity(
    image_path: str,
    output_overlay_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Detects overwriting, whitening, or pasted rectangular background patches.
    Looks for rectangular boundaries with luminance steps or texture discontinuity.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect edges using Canny
    edges = cv2.Canny(gray, 30, 100)
    
    # Close small gaps in borders
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    findings = []
    overlay = img.copy()
    
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw < 80 or bh < 12 or bw > (w * 0.75) or bh > (h * 0.35):
            continue
            
        aspect = float(bw) / max(bh, 1.0)
        if aspect < 1.8:
            continue
            
        pad = 2
        if y < 8 or x < 8 or (y + bh + 8) > h or (x + bw + 8) > w:
            continue
            
        inner_roi = gray[y+pad:y+bh-pad, x+pad:x+bw-pad]
        outer_top = gray[max(0, y-8):y, x:x+bw]
        outer_bottom = gray[y+bh:min(h, y+bh+8), x:x+bw]
        
        if inner_roi.size == 0 or outer_top.size == 0 or outer_bottom.size == 0:
            continue
            
        inner_mean = float(np.mean(inner_roi))
        outer_mean = (float(np.mean(outer_top)) + float(np.mean(outer_bottom))) / 2.0
        lum_diff = abs(inner_mean - outer_mean)
        
        # Check border perimeter outline presence
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        is_rect = len(approx) in [4, 5, 6] or (cv2.contourArea(cnt) / (bw * bh) > 0.80)
        
        # Detected if rectangular patch with either:
        # a) noticeable background luminance step (> 4.0)
        # b) explicit bordered box enclosing text in an unbordered ledger area
        if is_rect and (lum_diff > 4.0 or (lum_diff > 2.0 and len(approx) <= 5)):
            score = min(0.96, round(0.65 + (lum_diff * 0.03), 2))
            
            cv2.rectangle(overlay, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            cv2.putText(overlay, f"Pasted/Whitened: {score:.2f}", (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            
            findings.append({
                "detector": "background_discontinuity_analysis",
                "bbox": (x, y, bw, bh),
                "score": score,
                "category": "POTENTIAL_MANIPULATION",
                "observation": f"Rectangular patch at ({x},{y},{bw},{bh}) exhibits background luminance step ({inner_mean:.1f} vs surrounding {outer_mean:.1f}, delta {lum_diff:.1f}) and sharp boundary transition consistent with whitening or pasted overlay.",
                "technical_details": f"Luminance step delta={lum_diff:.2f}. Bounding quadrilateral dimensions {bw}x{bh}px, aspect={aspect:.1f}."
            })
            
    if output_overlay_path:
        cv2.imwrite(output_overlay_path, overlay)
        
    return findings
