from typing import List
from .http_client import create_session
from ..config import CROSSENCODER_URL, HTTP_RETRIES, HTTP_BACKOFF_FACTOR, CONNECT_TIMEOUT, READ_TIMEOUT
from ..logger import setup_logging
import requests

log = setup_logging()
session, timeout = create_session(
    retries=HTTP_RETRIES,
    backoff_factor=HTTP_BACKOFF_FACTOR,
    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
)

def rerank(pairs: List[List[str]]) -> List[float]:
    try:
        r = session.post(CROSSENCODER_URL, json={"pairs": pairs}, timeout=timeout)
        r.raise_for_status()
        return r.json().get("scores", [])
    except requests.exceptions.Timeout:
        log.error(f"Cross-encoder request timed out after {timeout}")
    except Exception:
        log.exception("Cross-encoder request failed")
    return []