# Read Workflow

Read and inspect Confluence pages with smart status display. Shows sync state for our pages, previews for external pages.

## Input

User provides one of:
- Page ID: "прочитай 559218693"
- URL: "прочитай https://yourcompany.atlassian.net/wiki/spaces/SD/pages/559218693"
- Title/name: "прочитай ILT Event Viewer Designer Input"
- Feature reference: "что сейчас в Confluence по фиче 14"

## Algorithm

### 1. Resolve Page

| Input | Action |
|-------|--------|
| Page ID (numeric) | Direct `getConfluencePage` call |
| Confluence URL | Extract page ID from URL path segment, call `getConfluencePage` |
| Title or name | Search pages-registry by `title` or `feature_folder` first; if not found, CQL: `title ~ "keyword"` via `searchConfluenceUsingCql` |
| Feature reference ("фича 14") | Search pages-registry by `feature_folder` containing "14" |

If multiple matches found -> show list, ask user to pick.

### 2. Fetch Page

Call `getConfluencePage(cloudId, pageId, contentFormat: "markdown")`.

Expected response fields: body content, version number, title.

**Metadata availability:** Fields like `lastModifiedBy`, `lastModifiedDate`, `space`, `ancestors` may or may not be in the response depending on the MCP tool's implementation. If critical metadata is missing:
- **Fallback 1:** Use `searchConfluenceUsingCql` with `id = {pageId}` to get additional metadata
- **Fallback 2:** Use `fetchAtlassian` with page ARI if available
- **Fallback 3:** Show "metadata unavailable" and proceed with what we have

### 3. Smart Display

#### For OUR pages (found in pages-registry):

```
=== ILT Event Viewer - Designer Input ===
Space: SD | Page ID: 559218693
Version: 3 | Last modified: 2026-03-23 by the user
URL: https://yourcompany.atlassian.net/wiki/spaces/SD/pages/559218693/...
Local file: your-project/docs/.../ILT-Event-Viewer-Designer-Input.md
Jira: LT-2108 (epic: LT-2104)

Status: IN SYNC
  Local hash:  abc123
  Pushed hash: abc123
  Remote ver:  3 (pushed as v3)

Контент совпадает с локальным файлом.
```

**Status determination:**

| Status | Condition | Message |
|--------|-----------|---------|
| **IN SYNC** | local file hash == pushed hash AND remote version == pushed version | "Контент совпадает с локальным файлом." |
| **OUT OF SYNC** | local file hash != pushed hash | "Локальный файл изменился. Обновить страницу? (да / нет / показать diff)" |
| **REMOTE MODIFIED** | remote version > pushed version | "Кто-то редактировал страницу в Confluence. Показать diff? (да / нет)" |

Both OUT OF SYNC and REMOTE MODIFIED can be true simultaneously -> show both warnings.

To calculate local hash: read local file -> filter through banned_patterns -> MD5. Same algorithm as in publish-workflow.

#### For EXTERNAL pages (not in pages-registry):

```
=== Page Title ===
Space: SD | Page ID: 12345
Version: 7 | Last modified: 2026-03-20 by Casey
URL: https://...

Content preview (first ~500 chars):
  [preview text]

Показать полностью? (да / нет)
```

No sync status for external pages since we don't manage them.

### 4. Optional Diff

If user requests diff for our page:
1. Read local file, filter through banned_patterns, get clean local content
2. Get remote content (already fetched in Step 2, using `contentFormat: "markdown"`)
3. Compare and show added/removed/changed sections
4. If remote content is still XHTML/ADF despite requesting markdown, strip HTML tags for readable comparison

This diff is text-level comparison, not line-by-line git diff. Focus on showing meaningful content changes, not formatting noise.

### 5. Follow-up Actions

After showing page info, offer relevant actions:
- **OUT OF SYNC** -> "Обновить страницу? (да)" -> transition to publish-workflow UPDATE path
- **REMOTE MODIFIED** -> "Скачать remote версию? (да)" -> save remote content to local file
- **IN SYNC** -> no action needed
- **Any page** -> "Показать полный контент? / Показать diff? / Открыть в браузере?"

## Notes

- Always request `contentFormat: "markdown"` for readable output and proper diff comparison
- URL parsing: Confluence page URLs have format `.../pages/{pageId}/...` - extract the numeric segment
- Registry lookup by feature: match against `feature_folder` field (e.g., "14-ILT-Event-Viewer" matches "14")
