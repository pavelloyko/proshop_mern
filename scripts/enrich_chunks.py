"""
Enrich chunk keywords and summary using Anthropic API.

Reads docs/chunks.jsonl, generates LLM-quality keywords and summary for each
chunk, writes back to docs/chunks.jsonl.

Requires ANTHROPIC_API_KEY env var.

Usage:
    ANTHROPIC_API_KEY=... python3 scripts/enrich_chunks.py [--batch-size 20] [--start 0]
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = ROOT / "docs" / "chunks.jsonl"

SYSTEM_PROMPT = """You are a metadata extraction assistant for a RAG (Retrieval-Augmented Generation) system.

Given a text chunk from a technical documentation corpus, extract:
1. keywords: 5-8 specific, searchable terms (technologies, components, API routes, file names, concepts)
2. summary: one sentence (max 200 chars) describing WHAT this chunk is about

Rules for keywords:
- Specific: "CheckoutSteps.js", "/api/products", "JWT Bearer token", "MongoDB aggregation pipeline"
- NOT generic: "team", "project", "data", "system", "use"
- 5-8 keywords, not fewer, not more

Rules for summary:
- One sentence, max 200 chars
- What the chunk is ABOUT (not just restating the heading)
- Example good: "The team chose MongoDB over PostgreSQL for its document model flexibility with variable product attributes."
- Example bad: "This section discusses the database."

Respond ONLY with valid JSON: {"keywords": ["kw1", "kw2", ...], "summary": "..."}"""


def load_chunks():
    chunks = []
    with open(CHUNKS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def save_chunks(chunks):
    with open(CHUNKS_FILE, 'w') as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')


def enrich_batch(chunks, start, batch_size, client):
    """Enrich a batch of chunks using the Anthropic API."""
    end = min(start + batch_size, len(chunks))
    batch = chunks[start:end]

    # Build a single prompt with multiple chunks
    parts = []
    for i, c in enumerate(batch):
        preview = c["text"]
        if len(preview) > 1500:
            preview = preview[:1500] + "..."
        parts.append(f"--- CHUNK {i} ---\n{preview}\n")

    prompt = "Extract keywords and summary for each chunk:\n\n" + "\n".join(parts)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Parse response - expect JSON array
        # Try to extract JSON from the response
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        results = json.loads(text)

        if isinstance(results, list):
            for i, r in enumerate(results):
                if i < len(batch):
                    if "keywords" in r:
                        batch[i]["metadata"]["keywords"] = r["keywords"]
                    if "summary" in r:
                        batch[i]["metadata"]["summary"] = r["summary"]
        elif isinstance(results, dict) and "keywords" in results:
            # Single result for single chunk
            batch[0]["metadata"]["keywords"] = results["keywords"]
            batch[0]["metadata"]["summary"] = results.get("summary", "")

        return True

    except Exception as e:
        print(f"  API error: {e}")
        return False


def enrich_one_by_one(chunks, start, batch_size, client):
    """Enrich chunks one by one (fallback if batch fails)."""
    end = min(start + batch_size, len(chunks))
    for i in range(start, end):
        c = chunks[i]
        preview = c["text"]
        if len(preview) > 2000:
            preview = preview[:2000] + "..."

        prompt = f"Extract keywords and summary for this chunk:\n\n{preview}"

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]

            result = json.loads(text)
            if "keywords" in result:
                c["metadata"]["keywords"] = result["keywords"]
            if "summary" in result:
                c["metadata"]["summary"] = result["summary"]

        except Exception as e:
            print(f"  Error on chunk {i}: {e}")
            continue

        if (i - start + 1) % 10 == 0:
            print(f"  Processed {i - start + 1}/{end - start}")
            save_chunks(chunks)

    return True


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY env var required")
        sys.exit(1)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except ImportError:
        print("Error: anthropic package required. pip install anthropic")
        sys.exit(1)

    batch_size = int(sys.argv[sys.argv.index("--batch-size") + 1]) if "--batch-size" in sys.argv else 5
    start = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0

    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks, enriching from index {start}, batch_size={batch_size}")

    # Process in batches of batch_size
    total = len(chunks)
    i = start
    while i < total:
        end = min(i + batch_size, total)
        print(f"Batch {i//batch_size + 1}: chunks {i}-{end-1}")

        # Try batch first, fall back to one-by-one
        if not enrich_batch(chunks, i, batch_size, client):
            print("  Batch failed, falling back to one-by-one")
            enrich_one_by_one(chunks, i, batch_size, client)

        save_chunks(chunks)
        i = end
        time.sleep(1)  # Rate limit courtesy

    print(f"\nDone. Enriched {total} chunks.")


if __name__ == "__main__":
    main()
