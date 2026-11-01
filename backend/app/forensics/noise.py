import cv2
import numpy as np
from typing import List, Dict, Any, Optional

def analyze_noise_residual(
    image_path: str,
    output_overlay_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Computes high-frequency noise residual and checks for localized noise variance inconsistencies.
    Spliced or edited regions frequently carry a different sensor/scanner noise fingerprint.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return []
    h, w = img.shape
    
    # 1. High frequency residual: |Image - MedianBlur(Image)|
    denoised = cv2.medianBlur(img, 3)
    residual = cv2.absdiff(img, denoised).astype(np.float32)
    
    # 2. Local standard deviation using sliding box filter
    mean_sq = cv2.boxFilter(residual ** 2, -1, (25, 25))
    sq_mean = cv2.boxFilter(residual, -1, (25, 25)) ** 2
    local_var = np.maximum(0.0, mean_sq - sq_mean)
    local_std = np.sqrt(local_var)
    
    global_mean_std = float(np.mean(local_std))
    global_var_std = float(np.std(local_std))
    
    # 3. Detect regions where local std is > 3 sigma away from mean
    thresh = global_mean_std + 3.0 * max(global_var_std, 0.5)
    _, mask = cv2.threshold(local_std, thresh, 255, cv2.THRESH_BINARY)
    mask = mask.astype(np.uint8)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    findings = []
    
    color_img = cv2.imread(image_path)
    if color_img is None:
        color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 400 or area > (w * h * 0.35):
            continue
            
        x, y, bw, bh = cv2.boundingRect(cnt)
        patch_noise = float(np.mean(local_std[y:y+bh, x:x+bw]))
        score = min(0.95, round((patch_noise / max(thresh, 1.0)) * 0.7, 2))
        
        cv2.rectangle(color_img, (x, y), (x + bw, y + bh), (255, 128, 0), 2)
        cv2.putText(color_img, f"Noise Inconsistency: {score:.2f}", (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 128, 0), 1)
        
        findings.append({
            "detector": "noise_residual_analysis",
            "bbox": (x, y, bw, bh),
            "score": score,
            "category": "POTENTIAL_MANIPULATION" if score > 0.70 else "OBSERVED",
            "observation": f"High-frequency sensor noise standard deviation in region ({x},{y},{bw},{bh}) is {patch_noise:.2f}, deviating from global document mean ({global_mean_std:.2f}).",
            "technical_details": f"Median 3x3 residual variance. Local std={patch_noise:.2f} vs global threshold={thresh:.2f}."
        })
        
    if output_overlay_path:
        cv2.imwrite(output_overlay_path, color_img)
        
    return findings
