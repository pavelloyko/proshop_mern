# Chunking Specification — ProShop RAG Pipeline

## Source

`docs/project-data/` — 35 markdown files across 7 subdirectories.

## Output

`docs/chunks.jsonl` — one JSON object per line.

## Chunk Schema

```json
{
  "text": "heading + content of the chunk",
  "metadata": {
    "source_file": "adrs/adr-001-mongodb-vs-postgres.md",
    "file_path": "docs/project-data/adrs/adr-001-mongodb-vs-postgres.md",
    "title": "ADR-001: Use MongoDB (via Mongoose) as the Primary Database",
    "parent_headings": ["Context"],
    "type": "adr",
    "keywords": ["mongodb", "mongoose", "database selection", "postgresql", "document store", "schema flexibility"],
    "summary": "The team chose MongoDB over PostgreSQL for its schema flexibility with variable product attributes.",
    "language": "en",
    "chunk_index": 0
  }
}
```

## Field Definitions

| Field | Source | Rules |
|---|---|---|
| `text` | Chunk content | Prepend heading context (H2/H3 line) so the chunk is self-contained |
| `source_file` | Relative path from `docs/project-data/` | e.g. `features/checkout.md` |
| `file_path` | Path from project root | e.g. `docs/project-data/features/checkout.md` |
| `title` | H1 of the file | First `# ...` line |
| `parent_headings` | H2/H3 breadcrumb | e.g. `["System Overview", "Actors"]` — empty `[]` for content directly under H1 |
| `type` | From directory name | `adr`, `api`, `feature`, `runbook`, `incident`, `page`, `doc` (root-level files) |
| `keywords` | LLM-generated | 5-8 specific, searchable terms (technologies, components, routes, file names, concepts) |
| `summary` | LLM-generated | One sentence, max 200 chars. What this chunk is ABOUT, not a heading restatement |
| `language` | Detected from text | `en`, `ru`, or `mixed` |
| `chunk_index` | 0-based counter | Position within the source file |

## Type Mapping

| Directory | type |
|---|---|
| `adrs/` | `adr` |
| `api/` | `api` |
| `features/` | `feature` |
| `runbooks/` | `runbook` |
| `incidents/` | `incident` |
| `pages/` | `page` |
| (root files) | `doc` |

## Chunking Rules

### Size targets

- **Target:** 400-500 tokens
- **Max:** 600 tokens (hard split if exceeded)
- **Min:** no minimum — small sections stay as separate chunks

### Token estimation

- English: characters / 4
- Russian: characters / 3
- Mixed: characters / 3.5

### Splitting algorithm

1. Parse markdown into sections by `##` and `###` headings
2. Each section (content under an H2 or H3) is a chunk candidate
3. If section <= 600 tokens → one chunk, include heading line in text
4. If section > 600 tokens → split at paragraph boundaries (`\n\n`), keep ~50 token overlap between split parts
5. Tables and code blocks are atomic — never split inside them
6. Very small files (e.g. pages/*.md at 35-50 lines) → entire file is one chunk

### Heading handling

- Always prepend the heading hierarchy to chunk text so it reads coherently:
  ```
  ## Context
  <content>
  ```
- For subsections, include the parent heading context:
  ```
  ## Consequences
  ### Positive
  <content>
  ```

## Keywords Quality Criteria

Good keywords:
- Specific: `CheckoutSteps.js`, `/api/products`, `JWT Bearer token`, `MongoDB aggregation pipeline`
- Searchable: terms a developer would search for
- Diverse: mix of technologies, components, concepts

Bad keywords (avoid):
- Generic: `team`, `project`, `data`, `system`, `use`, `also`
- Stopwords or common words
- Too many (> 8) or too few (< 3)

## Summary Quality Criteria

Good: "The team chose MongoDB over PostgreSQL for its document model flexibility with variable product attributes."
Bad: "This section discusses the database." (too vague)
Bad: "ADR-001: Use MongoDB (via Mongoose) as the Primary Database Status: Accepted Date: 2023-01-10..." (just repeated text)

## Language Detection

- Text contains Cyrillic characters and Latin → `mixed`
- Only Cyrillic → `ru`
- Only Latin → `en`

## File Groups for Parallel Processing

| Group | Files | Agent |
|---|---|---|
| 1 | architecture.md, best-practices.md | large-1 |
| 2 | feature-flags-spec.md, dev-history.md, glossary.md, features-analysis-ru.md | large-2 |
| 3 | features/*.md (6 files) | features |
| 4 | api/*.md (5 files), runbooks/*.md (6 files) | api-runbooks |
| 5 | pages/*.md (16 files), adrs/*.md (5 files), incidents/*.md (3 files) | pages-adrs-incidents |
