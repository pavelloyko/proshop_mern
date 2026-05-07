"""
Vectorize chunks.jsonl with BGE-M3 and upsert into Qdrant.

Reads docs/chunks.jsonl, encodes each chunk's text with BAAI/bge-m3,
and upserts vectors + payload into a Qdrant collection.

Usage:
    python3 scripts/vectorize.py [--batch-size 8] [--recreate] [--resume] [--device auto]
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import torch
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


def parse_args():
    args = sys.argv[1:]
    def get_val(flag, default):
        return type(default)(args[args.index(flag) + 1]) if flag in args else default

    return {
        "batch_size": get_val("--batch-size", 8),
        "recreate": "--recreate" in args,
        "resume": "--resume" in args,
        "device": get_val("--device", "auto"),
    }


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_payload(chunk: dict) -> dict:
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


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_existing_ids(client: QdrantClient, total: int) -> set[int]:
    existing = set()
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        for r in records:
            existing.add(r.id)
        if offset is None:
            break
    return existing


def main():
    opts = parse_args()
    batch_size = opts["batch_size"]

    chunks = load_chunks(CHUNKS_FILE)
    total = len(chunks)
    print(f"Loaded {total} chunks from {CHUNKS_FILE.name}")

    client = QdrantClient(url=QDRANT_URL, timeout=30)
    print(f"Connected to Qdrant at {QDRANT_URL}")

    # Determine skip set for resume
    skip_ids: set[int] = set()
    collection_exists = COLLECTION_NAME in [c.name for c in client.get_collections().collections]

    if opts["recreate"]:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"Recreated collection '{COLLECTION_NAME}'")
        collection_exists = True
    elif not collection_exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION_NAME}'")
    elif opts["resume"]:
        skip_ids = get_existing_ids(client, total)
        print(f"Resume mode: skipping {len(skip_ids)} already-uploaded chunks")
    else:
        print(f"Collection '{COLLECTION_NAME}' exists, will upsert (overwrite)")

    # Pick device
    device = pick_device(opts["device"])
    print(f"Loading {EMBEDDING_MODEL} on {device}...")
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print(f"Model ready, dimension={model.get_sentence_embedding_dimension()}")

    # Adjust batch size for device
    if device == "mps" and batch_size > 8:
        print(f"MPS detected: reducing batch_size {batch_size} -> 8 to avoid OOM")
        batch_size = 8

    # Process in batches
    processed = 0
    skipped = 0
    errors = 0
    start_time = time.time()
    use_mps = device == "mps"
    fell_back_to_cpu = False

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]

        # Skip chunks already in collection
        batch_ids = [i + j for j in range(len(batch))]
        if skip_ids and all(bid in skip_ids for bid in batch_ids):
            skipped += len(batch)
            continue

        texts = [c["text"] for c in batch]
        try:
            vectors = model.encode(
                texts,
                show_progress_bar=False,
                normalize_embeddings=True,
                batch_size=len(batch),
            )

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

        except RuntimeError as e:
            if "MPS" in str(e) or "out of memory" in str(e):
                if use_mps and not fell_back_to_cpu:
                    print(f"\n  MPS OOM at batch {i}, falling back to CPU...")
                    del model
                    torch.mps.empty_cache()
                    device = "cpu"
                    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
                    fell_back_to_cpu = True
                    # Retry this batch on CPU
                    vectors = model.encode(
                        texts,
                        show_progress_bar=False,
                        normalize_embeddings=True,
                    )
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
                else:
                    errors += len(batch)
                    print(f"  OOM ERROR on batch {i}-{i+len(batch)-1}: {e}")
                    continue
            else:
                errors += len(batch)
                print(f"  ERROR on batch {i}-{i+len(batch)-1}: {e}")
                continue
        except Exception as e:
            errors += len(batch)
            print(f"  ERROR on batch {i}-{i+len(batch)-1}: {e}")
            continue

        elapsed = time.time() - start_time
        done = processed + skipped + errors
        rate = processed / elapsed if elapsed > 0 else 0
        remaining = (total - done) / rate if rate > 0 else 0
        print(
            f"  [{done}/{total}] "
            f"{processed} upserted, {skipped} skipped, {errors} errors | "
            f"{rate:.1f} chunks/s, ~{remaining:.0f}s left"
        )

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.1f}s: {processed} upserted, {skipped} skipped, {errors} errors")

    info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}': {info.points_count} points, status={info.status}")


if __name__ == "__main__":
    main()
