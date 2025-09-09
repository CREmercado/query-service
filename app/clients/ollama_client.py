from typing import Any, Dict, List
from .http_client import create_session
from ..config import OLLAMA_URL, HTTP_RETRIES, HTTP_BACKOFF_FACTOR, CONNECT_TIMEOUT, READ_TIMEOUT, OLLAMA_EMBED_MODEL
from ..logger import setup_logging
import requests

log = setup_logging()
session, timeout = create_session(
    retries=HTTP_RETRIES,
    backoff_factor=HTTP_BACKOFF_FACTOR,
    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
)

def _extract_embedding(resp_json: Any) -> List[float]:
    payload = resp_json[0] if isinstance(resp_json, list) and resp_json else resp_json
    if isinstance(payload, dict):
        embs = payload.get("embeddings") or payload.get("embedding")
        if embs is None:
            for item in (resp_json if isinstance(resp_json, list) else [resp_json]):
                if isinstance(item, dict) and "embeddings" in item:
                    embs = item["embeddings"]
                    break
        if isinstance(embs, list) and embs and isinstance(embs[0], list):
            return embs[0]
        if isinstance(embs, list):
            return embs
    if isinstance(resp_json, list) and all(isinstance(x, (int, float)) for x in resp_json):
        return resp_json
    raise ValueError("Unrecognized embedding shape from Ollama")

def embed(text: str, model: str = OLLAMA_EMBED_MODEL) -> List[float]:
    try:
        r = session.post(f"{OLLAMA_URL}/api/embed", json={"model": model, "input": text}, timeout=timeout)
        r.raise_for_status()
        return _extract_embedding(r.json())
    except Exception:
        log.exception("Ollama embed API failed")
        raise

def generate_expand(prompt: str, model: str) -> str:
    try:
        r = session.post(f"{OLLAMA_URL}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        return j.get("response") or j.get("text") or str(j)
    except Exception:
        log.exception("Ollama generate_expand API failed")
        raise

def chat(system_message: str, user_message: str, model: str) -> Dict[str, Any]:
    try:
        r = session.post(f"{OLLAMA_URL}/api/chat", json={"model": model, "stream": False,
            "messages": [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        log.exception("Ollama chat API failed")
        raise

def ensure_ollama_model(model: str):
    """
    Ensure Ollama model is available. If not, trigger pull.
    """
    # 1) check if model already available
    try:
        # 1) Check if model already available
        resp = session.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        resp.raise_for_status()
        tags = resp.json().get("models", [])
        if any(m.get("name") == model for m in tags):
            log.info(f"Ollama model '{model}' is already available.")
            return
    except Exception as e:
        log.warning(f"Could not list Ollama models: {e}")

    # 2) Pull model
    log.info(f"Pulling Ollama model '{model}' ... this may take several minutes")
    try:
        resp = session.post(
            f"{OLLAMA_URL}/api/pull",
            json={"model": model},
            timeout=timeout
        )
        resp.raise_for_status()
        log.info(f"Ollama model '{model}' pull triggered successfully.")
    except Exception as e:
        log.error(f"Failed to pull Ollama model '{model}': {e}")
        raise