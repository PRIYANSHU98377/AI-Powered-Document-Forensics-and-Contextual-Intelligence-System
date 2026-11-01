import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict

def detect_copy_move(
    image_path: str,
    output_overlay_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Detects copy-move forgery (cloned stamps, signatures, or digits) using ORB keypoint
    matching and displacement vector clustering.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Initialize ORB detector with 2500 features
    orb = cv2.ORB_create(nfeatures=2500, fastThreshold=12)
    kps, descs = orb.detectAndCompute(gray, None)
    
    if descs is None or len(kps) < 20:
        return []
        
    # BFMatcher with Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(descs, descs, k=3)
    
    valid_pairs = []
    min_dist_px = 50.0  # Minimum spatial distance to avoid adjacent feature self-matching
    
    for m_list in matches:
        if len(m_list) < 2:
            continue
        m1 = m_list[0]
        # Skip identical feature
        candidates = [m for m in m_list if m.queryIdx != m.trainIdx]
        if not candidates:
            continue
        best = candidates[0]
        
        pt1 = np.array(kps[best.queryIdx].pt)
        pt2 = np.array(kps[best.trainIdx].pt)
        spatial_dist = np.linalg.norm(pt1 - pt2)
        
        if spatial_dist > min_dist_px and best.distance < 45:
            # Consistent displacement vector
            dx = round(pt2[0] - pt1[0], -1)  # bin to nearest 10 px
            dy = round(pt2[1] - pt1[1], -1)
            valid_pairs.append({
                "pt1": pt1,
                "pt2": pt2,
                "vector": (dx, dy),
                "dist": best.distance
            })
            
    # Cluster displacement vectors
    vector_clusters = defaultdict(list)
    for pair in valid_pairs:
        vector_clusters[pair["vector"]].append(pair)
        
    findings = []
    overlay = img.copy()
    
    for vec, pairs in vector_clusters.items():
        if len(pairs) >= 5:  # Significant cluster of cloned keypoints!
            pts1 = np.array([p["pt1"] for p in pairs])
            pts2 = np.array([p["pt2"] for p in pairs])
            
            x1, y1, bw1, bh1 = cv2.boundingRect(pts1.astype(np.int32))
            x2, y2, bw2, bh2 = cv2.boundingRect(pts2.astype(np.int32))
            
            # Draw connections on overlay
            for p in pairs:
                p1 = (int(p["pt1"][0]), int(p["pt1"][1]))
                p2 = (int(p["pt2"][0]), int(p["pt2"][1]))
                cv2.line(overlay, p1, p2, (0, 0, 255), 1)
                cv2.circle(overlay, p1, 3, (0, 255, 0), -1)
                cv2.circle(overlay, p2, 3, (255, 0, 0), -1)
                
            cv2.rectangle(overlay, (x1, y1), (x1 + bw1, y1 + bh1), (0, 255, 0), 2)
            cv2.rectangle(overlay, (x2, y2), (x2 + bw2, y2 + bh2), (255, 0, 0), 2)
            cv2.putText(overlay, f"Copy-Move: {len(pairs)} pts", (x2, max(15, y2 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            score = min(0.99, round(0.65 + (len(pairs) * 0.05), 2))
            findings.append({
                "detector": "copy_move_detection",
                "bbox": (x2, y2, bw2, bh2),
                "source_bbox": (x1, y1, bw1, bh1),
                "score": score,
                "category": "POTENTIAL_MANIPULATION",
                "observation": f"Detected {len(pairs)} cloned feature keypoint pairs duplicated between region ({x1},{y1},{bw1},{bh1}) and region ({x2},{y2},{bw2},{bh2}) with identical displacement vector {vec}.",
                "technical_details": f"ORB keypoint matching with RANSAC-like spatial displacement clustering. {len(pairs)} parallel vector correspondences."
            })
            
    if output_overlay_path:
        cv2.imwrite(output_overlay_path, overlay)
        
    return findings
