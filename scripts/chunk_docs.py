"""
Markdown chunker for RAG pipeline.

Parses docs/project-data/ markdown files, splits by heading hierarchy,
generates metadata (keywords + summary via heuristics), outputs JSONL.

Usage:
    python3 scripts/chunk_docs.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "docs" / "project-data"
OUTPUT = ROOT / "docs" / "chunks.jsonl"

# --- Token estimation ---
def estimate_tokens(text: str) -> int:
    """Rough token count: chars/4 for English, chars/3 for Cyrillic-heavy text."""
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    total = len(text)
    if total == 0:
        return 0
    ratio = cyrillic / total
    if ratio > 0.3:
        return total // 3
    return total // 4


# --- Language detection ---
def detect_language(text: str) -> str:
    has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', text))
    has_latin = bool(re.search(r'[a-zA-Z]', text))
    if has_cyrillic and has_latin:
        return "mixed"
    if has_cyrillic:
        return "ru"
    return "en"


# --- Type from directory ---
def get_type(source_file: str) -> str:
    parts = source_file.split("/")
    if len(parts) > 1:
        dir_map = {
            "adrs": "adr", "api": "api", "features": "feature",
            "runbooks": "runbook", "incidents": "incident", "pages": "page"
        }
        return dir_map.get(parts[0], "doc")
    return "doc"


# --- Markdown parsing ---
HEADING_RE = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


def parse_sections(text: str) -> list[dict]:
    """Parse markdown into sections by ## and ### headings.
    Returns list of {heading: str, level: int, content: str}."""
    lines = text.split('\n')
    sections = []
    current = {"heading": "", "level": 0, "content_lines": []}

    # First pass: collect everything before first ## as section with heading from H1
    found_h2 = False
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()

            if level == 1:
                # H1 — just skip, we store it separately as title
                continue

            if level <= 3:
                # Save previous section
                if current["content_lines"]:
                    sections.append({
                        "heading": current["heading"],
                        "level": current["level"],
                        "content": '\n'.join(current["content_lines"]).strip()
                    })
                current = {"heading": heading_text, "level": level, "content_lines": [line]}
                found_h2 = True
                continue

        current["content_lines"].append(line)

    # Don't forget last section
    if current["content_lines"]:
        content = '\n'.join(current["content_lines"]).strip()
        if content:
            sections.append({
                "heading": current["heading"],
                "level": current["level"],
                "content": content
            })

    return sections


def get_parent_headings(heading: str, level: int, heading_stack: list) -> list[str]:
    """Build breadcrumb from heading stack."""
    if level == 2:
        return [heading] if heading else []
    if level == 3:
        # Find parent H2
        for h, l in reversed(heading_stack):
            if l == 2:
                return [h, heading]
        return [heading]
    return [heading] if heading else []


def split_large_section(section_text: str, max_tokens: int = 600) -> list[str]:
    """Split a large section at paragraph boundaries."""
    paragraphs = re.split(r'\n\n+', section_text)
    chunks = []
    current = ""

    for para in paragraphs:
        if not para.strip():
            continue
        candidate = (current + "\n\n" + para).strip() if current else para
        if estimate_tokens(candidate) <= max_tokens:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If single paragraph exceeds max, keep it whole (atomic)
            current = para

    if current:
        chunks.append(current)

    return chunks if chunks else [section_text]


# --- Keyword extraction ---
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most", "other",
    "some", "such", "no", "only", "own", "same", "than", "too", "very",
    "just", "because", "if", "when", "where", "how", "what", "which", "who",
    "whom", "this", "that", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their", "also", "about", "up", "here", "there", "where", "why",
    "while", "since", "until", "although", "though", "however", "therefore",
    "thus", "hence", "well", "example", "see", "like", "new", "one", "two",
    "first", "second", "using", "based", "using",
    # Russian stop words
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а",
    "то", "всё", "она", "так", "его", "но", "да", "ты", "к", "у", "же",
    "вы", "за", "бы", "по", "только", "её", "мне", "было", "вот", "от",
    "меня", "ещё", "нет", "о", "из", "ему", "теперь", "когда", "даже",
    "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был", "него",
    "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом",
    "себя", "ничего", "ей", "может", "они", "тут", "где", "есть", "надо",
    "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без",
    "будто", "чего", "раз", "тоже", "себе", "под", "будет", "ж", "тогда",
    "кто", "этот", "того", "потому", "этого", "какой", "совсем", "ним",
    "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "сейчас",
    "были", "куда", "зачем", "всех", "никогда", "можно", "при", "наконец",
    "два", "об", "другой", "хоть", "после", "над", "больше", "тот", "через",
    "эти", "нас", "про", "всего", "них", "какая", "много", "разве", "три",
    "эту", "моя", "впрочем", "хорошо", "свою", "этой", "перед", "иногда",
    "лучше", "чуть", "том", "нельзя", "такой", "им", "более", "всегда",
    "конечно", "всю", "между",
}


def extract_keywords(text: str, heading: str) -> list[str]:
    """Extract 5-8 keywords from text using frequency + heading terms."""
    # Combine heading and content
    combined = heading + " " + text

    # Extract technical terms: CamelCase, dot.separated, /api/routes, file.js
    tech_terms = re.findall(
        r'(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+'
        r'|\b[A-Z]{2,}\b'
        r'|\b\w+\.\w+(?:\.\w+)*\b'
        r'|/api/\w+[\w/]*'
        r'|\w+\.(js|jsx|ts|tsx|py|json|md|css|sql)\b'
        r'|\b[A-Z_]{3,}\b)',
        combined
    )

    # Extract regular words
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', combined.lower())

    # Count frequencies, excluding stop words
    freq = {}
    for w in words:
        if w not in STOP_WORDS and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1

    # Boost heading words
    heading_words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', heading.lower())
    for hw in heading_words:
        if hw in freq:
            freq[hw] = freq[hw] + 5

    # Combine tech terms (unique, high priority) with frequency-based words
    keywords = []

    # Add unique tech terms first
    seen = set()
    for tt in tech_terms:
        tt_lower = tt.lower()
        if tt_lower not in seen and tt_lower not in STOP_WORDS and tt.strip():
            keywords.append(tt)
            seen.add(tt_lower)

    # Sort remaining by frequency
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    for word, count in sorted_words:
        if word not in seen and len(keywords) < 8:
            keywords.append(word)
            seen.add(word)

    return [k for k in keywords[:8] if k and k.strip()]


def extract_summary(text: str) -> str:
    """Extract first meaningful sentence as summary."""
    # Remove markdown formatting for cleaner extraction
    clean = re.sub(r'#{1,6}\s+', '', text)
    clean = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', clean)
    clean = re.sub(r'`([^`]+)`', r'\1', clean)
    clean = clean.strip()

    # Find first sentence (ends with . ! ? followed by space or end)
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and len(s) < 250:
            return s

    # Fallback: first 150 chars
    if len(clean) > 150:
        return clean[:147] + "..."
    return clean


# --- Section merging ---
def group_sections_by_h2(sections: list[dict]) -> list[list[dict]]:
    """Group consecutive sections under the same H2 parent.
    Each group starts at an H2 section. H3 subsections stay with their H2."""
    groups = []
    current_group = []

    for sec in sections:
        if sec["level"] == 2 and current_group:
            groups.append(current_group)
            current_group = [sec]
        else:
            current_group.append(sec)

    if current_group:
        groups.append(current_group)

    return groups


def merge_sections(sections: list[dict], max_tokens: int = 600) -> list[dict]:
    """Merge consecutive small sections into larger chunks.
    Never cross H2 boundaries. Merge H3 subsections within the same H2."""
    groups = group_sections_by_h2(sections)

    # Merge orphan pre-H2 content with first real H2 group
    if groups and groups[0] and all(s["level"] != 2 for s in groups[0]):
        if len(groups) > 1:
            groups[0].extend(groups[1])
            groups = [groups[0]] + groups[2:]

    merged = []
    for group in groups:
        # Calculate total tokens for the group
        combined_text = "\n\n".join(s["content"] for s in group if s["content"].strip())
        total_tokens = estimate_tokens(combined_text)

        if total_tokens <= max_tokens:
            # Entire group fits in one chunk
            h2_heading = next((s["heading"] for s in group if s["level"] == 2), "")
            h3_headings = [s["heading"] for s in group if s["level"] == 3 and s["heading"]]
            parent = []
            if h2_heading:
                parent.append(h2_heading)
            parent.extend(h3_headings)

            merged.append({
                "heading": h2_heading or (group[0]["heading"] if group else ""),
                "level": 2 if h2_heading else group[0]["level"] if group else 0,
                "content": combined_text,
                "parent_headings": parent,
            })
        else:
            # Group too large — merge subsections greedily
            current_text = ""
            current_headings = []
            h2_heading = next((s["heading"] for s in group if s["level"] == 2), "")

            for sec in group:
                candidate = (current_text + "\n\n" + sec["content"]).strip() if current_text else sec["content"]
                if estimate_tokens(candidate) <= max_tokens:
                    current_text = candidate
                    if sec["heading"] and sec["heading"] != h2_heading:
                        current_headings.append(sec["heading"])
                else:
                    # Flush current
                    if current_text:
                        parent = [h2_heading] if h2_heading else []
                        parent.extend(current_headings)
                        merged.append({
                            "heading": h2_heading or current_headings[0] if current_headings else "",
                            "level": 2,
                            "content": current_text,
                            "parent_headings": parent,
                        })
                    current_text = sec["content"]
                    current_headings = [sec["heading"]] if sec["heading"] and sec["heading"] != h2_heading else []

            if current_text:
                parent = [h2_heading] if h2_heading else []
                parent.extend(current_headings)
                merged.append({
                    "heading": h2_heading or current_headings[0] if current_headings else "",
                    "level": 2,
                    "content": current_text,
                    "parent_headings": parent,
                })

    return merged


# --- Main processing ---
def process_file(file_path: Path) -> list[dict]:
    """Process a single markdown file into chunks."""
    relative = file_path.relative_to(SOURCE_DIR)
    source_file = str(relative)
    file_path_str = f"docs/project-data/{source_file}"

    text = file_path.read_text(encoding='utf-8')
    if not text.strip():
        return []

    # Extract title from H1
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    # Strip H1 line for processing
    body = re.sub(r'^#\s+.+$', '', text, count=1, flags=re.MULTILINE).strip()
    body_tokens = estimate_tokens(body)

    # Small file → one chunk (threshold 800 covers most page/screen docs)
    if body_tokens <= 800:
        return [make_chunk(body, source_file, file_path_str, title, [], 0)]

    # Parse sections and merge small ones
    sections = parse_sections(text)
    merged = merge_sections(sections, 600)

    chunks = []
    for m in merged:
        content = m["content"].strip()
        if not content:
            continue

        parent_headings = m.get("parent_headings", [])
        if not parent_headings and m["heading"]:
            parent_headings = [m["heading"]]

        tokens = estimate_tokens(content)
        if tokens <= 650:
            chunks.append(make_chunk(
                content, source_file, file_path_str, title,
                parent_headings, len(chunks)
            ))
        else:
            parts = split_large_section(content, 600)
            for part in parts:
                chunks.append(make_chunk(
                    part, source_file, file_path_str, title,
                    parent_headings, len(chunks)
                ))

    # Post-process: merge tiny chunks (< 40 tokens) with next chunk
    merged_chunks = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if c is None:
            i += 1
            continue
        while (estimate_tokens(c["text"]) < 40 and i + 1 < len(chunks)):
            i += 1
            next_c = chunks[i]
            if next_c is None:
                break
            c["text"] = c["text"] + "\n\n" + next_c["text"]
            c["metadata"]["keywords"] = extract_keywords(
                c["text"], c["metadata"]["parent_headings"][-1] if c["metadata"]["parent_headings"] else ""
            )
            c["metadata"]["summary"] = extract_summary(c["text"])
        merged_chunks.append(c)
        i += 1

    # Re-index
    for idx, c in enumerate(merged_chunks):
        c["metadata"]["chunk_index"] = idx

    # Fallback
    if not merged_chunks and body:
        merged_chunks.append(make_chunk(body, source_file, file_path_str, title, [], 0))

    return merged_chunks


def make_chunk(text: str, source_file: str, file_path: str, title: str,
               parent_headings: list[str], chunk_index: int) -> dict:
    text = text.strip()
    if not text:
        return None

    heading = parent_headings[-1] if parent_headings else ""
    return {
        "text": text,
        "metadata": {
            "source_file": source_file,
            "file_path": file_path,
            "title": title,
            "parent_headings": parent_headings,
            "type": get_type(source_file),
            "keywords": extract_keywords(text, heading),
            "summary": extract_summary(text),
            "language": detect_language(text),
            "chunk_index": chunk_index,
        }
    }


def main():
    if not SOURCE_DIR.exists():
        print(f"Source directory not found: {SOURCE_DIR}")
        sys.exit(1)

    # Collect all markdown files
    md_files = sorted(SOURCE_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files in {SOURCE_DIR}")

    all_chunks = []
    for f in md_files:
        chunks = process_file(f)
        valid = [c for c in chunks if c is not None]
        all_chunks.extend(valid)
        rel = f.relative_to(SOURCE_DIR)
        print(f"  {rel}: {len(valid)} chunks")

    # Stats
    types = {}
    langs = {}
    files = set()
    token_counts = []
    for c in all_chunks:
        m = c["metadata"]
        types[m.get("type", "?")] = types.get(m.get("type", "?"), 0) + 1
        langs[m.get("language", "?")] = langs.get(m.get("language", "?"), 0) + 1
        files.add(m.get("source_file", "?"))
        token_counts.append(estimate_tokens(c["text"]))

    print(f"\n--- Stats ---")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Source files: {len(files)}")
    print(f"By type: {json.dumps(types, indent=2)}")
    print(f"By language: {json.dumps(langs, indent=2)}")
    if token_counts:
        print(f"Token range: {min(token_counts)}-{max(token_counts)} (avg {sum(token_counts)//len(token_counts)})")

    # Write output
    OUTPUT.write_text("")
    with open(OUTPUT, "a") as out:
        for chunk in all_chunks:
            out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nWritten to {OUTPUT} ({len(all_chunks)} lines)")


if __name__ == "__main__":
    main()
