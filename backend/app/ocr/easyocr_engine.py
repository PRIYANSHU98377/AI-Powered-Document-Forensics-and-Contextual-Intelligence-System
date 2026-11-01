from typing import List, Dict, Any

_reader = None

def is_easyocr_available() -> bool:
    try:
        import easyocr
        return True
    except ImportError:
        return False

def get_easyocr_reader():
    global _reader
    if _reader is None and is_easyocr_available():
        import easyocr
        # Initialize CPU reader
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader

def run_easyocr(image_path: str) -> List[Dict[str, Any]]:
    """
    Runs EasyOCR on image, returns word dicts.
    """
    if not is_easyocr_available():
        return []
    try:
        reader = get_easyocr_reader()
        if not reader:
            return []
        results = reader.readtext(image_path)
        words = []
        for bbox, text, conf in results:
            text = text.strip()
            if not text:
                continue
            # bbox is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            x_min = min(pt[0] for pt in bbox)
            y_min = min(pt[1] for pt in bbox)
            x_max = max(pt[0] for pt in bbox)
            y_max = max(pt[1] for pt in bbox)
            w = x_max - x_min
            h = y_max - y_min
            
            # Split compound phrases into words
            sub_words = text.split()
            if len(sub_words) > 1:
                word_w = w / len(sub_words)
                for idx, sw in enumerate(sub_words):
                    words.append({
                        "text": sw,
                        "confidence": float(conf),
                        "bbox": (float(x_min + idx * word_w), float(y_min), float(word_w), float(h)),
                        "engine": "easyocr"
                    })
            else:
                words.append({
                    "text": text,
                    "confidence": float(conf),
                    "bbox": (float(x_min), float(y_min), float(w), float(h)),
                    "engine": "easyocr"
                })
        return words
    except Exception as e:
        print(f"EasyOCR execution error: {e}")
        return []
