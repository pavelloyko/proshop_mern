"""
Combine per-group JSONL chunk files into a single docs/chunks.jsonl.
Validates schema and reports stats.

Usage:
    python3 scripts/combine_chunks.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT / "scripts" / "tmp"
OUTPUT = ROOT / "docs" / "chunks.jsonl"

GROUP_FILES = sorted(TMP_DIR.glob("chunks_group*.jsonl"))

REQUIRED_FIELDS = {
    "text": str,
    "metadata": dict,
}
REQUIRED_META = {
    "source_file": str,
    "file_path": str,
    "title": str,
    "parent_headings": list,
    "type": str,
    "keywords": list,
    "summary": str,
    "language": str,
    "chunk_index": int,
}

VALID_TYPES = {"adr", "api", "feature", "runbook", "incident", "page", "doc"}
VALID_LANGS = {"en", "ru", "mixed"}


def validate_chunk(chunk: dict, line_num: int, file_name: str) -> list[str]:
    errors = []
    for field, ftype in REQUIRED_FIELDS.items():
        if field not in chunk:
            errors.append(f"missing field '{field}'")
        elif not isinstance(chunk[field], ftype):
            errors.append(f"'{field}' should be {ftype.__name__}, got {type(chunk[field]).__name__}")

    if "metadata" in chunk and isinstance(chunk["metadata"], dict):
        meta = chunk["metadata"]
        for field, ftype in REQUIRED_META.items():
            if field not in meta:
                errors.append(f"metadata missing '{field}'")
            elif not isinstance(meta[field], ftype):
                errors.append(f"metadata '{field}' should be {ftype.__name__}")

        if "type" in meta and meta["type"] not in VALID_TYPES:
            errors.append(f"invalid type '{meta['type']}'")
        if "language" in meta and meta["language"] not in VALID_LANGS:
            errors.append(f"invalid language '{meta['language']}'")
        if "keywords" in meta and isinstance(meta["keywords"], list):
            if len(meta["keywords"]) < 3:
                errors.append(f"too few keywords ({len(meta['keywords'])})")
            if len(meta["keywords"]) > 10:
                errors.append(f"too many keywords ({len(meta['keywords'])})")
        if "summary" in meta and isinstance(meta["summary"], str):
            if len(meta["summary"]) > 300:
                errors.append(f"summary too long ({len(meta['summary'])} chars)")

    if not chunk.get("text", "").strip():
        errors.append("empty text")

    return errors


def main():
    if not GROUP_FILES:
        print(f"No chunk files found in {TMP_DIR}")
        sys.exit(1)

    print(f"Found {len(GROUP_FILES)} group files:")
    all_chunks = []
    total_errors = 0
    chunks_with_errors = 0

    for gf in GROUP_FILES:
        lines = gf.read_text().strip().split("\n")
        count = 0
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ERROR {gf.name} line {i}: invalid JSON: {e}")
                total_errors += 1
                continue

            errors = validate_chunk(chunk, i, gf.name)
            if errors:
                print(f"  WARN {gf.name} line {i}: {'; '.join(errors)}")
                total_errors += len(errors)
                chunks_with_errors += 1

            all_chunks.append(chunk)
            count += 1
        print(f"  {gf.name}: {count} chunks")

    print(f"\nTotal: {len(all_chunks)} chunks, {total_errors} errors in {chunks_with_errors} chunks")

    # Stats
    types = {}
    langs = {}
    files = set()
    for c in all_chunks:
        m = c.get("metadata", {})
        t = m.get("type", "?")
        types[t] = types.get(t, 0) + 1
        l = m.get("language", "?")
        langs[l] = langs.get(l, 0) + 1
        files.add(m.get("source_file", "?"))

    print(f"\nBy type: {json.dumps(types, indent=2)}")
    print(f"By language: {json.dumps(langs, indent=2)}")
    print(f"Source files: {len(files)}")

    # Write output
    OUTPUT.write_text("")
    with open(OUTPUT, "a") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nWritten to {OUTPUT} ({len(all_chunks)} lines)")


if __name__ == "__main__":
    main()
