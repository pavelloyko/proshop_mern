"""
RAG Search MCP Server for ProShop MERN.

Wraps query.py search logic (BGE-M3 + Qdrant cosine + RRF) as a single
MCP tool so agents can retrieve project documentation chunks.
"""

import os
import re
from pathlib import Path

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import torch
from fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
COLLECTION_NAME = "proshop_chunks"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "BAAI/bge-m3"

# Russian → English term map for cross-lingual query bridging
_RU_EN = {
    "какая": "which", "какие": "which", "какой": "which", "какую": "which",
    "что": "what", "как": "how", "где": "where", "когда": "when",
    "почему": "why", "зачем": "why", "сколько": "how many", "кто": "who",
    "бд": "database", "база": "database",
    "фичи": "features", "фича": "feature", "фич": "feature",
    "функционал": "functionality",
    "зависит": "depends", "зависят": "depend",
    "зависимость": "dependency", "зависимости": "dependencies",
    "инцидент": "incident", "инциденты": "incidents",
    "чекаут": "checkout",
    "оплата": "payment", "оплаты": "payment", "оплату": "payment",
    "авторизация": "authentication", "аутентификация": "authentication",
    "логин": "login",
    "корзина": "cart", "корзины": "cart",
    "товар": "product", "товары": "products", "товаров": "products",
    "заказ": "order", "заказы": "orders", "заказов": "orders",
    "пользователь": "user", "пользователя": "user",
    "пользователей": "users",
    "админ": "admin", "админа": "admin",
    "роли": "roles", "роль": "role",
    "маршрут": "route", "маршруты": "routes",
    "эндпоинт": "endpoint", "эндпоинты": "endpoints",
    "модель": "model", "модели": "models",
    "схема": "schema", "схемы": "schemas",
    "миграция": "migration",
    "деплой": "deployment",
    "конфиг": "config", "конфигурация": "configuration",
    "ошибка": "error", "ошибки": "errors",
    "лог": "log", "логи": "logs",
    "скрипт": "script",
    "используется": "used", "используются": "used",
    "случилось": "happened", "случается": "happens",
    "именно": "specifically",
    "последнего": "last", "последний": "last", "последняя": "last",
    "последнем": "last", "последней": "last",
    "первый": "first", "первая": "first",
    "нужно": "need", "нужен": "need", "нужна": "need",
    "может": "can", "могут": "can",
    "должен": "should", "должна": "should",
    "сделать": "do", "делает": "does",
    "работает": "works", "работают": "work",
    "настроить": "configure", "настройка": "configuration",
    "добавить": "add", "добавление": "adding",
    "удалить": "delete", "удаление": "deleting",
    "изменить": "change", "изменение": "changing",
    "обновить": "update", "обновление": "updating",
    "создать": "create", "создание": "creating",
    "решение": "decision",
    "во": "during", "время": "time",
}

mcp = FastMCP("proshop-rag-search")

# ---------------------------------------------------------------------------
# Lazy-loaded singletons — model loads once on first call
# ---------------------------------------------------------------------------

_model: SentenceTransformer | None = None
_client: QdrantClient | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        _model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    return _model


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, timeout=30)
    return _client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яА-ЯёЁ]", text))


def _ru_to_en_query(ru_query: str) -> str:
    tokens = re.findall(r"\S+", ru_query)
    out = []
    for tok in tokens:
        lower = tok.lower().strip(".,!?;:")
        if lower in _RU_EN:
            out.append(_RU_EN[lower])
        elif _has_cyrillic(tok):
            continue
        else:
            out.append(tok)
    return " ".join(out)


def _point_to_chunk(point) -> dict:
    p = point.payload
    text = p.get("text", "")
    snippet = text[:200] + "..." if len(text) > 200 else text
    return {
        "source_file": p.get("source_file", ""),
        "file_path": p.get("file_path", ""),
        "title": p.get("title", ""),
        "parent_headings": p.get("parent_headings", []),
        "type": p.get("type", ""),
        "score": round(point.score, 4),
        "snippet": snippet,
    }


# ---------------------------------------------------------------------------
# Tool — search_project_docs
# ---------------------------------------------------------------------------

@mcp.tool()
def search_project_docs(query: str, top_k: int = 5) -> dict:
    """Search the proshop_mern project documentation using semantic
    vector search (BGE-M3 embeddings, Qdrant cosine similarity).

    Retrieves relevant chunks from ADRs, feature docs, API references,
    runbooks, incidents, glossary, and dev history. Supports Russian and
    English queries — Russian queries are auto-bridged to English via a
    local dictionary and merged with Reciprocal Rank Fusion.

    WHEN TO CALL:
      - The user asks about proshop_mern architecture, features, ADRs,
        runbooks, incidents, API endpoints, glossary terms, or dev history.
      - You need factual information about HOW or WHY something works in
        the project — e.g. "why MongoDB?", "how does auth work?",
        "what happened in the last checkout incident?".
      - You MUST use this FIRST when the user asks about product
        functionality, technical decisions, or project documentation.

    WHEN NOT TO CALL:
      - The user asks about feature flag STATE (enabled/disabled/traffic %)
        — use the proshop-feature-flags MCP server (get_feature_info) instead.
      - The user asks to CHANGE a feature flag — use proshop-feature-flags
        (set_feature_state / adjust_traffic_rollout).
      - The user asks about live application data (orders, users, products)
        — this tool only covers project documentation, not runtime data.

    EXAMPLES:
      1. search_project_docs(query="why was MongoDB chosen over PostgreSQL?")
         → returns ADR-001 chunks with Context, Decision, Consequences.
      2. search_project_docs(query="какие фичи зависят от stripe", top_k=3)
         → returns payment-related chunks from feature-flags-spec and ADR-004.
      3. search_project_docs(query="checkout incident timeline")
         → returns i-001-paypal-double-charge chunks (Timeline, Root Cause).

    Args:
        query: Natural-language search query (Russian or English).
        top_k: Number of chunks to return (1-20, default 5).

    Returns:
        Dict with 'total' (int) and 'chunks' (list of chunk objects).
        Each chunk has: source_file, file_path, title, parent_headings,
        type, score, snippet (~200 chars).
    """
    top_k = max(1, min(20, top_k))

    model = _get_model()
    client = _get_client()

    queries = [query]
    if _has_cyrillic(query):
        en_query = _ru_to_en_query(query)
        if en_query and en_query != query:
            queries.append(en_query)

    vectors = model.encode(queries, normalize_embeddings=True, show_progress_bar=False)

    fetch_limit = top_k * 3
    all_results: list[list] = []
    for vec in vectors:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vec.tolist(),
            limit=fetch_limit,
            with_payload=True,
        )
        all_results.append(results.points)

    if len(all_results) == 1:
        chunks = [_point_to_chunk(p) for p in all_results[0][:top_k]]
        return {"total": len(chunks), "chunks": chunks}

    # Reciprocal Rank Fusion
    rrf_k = 60
    rrf_scores: dict[int, float] = {}
    hits_by_id: dict[int, dict] = {}

    for ranked_list in all_results:
        for rank, point in enumerate(ranked_list, 1):
            pid = point.id
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (rrf_k + rank)
            if pid not in hits_by_id or point.score > hits_by_id[pid]["score"]:
                hits_by_id[pid] = _point_to_chunk(point)
                hits_by_id[pid]["score"] = round(point.score, 4)

    ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
    chunks = []
    for pid in ranked_ids:
        hit = hits_by_id[pid]
        hit["rrf_score"] = round(rrf_scores[pid], 5)
        chunks.append(hit)

    return {"total": len(chunks), "chunks": chunks}


if __name__ == "__main__":
    mcp.run()
