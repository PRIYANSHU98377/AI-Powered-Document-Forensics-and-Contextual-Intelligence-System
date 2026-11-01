import json
import httpx
from typing import Dict, Any, Optional
from ..core.config import settings
from ..core.security import wrap_untrusted_document_content
from .templates import get_template_dual_view

def generate_reasoning_explanation(
    detector_name: str,
    observation: str,
    evidence_id: str,
    field_context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Dual-View reasoning provider.
    Defaults to deterministic template-based reasoning.
    Optionally calls external LLM (Anthropic, OpenAI, or Ollama) if configured.
    Strictly preserves evidence IDs and never invents ungrounded facts.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    # 1. Deterministic template fallback
    default_views = get_template_dual_view(detector_name, evidence_id)
    if provider == "template":
        return default_views
        
    # Build prompt with OWASP ML Top 10 untrusted wrapper
    raw_context = f"Detector: {detector_name}\nObservation: {observation}\nEvidence ID: {evidence_id}\n"
    if field_context:
        raw_context += f"Related Fields: {json.dumps(field_context)}\n"
        
    wrapped_context = wrap_untrusted_document_content(raw_context)
    
    system_prompt = (
        "You are an impartial, objective Document Forensics & Integrity Analyst. "
        "Your task is to synthesize balanced, objective explanations for detected document anomalies.\n"
        "MANDATORY FORENSIC GUIDELINES:\n"
        "1. NEVER use the word 'fraud' or make definitive guilt determinations. Use 'potential anomaly', 'inconsistency', or 'potential manipulation'.\n"
        "2. You may ONLY reference the supplied Evidence ID and provided facts. DO NOT invent facts, people, or evidence.\n"
        "3. Provide exactly three fields in JSON format:\n"
        "   - 'suspicious_view': The technical argument for why this may indicate intentional alteration.\n"
        "   - 'innocent_view': Plausible benign explanations (compression, scanner calibration, formatting variation, clerical typo).\n"
        "   - 'recommended_verification': Concrete human-review verification action.\n"
        "Output ONLY valid JSON."
    )
    
    # 2. Anthropic API
    if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        try:
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            body = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 300,
                "system": system_prompt,
                "messages": [{"role": "user", "content": wrapped_context}]
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    txt = data["content"][0]["text"]
                    parsed = json.loads(txt)
                    return {
                        "suspicious": parsed.get("suspicious_view", default_views["suspicious"]),
                        "innocent": parsed.get("innocent_view", default_views["innocent"]),
                        "rec": parsed.get("recommended_verification", default_views["rec"])
                    }
        except Exception as e:
            print(f"Anthropic API call failed, using template: {e}")
            
    # 3. OpenAI API
    elif provider == "openai" and settings.OPENAI_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            body = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": wrapped_context}
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 300
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"])
                    return {
                        "suspicious": parsed.get("suspicious_view", default_views["suspicious"]),
                        "innocent": parsed.get("innocent_view", default_views["innocent"]),
                        "rec": parsed.get("recommended_verification", default_views["rec"])
                    }
        except Exception as e:
            print(f"OpenAI API call failed, using template: {e}")
            
    # 4. Ollama Local LLM
    elif provider == "ollama":
        try:
            body = {
                "model": "llama3",
                "system": system_prompt,
                "prompt": wrapped_context,
                "stream": False,
                "format": "json"
            }
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = json.loads(data["response"])
                    return {
                        "suspicious": parsed.get("suspicious_view", default_views["suspicious"]),
                        "innocent": parsed.get("innocent_view", default_views["innocent"]),
                        "rec": parsed.get("recommended_verification", default_views["rec"])
                    }
        except Exception as e:
            print(f"Ollama call failed, using template: {e}")
            
    # Default fallback
    return default_views
