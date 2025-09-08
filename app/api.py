import requests
from fastapi import FastAPI, HTTPException, status
from .logger import setup_logging
from .schemas import RagQueryRequest, RagQueryResponse, TopDoc, HealthCheck
from .clients import ollama_client, qdrant_client, crossencoder_client
from .config import OLLAMA_EMBED_MODEL, OLLAMA_CHAT_MODEL, OLLAMA_EXPAND_MODEL, DEFAULT_TOPK, DEFAULT_TOPN, CONTEXT_SNIPPET_CHARS, OLLAMA_URL, QDRANT_URL, QUERY_EXPANSION_TEMPLATE, RAG_SYSTEM_TEMPLATE, RAG_USER_TEMPLATE
from .clients.ollama_client import ensure_ollama_model

log = setup_logging()
app = FastAPI(title="RAG Query Service")

@app.on_event("startup")
def startup():
    ensure_ollama_model(OLLAMA_EMBED_MODEL)
    ensure_ollama_model(OLLAMA_CHAT_MODEL)
    ensure_ollama_model(OLLAMA_EXPAND_MODEL)

def check_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        return "up" if r.status_code < 400 else "down"
    except Exception:
        return "down"

@app.get("/health", response_model=HealthCheck, status_code=status.HTTP_200_OK)
def health():
    ollama_status = check_url(f"{OLLAMA_URL}")
    qdrant_status = check_url(f"{QDRANT_URL}/collections")
    overall = "ok" if all(s == "up" for s in [ollama_status, qdrant_status]) else "degraded"
    return HealthCheck(
        status=overall,
        ollama=ollama_status,
        qdrant=qdrant_status
    )

@app.post("/rag-query", response_model=RagQueryResponse)
def rag_query(req: RagQueryRequest):
    # 1) parameters
    use_expansion = bool(req.useExpansion)
    topK = req.topK or DEFAULT_TOPK
    topN = req.topN or DEFAULT_TOPN
    collection = req.collection

    # 2) optional query expansion
    expanded = None
    if use_expansion:
        prompt = QUERY_EXPANSION_TEMPLATE.format(query=req.query)
        try:
            expanded = ollama_client.generate_expand(prompt, model=OLLAMA_EXPAND_MODEL)
            if isinstance(expanded, dict):
                expanded = expanded.get("response") or str(expanded)
            expanded = (expanded or "").strip()
        except Exception as e:
            log.exception("Query expansion failed; continuing with original query")
            expanded = None

    # 3) final query selection
    final_query = (f"Original: {req.query}\nExpanded: {expanded}" if (use_expansion and expanded) else req.query)

    # 4) embed query
    try:
        vector = ollama_client.embed(final_query, model=OLLAMA_EMBED_MODEL)
    except Exception as e:
        log.exception("Embedding failed")
        raise HTTPException(status_code=502, detail="Embedding failed")

    # 5) qdrant search
    try:
        resp = qdrant_client.search_collection(collection=collection, vector=vector, limit=topK, with_payload=True)
        # Qdrant returns { "result": { "data": [ { "id": "...", "payload": {...}, "vector": [...] }, ...] } }
        # but older versions use "result": [{"id":..., "payload":...}, ...] — be robust:
        raw_results = resp.get("result")
        # If result contains "data", convert
        if isinstance(raw_results, dict) and "data" in raw_results:
            vector_records = raw_results["data"]
        elif isinstance(resp, dict) and "result" in resp and isinstance(resp["result"], list):
            vector_records = resp["result"]
        else:
            # fallback: assume top-level 'result' is list-like
            vector_records = resp.get("result") or []
    except Exception:
        log.exception("Qdrant search failed")
        raise HTTPException(status_code=502, detail="Vector search failed")

    # 6) prepare rerank pairs
    pairs = []
    for rec in vector_records:
        payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
        text = payload.get("text", "") if isinstance(payload, dict) else ""
        pairs.append([final_query, text])

    # 7) cross-encoder rerank
    try:
        scores = crossencoder_client.rerank(pairs)
    except Exception:
        log.exception("Cross-encoder rerank failed")
        # fallback: use Qdrant's stored 'score' if present, else zeroes
        scores = []
        for rec in vector_records:
            scores.append(rec.get("score", 0.0) if isinstance(rec, dict) else 0.0)

    # 8) combine & sort by rerank score
    combined = []
    for i, rec in enumerate(vector_records):
        doc_id = rec.get("id", str(i))
        payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
        rerank_score = scores[i] if i < len(scores) else rec.get("score", 0.0)
        combined.append({"id": doc_id, "rerank": float(rerank_score), "payload": payload})
    combined_sorted = sorted(combined, key=lambda x: x["rerank"], reverse=True)
    top = combined_sorted[:topN]

    # 9) build context: numbered short snippets
    context_blocks = []
    for idx, item in enumerate(top):
        text = (item.get("payload") or {}).get("text", "")
        snippet = (text[:CONTEXT_SNIPPET_CHARS] + "...") if len(text) > CONTEXT_SNIPPET_CHARS else text
        context_blocks.append(f"[{idx+1}] ({item['id']})\n{snippet}")
    context = "\n\n".join(context_blocks)

    # 10) ask Ollama chat using the context
    system_msg = RAG_SYSTEM_TEMPLATE
    user_msg = RAG_USER_TEMPLATE.format(query=req.query, context=context)

    try:
        chat_resp = ollama_client.chat(system_message=system_msg, user_message=user_msg, model=OLLAMA_CHAT_MODEL)
        # Ollama chat typically returns object with 'response' or 'message' structure; try to extract text:
        if isinstance(chat_resp, dict):
            # try common shapes
            ans = chat_resp.get("response") or chat_resp.get("message") or chat_resp.get("choices", [{}])[0].get("message", {}).get("content")
            if isinstance(ans, dict):
                # may be nested
                ans_text = ans.get("content") or str(ans)
            else:
                ans_text = str(ans)
        else:
            ans_text = str(chat_resp)
        answer_text = ans_text or ""
    except Exception:
        log.exception("Ollama chat failed")
        raise HTTPException(status_code=502, detail="Chat model failed")

    # 11) Response shape
    top_docs_out = []
    for it in top:
        top_docs_out.append({"id": it["id"], "rerank": it["rerank"], "payload": it["payload"]})

    return {
        "answer": answer_text,
        "model_used": OLLAMA_CHAT_MODEL,
        "topDocs": top_docs_out,
        "context": context
    }
