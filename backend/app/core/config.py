import os
from pathlib import Path
from pydantic import BaseModel
from typing import Set

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
STORAGE_DIR = DATA_DIR / "storage"
EVIDENCE_DIR = DATA_DIR / "evidence"

for d in [DATA_DIR, UPLOAD_DIR, STORAGE_DIR, EVIDENCE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "DocDetective"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    STORAGE_DIR: Path = STORAGE_DIR
    EVIDENCE_DIR: Path = EVIDENCE_DIR
    
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'docdetective.db'}"
    
    # File limits
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
    
    # OCR settings
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    ENABLE_EASYOCR: bool = os.getenv("ENABLE_EASYOCR", "true").lower() in ("true", "1", "yes")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "template").lower()  # template, anthropic, openai, ollama
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Security & Masking
    MASK_SENSITIVE_DATA: bool = True

settings = Settings()
