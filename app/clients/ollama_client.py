import requests
from typing import Any, Dict, List, Optional
from . import logger
from ..config import OLLAMA_URL, EMBED_MODEL, CHAT_MODEL, EXPAND_MODEL

log = logger.setup_logging()

def _extract_embedding(resp_json: Any) -> List[float]:
    # If list-wrapped
    payload = resp_json[0] if isinstance(resp_json, list) and len(resp_json) > 0 else resp_json
    if isinstance(payload, dict):
        embs = payload.get("embeddings") or payload.get("embedding")
        if embs is None:
            # fallback searching list
            for item in (resp_json if isinstance(resp_json, list) else [resp_json]):
                if isinstance(item, dict) and "embeddings" in item:
                    embs = item["embeddings"]
                    break
        if isinstance(embs, list) and len(embs) > 0 and isinstance(embs[0], list):
            return embs[0]
        if isinstance(embs, list):
            return embs
    if isinstance(resp_json, list) and all(isinstance(x, (int, float)) for x in resp_json):
        return resp_json
    raise ValueError("Unrecognized embedding shape from Ollama response")

def embed(text: str, model: str = EMBED_MODEL, timeout: int = 30) -> List[float]:
    url = f"{OLLAMA_URL.rstrip('/')}/api/embed"
    payload = {"model": model, "input": text}
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return _extract_embedding(r.json())

def generate_expand(prompt: str, model: str = EXPAND_MODEL, timeout: int = 30) -> str:
    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    # some Ollama responses have {"response": "<text>"} or direct shape; try both
    j = r.json()
    if isinstance(j, dict):
        return j.get("response") or j.get("text") or str(j)
    return str(j)

def chat(system_message: str, user_message: str, model: str = CHAT_MODEL, timeout: int = 30) -> Dict[str, Any]:
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    }
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()
