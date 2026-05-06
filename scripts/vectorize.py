"""
Vectorize chunks.jsonl with BGE-M3 and upsert into Qdrant.

Reads docs/chunks.jsonl, encodes each chunk's text with BAAI/bge-m3,
and upserts vectors + payload into a Qdrant collection.

Usage:
    python3 scripts/vectorize.py [--batch-size 32] [--recreate]
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = ROOT / "docs" / "chunks.jsonl"
COLLECTION_NAME = "proshop_chunks"
QDRANT_URL = "http://localhost:6333"
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_payload(chunk: dict) -> dict:
    """Extract Qdrant payload from chunk metadata."""
    meta = chunk.get("metadata", {})
    return {
        "text": chunk["text"],
        "source_file": meta.get("source_file", ""),
        "file_path": meta.get("file_path", ""),
        "title": meta.get("title", ""),
        "parent_headings": meta.get("parent_headings", []),
        "type": meta.get("type", ""),
        "keywords": meta.get("keywords", []),
        "summary": meta.get("summary", ""),
        "language": meta.get("language", "en"),
        "chunk_index": meta.get("chunk_index", 0),
    }


def main():
    batch_size = int(sys.argv[sys.argv.index("--batch-size") + 1]) if "--batch-size" in sys.argv else 32
    recreate = "--recreate" in sys.argv

    # Load chunks
    chunks = load_chunks(CHUNKS_FILE)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE.name}")

    # Connect to Qdrant
    client = QdrantClient(url=QDRANT_URL, timeout=30)
    print(f"Connected to Qdrant at {QDRANT_URL}")

    # Create or recreate collection
    if recreate:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"Recreated collection '{COLLECTION_NAME}'")
    else:
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            print(f"Created collection '{COLLECTION_NAME}'")
        else:
            print(f"Collection '{COLLECTION_NAME}' already exists, appending")

    # Load embedding model
    print(f"Loading {EMBEDDING_MODEL}...")
    device = "cpu"
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print(f"Model ready, dimension={model.get_sentence_embedding_dimension()}")

    # Process in batches
    total = len(chunks)
    processed = 0
    errors = 0
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        try:
            vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

            points = []
            for j, chunk in enumerate(batch):
                points.append(
                    PointStruct(
                        id=i + j,
                        vector=vectors[j].tolist(),
                        payload=build_payload(chunk),
                    )
                )

            client.upsert(collection_name=COLLECTION_NAME, points=points)
            processed += len(batch)
        except Exception as e:
            errors += len(batch)
            print(f"  ERROR on batch {i}-{i+len(batch)-1}: {e}")
            continue

        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        remaining = (total - processed - errors) / rate if rate > 0 else 0
        print(
            f"  [{processed + errors}/{total}] "
            f"{processed} upserted, {errors} errors | "
            f"{rate:.1f} chunks/s, ~{remaining:.0f}s remaining"
        )

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.1f}s: {processed} upserted, {errors} errors")

    # Verify
    info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}': {info.points_count} points, status={info.status}")


if __name__ == "__main__":
    main()
