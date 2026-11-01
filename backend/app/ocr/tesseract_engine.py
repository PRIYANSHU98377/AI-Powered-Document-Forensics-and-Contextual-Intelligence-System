import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import pytesseract
from ..core.config import settings

def is_tesseract_available() -> bool:
    candidate_paths = [
        settings.TESSERACT_CMD,
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for p in candidate_paths:
        if p and os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return True
            
    # Check if tesseract is on PATH
    if shutil.which("tesseract"):
        return True
    return False

def run_tesseract(image_path: str) -> List[Dict[str, Any]]:
    """
    Runs Tesseract OCR on an image and returns list of word dicts:
    [{'text': str, 'conf': float, 'bbox': (x, y, w, h), 'engine': 'tesseract'}]
    """
    if not is_tesseract_available():
        return []
        
    try:
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if text and conf > 10.0:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                words.append({
                    "text": text,
                    "confidence": conf / 100.0,
                    "bbox": (float(x), float(y), float(w), float(h)),
                    "engine": "tesseract"
                })
        return words
    except Exception as e:
        print(f"Tesseract execution error: {e}")
        return []
