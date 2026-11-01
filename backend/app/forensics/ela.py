import io
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance

def compute_ela(
    image_path: str,
    resave_quality: int = 90,
    scale: int = 15
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Error Level Analysis (ELA).
    Resaves image at resave_quality, computes absolute difference, and scales it.
    Returns (ela_image_rgb, ela_gray, global_mean_error).
    """
    orig = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    orig.save(buf, "JPEG", quality=resave_quality)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")
    
    diff = ImageChops.difference(orig, resaved)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale_factor = min(255.0 / max_diff, scale)
    
    diff_enhanced = ImageEnhance.Brightness(diff).enhance(scale_factor)
    ela_np = np.array(diff_enhanced)
    ela_gray = cv2.cvtColor(ela_np, cv2.COLOR_RGB2GRAY)
    
    global_mean = float(np.mean(ela_gray))
    return ela_np, ela_gray, global_mean

def detect_ela_anomalies(
    image_path: str,
    output_overlay_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes ELA for localized high-error compression spikes.
    Returns list of detected suspicious regions.
    """
    ela_rgb, ela_gray, global_mean = compute_ela(image_path)
    h, w = ela_gray.shape
    
    # Gaussian blur to smooth high frequency noise
    blurred = cv2.GaussianBlur(ela_gray, (21, 21), 0)
    
    # Threshold regions that exceed 2.5x the global background error level
    thresh_val = max(35.0, global_mean * 2.5)
    _, mask = cv2.threshold(blurred, int(thresh_val), 255, cv2.THRESH_BINARY)
    
    # Remove tiny noise specs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    findings = []
    
    # Prepare overlay canvas
    overlay = cv2.imread(image_path)
    if overlay is None:
        overlay = cv2.cvtColor(np.array(Image.open(image_path).convert("RGB")), cv2.COLOR_RGB2BGR)
        
    heatmap_colored = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)
    blended = cv2.addWeighted(overlay, 0.65, heatmap_colored, 0.35, 0)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 300 or area > (w * h * 0.4):
            continue
            
        x, y, bw, bh = cv2.boundingRect(cnt)
        roi_error = float(np.mean(ela_gray[y:y+bh, x:x+bw]))
        score = min(0.98, round((roi_error / max(thresh_val, 1.0)) * 0.7, 2))
        
        # Draw bounding rectangle on overlay
        cv2.rectangle(blended, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
        cv2.putText(blended, f"ELA Spike: {score:.2f}", (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        findings.append({
            "detector": "error_level_analysis",
            "bbox": (x, y, bw, bh),
            "score": score,
            "category": "POTENTIAL_MANIPULATION" if score > 0.75 else "OBSERVED",
            "observation": f"Localized compression error rate in region ({x},{y},{bw},{bh}) is {roi_error:.1f}, significantly elevated relative to document baseline ({global_mean:.1f}).",
            "technical_details": f"Resaved at JPEG Q=90. Localized error magnitude {roi_error:.2f} vs global mean {global_mean:.2f}."
        })
        
    if output_overlay_path:
        cv2.imwrite(output_overlay_path, blended)
        
    return findings
