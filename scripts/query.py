"""
Search script for proshop_mern RAG pipeline.

Embeds a query with BGE-M3 (same model used for ingestion) and retrieves
top-K chunks from Qdrant via cosine similarity. Supports optional payload
pre-filtering by type and source_file.

Cross-lingual: Russian queries are automatically translated to English via
a local term dictionary, then both vectors are searched and results merged
by max score per chunk — no external API needed.

Usage:
    # Single query
    python3 scripts/query.py "какая БД используется"

    # With filters
    python3 scripts/query.py "incident checkout" --type incident
    python3 scripts/query.py "payPal" --source-file features/payments.md

    # Top-K override (default 5)
    python3 scripts/query.py "redux vs context" --top-k 3

    # Batch mode: run 3 predefined test queries
    python3 scripts/query.py --test
"""

import argparse
import os
import re
import sys
from pathlib import Path

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import torch
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
COLLECTION_NAME = "proshop_chunks"
QDRANT_URL = "http://localhost:6333"
EMBEDDING_MODEL = "BAAI/bge-m3"

# Russian → English term map for cross-lingual query bridging.
# Covers tech terms and common question words in this project's domain.
_RU_EN = {
    # question words
    "какая": "which", "какие": "which", "какой": "which", "какую": "which",
    "что": "what", "как": "how", "где": "where", "когда": "when",
    "почему": "why", "зачем": "why", "сколько": "how many",
    "кто": "who",
    # tech / domain
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
    # verbs / modifiers
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
    # prepositions / glue (kept short to not dilute the vector)
    "во": "during", "время": "time",
}


def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[а-яА-ЯёЁ]", text))


def _ru_to_en_query(ru_query: str) -> str:
    """Word-by-word Russian→English replacement, keeping English/tech terms intact."""
    tokens = re.findall(r"\S+", ru_query)
    out = []
    for tok in tokens:
        lower = tok.lower().strip(".,!?;:")
        if lower in _RU_EN:
            out.append(_RU_EN[lower])
        elif _has_cyrillic(tok):
            # unmatched Russian word — drop it (noise for English embedding)
            continue
        else:
            out.append(tok)  # keep English / technical terms as-is
    return " ".join(out)


def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _build_qdrant_filter(filters: dict | None) -> Filter | None:
    if not filters:
        return None
    conditions = []
    if filters.get("type"):
        conditions.append(
            FieldCondition(key="type", match=MatchValue(value=filters["type"]))
        )
    if filters.get("source_file"):
        conditions.append(
            FieldCondition(
                key="source_file", match=MatchValue(value=filters["source_file"])
            )
        )
    return Filter(must=conditions) if conditions else None


def _point_to_hit(point) -> dict:
    p = point.payload
    return {
        "id": point.id,
        "score": point.score,
        "text": p.get("text", ""),
        "source_file": p.get("source_file", ""),
        "title": p.get("title", ""),
        "type": p.get("type", ""),
        "parent_headings": p.get("parent_headings", []),
        "chunk_index": p.get("chunk_index", 0),
    }


def search(
    query: str,
    model: SentenceTransformer,
    client: QdrantClient,
    top_k: int = 5,
    filters: dict | None = None,
) -> list[dict]:
    """Embed query and search Qdrant for top-K similar chunks.

    If the query contains Cyrillic, runs a parallel search with the
    English-translated version and merges via Reciprocal Rank Fusion.
    """
    qdrant_filter = _build_qdrant_filter(filters)

    # Decide which query strings to embed
    queries = [query]
    if _has_cyrillic(query):
        en_query = _ru_to_en_query(query)
        if en_query and en_query != query:
            queries.append(en_query)

    # Encode all queries in one batch (faster than separate calls)
    vectors = model.encode(queries, normalize_embeddings=True, show_progress_bar=False)

    # Run one search per query vector
    all_results: list[list] = []
    fetch_limit = top_k * 3  # over-fetch so RRF has enough candidates
    for vec in vectors:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vec.tolist(),
            limit=fetch_limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        all_results.append(results.points)

    if len(all_results) == 1:
        return [_point_to_hit(p) for p in all_results[0][:top_k]]

    # Reciprocal Rank Fusion: merge by rank position, not raw score.
    # RRF score = Σ 1/(k + rank_i)  — chunks ranked high by BOTH queries win.
    rrf_k = 60
    rrf_scores: dict[int, float] = {}
    hits_by_id: dict[int, dict] = {}

    for ranked_list in all_results:
        for rank, point in enumerate(ranked_list, 1):
            pid = point.id
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (rrf_k + rank)
            if pid not in hits_by_id or point.score > hits_by_id[pid]["score"]:
                hits_by_id[pid] = _point_to_hit(point)
                hits_by_id[pid]["score"] = point.score

    # Sort by RRF score, replace cosine score with it
    ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
    hits = []
    for pid in ranked_ids:
        hit = hits_by_id[pid]
        hit["rrf_score"] = rrf_scores[pid]
        hits.append(hit)
    return hits


def format_hit(hit: dict, idx: int, show_text: int = 200) -> str:
    text_preview = hit["text"][:show_text]
    if len(hit["text"]) > show_text:
        text_preview += "..."
    headings = " > ".join(hit["parent_headings"]) if hit["parent_headings"] else "-"
    score_str = f"cosine={hit['score']:.4f}"
    if "rrf_score" in hit:
        score_str += f"  rrf={hit['rrf_score']:.5f}"
    return (
        f"  #{idx}  {score_str}  type={hit['type']}  "
        f"source={hit['source_file']}  heading=[{headings}]\n"
        f"      \"{text_preview}\""
    )


def run_query(
    query: str,
    model: SentenceTransformer,
    client: QdrantClient,
    top_k: int = 5,
    filters: dict | None = None,
    label: str | None = None,
):
    if label:
        en_q = _ru_to_en_query(query) if _has_cyrillic(query) else None
        print(f"\n{'='*70}")
        print(f"QUERY:    {query}")
        if en_q:
            print(f"EN BRIDGE: {en_q}")
        print(f"LABEL:    {label}")
        if filters:
            print(f"FILTER:   {filters}")
        print(f"{'='*70}")
    else:
        print(f"\nQuery: \"{query}\"  top_k={top_k}  filters={filters}")

    hits = search(query, model, client, top_k=top_k, filters=filters)
    if not hits:
        print("  No results found.")
        return hits

    for i, hit in enumerate(hits, 1):
        print(format_hit(hit, i))
    return hits


def main():
    parser = argparse.ArgumentParser(description="Search proshop_mern RAG chunks")
    parser.add_argument("query", nargs="?", help="Search query text")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--type", dest="filter_type", help="Filter by chunk type")
    parser.add_argument(
        "--source-file", dest="filter_source", help="Filter by source_file"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run 3 predefined test queries"
    )
    args = parser.parse_args()

    if not args.query and not args.test:
        parser.print_help()
        sys.exit(1)

    client = QdrantClient(url=QDRANT_URL, timeout=30)
    print(f"Connected to Qdrant ({QDRANT_URL})")

    device = get_device()
    print(f"Loading {EMBEDDING_MODEL} on {device}...")
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print(f"Model ready\n")

    if args.test:
        run_query(
            "Какая БД используется в proshop_mern и почему именно она?",
            model,
            client,
            top_k=3,
            label="Q1: factual single-hop (expect: adrs/adr-001-mongodb...)",
        )

        run_query(
            "Какие фичи зависят от payment_stripe_v3?",
            model,
            client,
            top_k=3,
            label="Q2: multi-hop dependency (expect: features/payments.md or feature-flags-spec.md)",
        )

        run_query(
            "Что случилось во время последнего incident с checkout?",
            model,
            client,
            top_k=3,
            filters={"type": "incident"},
            label="Q3: filter by type=incident (expect: incidents/)",
        )
    else:
        filters = {}
        if args.filter_type:
            filters["type"] = args.filter_type
        if args.filter_source:
            filters["source_file"] = args.filter_source
        filters = filters or None

        run_query(args.query, model, client, top_k=args.top_k, filters=filters)


if __name__ == "__main__":
    main()
