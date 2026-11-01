from typing import List, Dict, Any
from rapidfuzz import fuzz
from ..models.schemas import ExtractedWord, WordCandidate, BoundingBox

def compute_iou(boxA, boxB) -> float:
    # box = (x, y, w, h)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    
    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    unionArea = float(boxAArea + boxBArea - interArea)
    
    if unionArea <= 0:
        return 0.0
    return interArea / unionArea

def fuse_word_streams(
    primary_words: List[Dict[str, Any]],
    secondary_words: List[Dict[str, Any]],
    page_num: int,
    page_width: float,
    page_height: float
) -> List[ExtractedWord]:
    """
    Fuses two OCR streams (e.g. Tesseract vs EasyOCR, or PyMuPDF vs Tesseract) using IoU matching.
    Detects discrepancies and flags low reliability when text candidates disagree.
    """
    if not secondary_words:
        # Single engine stream
        results = []
        for w in primary_words:
            bx, by, bw, bh = w["bbox"]
            bbox = BoundingBox(
                page=page_num,
                x=round(bx, 1),
                y=round(by, 1),
                w=round(bw, 1),
                h=round(bh, 1),
                normalized_x=round(bx / page_width, 4) if page_width else 0.0,
                normalized_y=round(by / page_height, 4) if page_height else 0.0,
                normalized_w=round(bw / page_width, 4) if page_width else 0.0,
                normalized_h=round(bh / page_height, 4) if page_height else 0.0
            )
            cand = WordCandidate(text=w["text"], confidence=round(w["confidence"], 3), engine=w["engine"])
            results.append(ExtractedWord(
                text=w["text"],
                bbox=bbox,
                confidence=round(w["confidence"], 3),
                ocr_agreement=1.0,
                raw_candidates=[cand],
                reliability="high" if w["confidence"] >= 0.70 else "medium"
            ))
        return results

    matched_secondary = set()
    fused: List[ExtractedWord] = []

    for pw in primary_words:
        p_bbox = pw["bbox"]
        best_match = None
        best_iou = 0.0
        best_idx = -1
        
        for idx, sw in enumerate(secondary_words):
            if idx in matched_secondary:
                continue
            iou = compute_iou(p_bbox, sw["bbox"])
            if iou > 0.25 and iou > best_iou:
                best_iou = iou
                best_match = sw
                best_idx = idx
                
        bx, by, bw, bh = p_bbox
        bbox = BoundingBox(
            page=page_num,
            x=round(bx, 1),
            y=round(by, 1),
            w=round(bw, 1),
            h=round(bh, 1),
            normalized_x=round(bx / page_width, 4) if page_width else 0.0,
            normalized_y=round(by / page_height, 4) if page_height else 0.0,
            normalized_w=round(bw / page_width, 4) if page_width else 0.0,
            normalized_h=round(bh / page_height, 4) if page_height else 0.0
        )
        
        p_cand = WordCandidate(text=pw["text"], confidence=round(pw["confidence"], 3), engine=pw["engine"])
        
        if best_match:
            matched_secondary.add(best_idx)
            s_cand = WordCandidate(text=best_match["text"], confidence=round(best_match["confidence"], 3), engine=best_match["engine"])
            
            # Compare texts
            sim = fuzz.ratio(pw["text"].lower(), best_match["text"].lower()) / 100.0
            if sim >= 0.85:
                # Strong consensus
                fused.append(ExtractedWord(
                    text=pw["text"],
                    bbox=bbox,
                    confidence=round(max(pw["confidence"], best_match["confidence"]), 3),
                    ocr_agreement=round(sim, 2),
                    raw_candidates=[p_cand, s_cand],
                    reliability="high"
                ))
            else:
                # Disagreement!
                fused.append(ExtractedWord(
                    text=pw["text"],
                    bbox=bbox,
                    confidence=round(min(pw["confidence"], best_match["confidence"]), 3),
                    ocr_agreement=round(sim, 2),
                    raw_candidates=[p_cand, s_cand],
                    reliability="low"
                ))
        else:
            # Unmatched primary word
            fused.append(ExtractedWord(
                text=pw["text"],
                bbox=bbox,
                confidence=round(pw["confidence"] * 0.85, 3),
                ocr_agreement=0.50,
                raw_candidates=[p_cand],
                reliability="medium"
            ))

    # Add any remaining secondary words that were completely missed by primary
    for idx, sw in enumerate(secondary_words):
        if idx not in matched_secondary:
            bx, by, bw, bh = sw["bbox"]
            bbox = BoundingBox(
                page=page_num,
                x=round(bx, 1),
                y=round(by, 1),
                w=round(bw, 1),
                h=round(bh, 1),
                normalized_x=round(bx / page_width, 4) if page_width else 0.0,
                normalized_y=round(by / page_height, 4) if page_height else 0.0,
                normalized_w=round(bw / page_width, 4) if page_width else 0.0,
                normalized_h=round(bh / page_height, 4) if page_height else 0.0
            )
            s_cand = WordCandidate(text=sw["text"], confidence=round(sw["confidence"], 3), engine=sw["engine"])
            fused.append(ExtractedWord(
                text=sw["text"],
                bbox=bbox,
                confidence=round(sw["confidence"] * 0.80, 3),
                ocr_agreement=0.50,
                raw_candidates=[s_cand],
                reliability="low"
            ))

    # Sort top-to-bottom, left-to-right
    fused.sort(key=lambda w: (round(w.bbox.y / 15.0) * 15.0, w.bbox.x))
    return fused
