from typing import Dict, Any
from .http_client import create_session
from ..config import QDRANT_URL, HTTP_RETRIES, HTTP_BACKOFF_FACTOR, CONNECT_TIMEOUT, READ_TIMEOUT
from ..logger import setup_logging

log = setup_logging()
session, timeout = create_session(
    retries=HTTP_RETRIES,
    backoff_factor=HTTP_BACKOFF_FACTOR,
    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
)

def search_collection(collection: str, vector: list, limit: int = 25, with_payload: bool = True) -> Dict[str, Any]:
    try:
        url = f"{QDRANT_URL}/collections/{collection}/points/search"
        body = {"vector": vector, "limit": limit, "with_payload": with_payload}
        r = session.post(url, json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        log.exception("Qdrant search failed")
        raise