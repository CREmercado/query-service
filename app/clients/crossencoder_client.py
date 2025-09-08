import requests
from typing import List, Any
from ..config import CROSSENCODER_URL
from ..logger import setup_logging

log = setup_logging()

def rerank(pairs: List[List[str]], timeout: int = 30) -> List[float]:
    payload = {"pairs": pairs}
    r = requests.post(CROSSENCODER_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    # Expect {"scores": [0.1, 0.2, ...]}
    return data.get("scores", [])