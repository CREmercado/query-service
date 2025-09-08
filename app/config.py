import os
from pathlib import Path

# Service addresses (docker-compose internal hostnames)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
CROSSENCODER_URL = os.getenv("CROSSENCODER_URL", "http://crossencoder:80/rerank")

# Default models
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1:8b")
EXPAND_MODEL = os.getenv("EXPAND_MODEL", "llama3.1:8b")

# Sizes / limits
DEFAULT_TOPK = int(os.getenv("DEFAULT_TOPK", "25"))
DEFAULT_TOPN = int(os.getenv("DEFAULT_TOPN", "5"))

# Other
CONTEXT_SNIPPET_CHARS = int(os.getenv("CONTEXT_SNIPPET_CHARS", "1200"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Load prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.es.md"
    return path.read_text(encoding="utf-8")