import requests
from typing import Dict, Any
from ..config import QDRANT_URL
from . import logger

log = logger.setup_logging()

def search_collection(collection: str, vector: list, limit: int = 25, with_payload: bool = True, timeout: int = 30) -> Dict[str, Any]:
    url = f"{QDRANT_URL.rstrip('/')}/collections/{collection}/points/search"
    body = {
        "vector": vector,
        "limit": limit,
        "with_payload": with_payload
    }
    r = requests.post(url, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()