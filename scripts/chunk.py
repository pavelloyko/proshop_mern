"""
Markdown Chunker for proshop_mern RAG pipeline.

Reads docs/project-data/*.md, splits by markdown structure,
generates rich metadata, outputs docs/chunks.jsonl.

Strategy:
  1. Parse frontmatter -> type, title
  2. Split by ## (H2) sections
  3. Merge consecutive small sections up to ~400 tokens
  4. Only split further (H3 / paragraph / sentence) when section > 400 tokens
  5. Overlap 20% only when splitting mid-section

Usage:
  python3 scripts/chunk.py
"""

import json
import re
from pathlib import Path
from collections import Counter

# ── Config ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs" / "project-data"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "chunks.jsonl"
MAX_TOKENS = 400
OVERLAP_TOKENS = 80
CHARS_PER_TOKEN = 3.5

STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как",
    "а", "то", "всё", "она", "так", "его", "но", "да", "ты", "к",
    "у", "же", "вы", "за", "бы", "по", "только", "её", "мне", "было",
    "вот", "от", "меня", "ещё", "нет", "о", "из", "ему", "теперь",
    "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни",
    "быть", "был", "него", "до", "вас", "нибудь", "опять", "уж",
    "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может",
    "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя",
    "их", "чем", "была", "сам", "чтоб", "без", "будто", "чего",
    "раз", "тоже", "себе", "под", "будет", "ж", "тогда", "кто",
    "этот", "того", "потому", "этого", "какой", "совсем", "ним",
    "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее",
    "сейчас", "были", "куда", "зачем", "всех", "никогда", "можно",
    "при", "наконец", "два", "об", "другой", "хоть", "после", "над",
    "больше", "тот", "через", "эти", "нас", "про", "всего", "них",
    "какая", "много", "разве", "три", "эту", "моя", "впрочем", "хорошо",
    "свою", "этой", "перед", "иногда", "лучше", "чуть", "том", "нельзя",
    "такой", "им", "более", "всегда", "конечно", "всю", "между",
    "это", "весь", "который", "мочь", "свой",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "that", "this",
    "these", "those", "it", "its", "he", "she", "they", "them", "their",
    "what", "which", "who", "whom", "whose", "also", "about", "up",
}


def tok(text: str) -> int:
    return len(text) / CHARS_PER_TOKEN


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text
    body = text[m.end():]
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body


def extract_h1(text: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_keywords(text: str, n: int = 8) -> list[str]:
    clean = re.sub(r"[#*`\[\]()>|_\-]", " ", text)
    clean = re.sub(r"[^\w\sа-яА-ЯёЁ]", " ", clean)
    words = clean.lower().split()
    words = [w for w in words if len(w) > 2 and w not in STOP_WORDS]
    return [w for w, _ in Counter(words).most_common(n)]


def extract_summary(text: str) -> str:
    clean = text.strip().lstrip("#").strip()
    m = re.search(r"^(.+?[.!?])\s", clean)
    if m:
        s = m.group(1)
        return s[:200] + ("..." if len(s) > 200 else "")
    return clean[:200] + "..." if len(clean) > 200 else clean


def detect_language(text: str) -> str:
    cyrillic = len(re.findall(r"[а-яА-ЯёЁ]", text))
    latin = len(re.findall(r"[a-zA-Z]", text))
    return "ru" if cyrillic > latin else "en"


def split_by_heading(body: str, level: int) -> list[tuple[str, str]]:
    pattern = rf"^({'#' * level})\s+(.+)$"
    sections = []
    current_heading = ""
    current_lines: list[str] = []

    for line in body.splitlines():
        if re.match(pattern, line, re.MULTILINE):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            hm = re.match(pattern, line)
            current_heading = hm.group(2).strip() if hm else ""
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    return sections


def merge_sections(sections: list[tuple[str, str]], max_tokens: int) -> list[tuple[list[str], str]]:
    """Merge consecutive small H2 sections up to max_tokens.
    Returns [(parent_headings_list, merged_text)]."""
    merged: list[tuple[list[str], str]] = []
    buf_headings: list[str] = []
    buf_text = ""

    for heading, content in sections:
        if not content.strip():
            continue

        candidate = (buf_text + "\n\n## " + heading + "\n\n" + content).strip() if buf_text else content

        if tok(candidate) <= max_tokens:
            if heading:
                buf_headings.append(heading)
            buf_text = candidate
        else:
            # Flush current buffer
            if buf_text:
                merged.append((buf_headings[:], buf_text))
            # Start new buffer — but check if this single section is also too large
            if tok(content) > max_tokens:
                # Will be split later by split_large_section
                merged.append(([heading] if heading else [], content))
                buf_headings = []
                buf_text = ""
            else:
                buf_headings = [heading] if heading else []
                buf_text = content

    if buf_text:
        merged.append((buf_headings[:], buf_text))

    return merged


def split_large_text(text: str, max_tokens: int) -> list[str]:
    """Split by paragraphs, then sentences. Add overlap if split occurs."""
    if tok(text) <= max_tokens:
        return [text]

    paragraphs = re.split(r"\n\n+", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if tok(current + "\n\n" + para) <= max_tokens:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if tok(para) > max_tokens:
                chunks.extend(_split_sentences(para, max_tokens))
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks if chunks else [text]


def _split_sentences(text: str, max_tokens: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sent in sentences:
        if tok(current + " " + sent) <= max_tokens:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent

    if current:
        chunks.append(current)

    return chunks if chunks else [text]


def add_overlap(chunks: list[str], overlap_tokens: int) -> list[str]:
    if len(chunks) <= 1:
        return chunks
    overlapped = [chunks[0]]
    overlap_chars = int(overlap_tokens * CHARS_PER_TOKEN)
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-overlap_chars:]
        dot = tail.find(". ")
        if dot != -1 and dot < len(tail) // 2:
            tail = tail[dot + 2:]
        overlapped.append(tail + "\n\n" + chunks[i])
    return overlapped


def chunk_file(filepath: Path) -> list[dict]:
    text = filepath.read_text(encoding="utf-8")
    if not text.strip():
        return []

    frontmatter, body = parse_frontmatter(text)
    h1 = extract_h1(text) or frontmatter.get("title", filepath.stem)
    doc_type = frontmatter.get("type", _infer_type(filepath))
    lang = detect_language(text)
    source_file = filepath.name
    file_path = str(filepath.relative_to(PROJECT_ROOT))

    # Whole file fits in one chunk
    if tok(body) <= MAX_TOKENS:
        return [_make_chunk(body, source_file, file_path, doc_type, h1, [], lang, 0)]

    # Split by H2, then merge small consecutive sections
    h2_sections = split_by_heading(body, 2)
    merged = merge_sections(h2_sections, MAX_TOKENS)

    chunks = []
    idx = 0
    for headings, content in merged:
        if tok(content) <= MAX_TOKENS:
            chunks.append(_make_chunk(content, source_file, file_path, doc_type, h1, headings, lang, idx))
            idx += 1
        else:
            # Large section — split further
            parts = split_large_text(content, MAX_TOKENS)
            if len(parts) > 1:
                parts = add_overlap(parts, OVERLAP_TOKENS)
            for part in parts:
                chunks.append(_make_chunk(part, source_file, file_path, doc_type, h1, headings, lang, idx))
                idx += 1

    return chunks


def _make_chunk(text, source_file, file_path, doc_type, title, headings, lang, idx):
    return {
        "text": text.strip(),
        "metadata": {
            "source_file": source_file,
            "file_path": file_path,
            "type": doc_type,
            "title": title,
            "parent_headings": headings,
            "keywords": extract_keywords(text),
            "summary": extract_summary(text),
            "language": lang,
            "chunk_index": idx,
        },
    }


def _infer_type(filepath: Path) -> str:
    parts = filepath.parts
    if "adrs" in parts: return "adr"
    if "api" in parts: return "api"
    if "features" in parts: return "feature"
    if "pages" in parts: return "page"
    if "runbooks" in parts: return "runbook"
    if "incidents" in parts: return "incident"
    name = filepath.stem.lower()
    if "architecture" in name: return "architecture"
    if "glossary" in name: return "glossary"
    if "best-practices" in name: return "best-practice"
    if "dev-history" in name: return "dev-history"
    if "feature-flags" in name: return "feature-flag-spec"
    return "doc"


def main():
    all_chunks = []
    md_files = sorted(DOCS_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files in {DOCS_DIR}")

    for fp in md_files:
        file_chunks = chunk_file(fp)
        all_chunks.extend(file_chunks)
        print(f"  {fp.relative_to(DOCS_DIR)}: {len(file_chunks)} chunks")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nTotal: {len(all_chunks)} chunks -> {OUTPUT_FILE}")
    tokens = [tok(c["text"]) for c in all_chunks]
    print(f"Avg tokens: {sum(tokens)/len(tokens):.0f}")
    print(f"Min tokens: {min(tokens):.0f}")
    print(f"Max tokens: {max(tokens):.0f}")


if __name__ == "__main__":
    main()
