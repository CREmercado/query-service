import os
from pathlib import Path

# External services
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_docs")
CROSSENCODER_URL = os.getenv("CROSSENCODER_URL", "http://crossencoder:80/rerank")

# Default models
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
OLLAMA_EXPAND_MODEL = os.getenv("OLLAMA_EXPAND_MODEL", "llama3.1:8b")

# Sizes / limits
DEFAULT_TOPK = int(os.getenv("DEFAULT_TOPK", "25"))
DEFAULT_TOPN = int(os.getenv("DEFAULT_TOPN", "5"))

# Other
CONTEXT_SNIPPET_CHARS = int(os.getenv("CONTEXT_SNIPPET_CHARS", "1200"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# HTTP client settings
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))
HTTP_BACKOFF_FACTOR = float(os.getenv("HTTP_BACKOFF_FACTOR", "0.5"))
CONNECT_TIMEOUT = int(os.getenv("CONNECT_TIMEOUT", "5"))
READ_TIMEOUT = int(os.getenv("READ_TIMEOUT", "300"))

# Load prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.es.md"
    return path.read_text(encoding="utf-8")

QUERY_EXPANSION_TEMPLATE = load_prompt("query_expansion")
RAG_SYSTEM_TEMPLATE = load_prompt("rag_system")
RAG_USER_TEMPLATE = load_prompt("rag_user")