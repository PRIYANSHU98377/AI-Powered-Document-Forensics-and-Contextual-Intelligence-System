from typing import List, Dict, Any
import pymupdf

def run_pymupdf_text(doc_orig_path: str, page_number: int, scale_x: float = 1.0, scale_y: float = 1.0) -> List[Dict[str, Any]]:
    """
    Extracts word bounding boxes directly from PDF page.
    (x0, y0, x1, y1, word, block_no, line_no, word_no)
    Scales coordinates to match rendered page image dimensions.
    """
    if not doc_orig_path.lower().endswith(".pdf"):
        return []
        
    try:
        doc = pymupdf.open(doc_orig_path)
        if page_number > len(doc):
            return []
        page = doc[page_number - 1]
        words_data = page.get_text("words")
        doc.close()
        
        words = []
        for w_item in words_data:
            x0, y0, x1, y1, text = w_item[0], w_item[1], w_item[2], w_item[3], w_item[4]
            bx = x0 * scale_x
            by = y0 * scale_y
            bw = (x1 - x0) * scale_x
            bh = (y1 - y0) * scale_y
            words.append({
                "text": text.strip(),
                "confidence": 0.99,
                "bbox": (float(bx), float(by), float(bw), float(bh)),
                "engine": "pymupdf_vector"
            })
        return words
    except Exception as e:
        print(f"PyMuPDF text extraction error: {e}")
        return []
