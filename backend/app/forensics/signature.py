import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

def extract_signature_regions(image_path: str) -> List[Dict[str, Any]]:
    """
    Locates potential signature regions based on cursive stroke density,
    aspect ratio, and placement in the document.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Signatures usually in bottom 60% of document
    y_start = int(h * 0.40)
    sub_gray = gray[y_start:, :]
    
    # Adaptive threshold to isolate pen strokes
    thresh = cv2.adaptiveThreshold(sub_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8)
    
    # Connect pen strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 4))
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        actual_y = y_start + y
        
        # Check aspect ratio (signatures are typically horizontal, w > h)
        aspect = float(bw) / max(bh, 1.0)
        area = bw * bh
        
        if 80 < bw < 350 and 20 < bh < 130 and 1.4 < aspect < 6.0 and area > 2000:
            roi_strokes = thresh[y:y+bh, x:x+bw]
            stroke_ratio = np.sum(roi_strokes > 0) / float(area)
            
            # Cursive signatures have stroke density between 0.05 and 0.35
            if 0.05 < stroke_ratio < 0.38:
                candidates.append({
                    "bbox": (x, actual_y, bw, bh),
                    "stroke_ratio": stroke_ratio,
                    "crop": img[actual_y:actual_y+bh, x:x+bw]
                })
                
    return candidates

def check_pasted_signature_edges(img_crop: np.ndarray) -> Tuple[bool, float, str]:
    """
    Checks if a signature crop exhibits sharp rectangular box edges or background tint step,
    indicating it was pasted from another source.
    """
    if img_crop is None or img_crop.size == 0:
        return False, 0.0, "Empty crop"
        
    gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    ch, cw = gray.shape
    
    # Check border gradient (left, right, top, bottom edges)
    edge_thickness = 4
    if ch < 15 or cw < 15:
        return False, 0.0, "Too small"
        
    top_edge = gray[:edge_thickness, :]
    bottom_edge = gray[-edge_thickness:, :]
    left_edge = gray[:, :edge_thickness]
    right_edge = gray[:, -edge_thickness:]
    
    center_roi = gray[edge_thickness:ch-edge_thickness, edge_thickness:cw-edge_thickness]
    
    border_mean = np.mean([np.mean(top_edge), np.mean(bottom_edge), np.mean(left_edge), np.mean(right_edge)])
    center_bg_mean = np.percentile(center_roi, 85)  # estimate background luminance
    
    diff = abs(center_bg_mean - border_mean)
    
    # Detect hard rectangular bounding line
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=5)
    
    has_box_lines = False
    if lines is not None and len(lines) >= 3:
        has_box_lines = True
        
    if diff > 7.0 or has_box_lines:
        score = min(0.95, round(0.65 + (diff * 0.03), 2))
        return True, score, f"Sharp perimeter edge and background step delta of {diff:.1f} detected around signature."
        
    return False, 0.20, "Natural stroke boundaries with no artificial perimeter."

def compare_signatures(sig1_crop: np.ndarray, sig2_crop: np.ndarray) -> Tuple[float, str]:
    """
    Compares two signature crops using Hu Moments and ORB keypoint cosine similarity.
    Returns (similarity_score, observation).
    """
    if sig1_crop is None or sig2_crop is None:
        return 0.0, "Missing signature crops"
        
    # Resize to common dimensions
    dim = (180, 70)
    g1 = cv2.resize(cv2.cvtColor(sig1_crop, cv2.COLOR_BGR2GRAY), dim)
    g2 = cv2.resize(cv2.cvtColor(sig2_crop, cv2.COLOR_BGR2GRAY), dim)
    
    # Binarize
    _, b1 = cv2.threshold(g1, 200, 255, cv2.THRESH_BINARY_INV)
    _, b2 = cv2.threshold(g2, 200, 255, cv2.THRESH_BINARY_INV)
    
    # 1. Hu moments shape distance
    m1 = cv2.HuMoments(cv2.moments(b1)).flatten()
    m2 = cv2.HuMoments(cv2.moments(b2)).flatten()
    # Log transform
    lm1 = -np.sign(m1) * np.log10(np.abs(m1) + 1e-12)
    lm2 = -np.sign(m2) * np.log10(np.abs(m2) + 1e-12)
    hu_dist = np.linalg.norm(lm1[:4] - lm2[:4])
    
    # Normalized similarity
    similarity = max(0.0, min(1.0, 1.0 - (hu_dist / 6.0)))
    
    if similarity >= 0.75:
        obs = f"Signatures exhibit consistent morphological structure (Hu-moment match: {similarity*100:.1f}%)."
    else:
        obs = f"Signatures exhibit divergent stroke morphology (Hu-moment divergence: {hu_dist:.2f}, match {similarity*100:.1f}%)."
        
    return round(similarity, 2), obs
