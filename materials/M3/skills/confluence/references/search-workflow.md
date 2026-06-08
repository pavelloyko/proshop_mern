# Search Workflow

Search Confluence content using CQL (Confluence Query Language) with fulltext, title, and filtered queries.

## Input

User describes what they're looking for:
- "Найди в Confluence всё про ILT Waitlist"
- "Какие страницы есть в SD space?"
- "Где упоминается timezone handling?"
- "Покажи все Design Documents"
- "Найди в SD всё про calendar за последний месяц"

## Algorithm

### 1. Parse Search Intent

| Input Pattern | Strategy |
|---------------|----------|
| Keyword or phrase | Fulltext CQL: `text ~ "keyword"` |
| "по заголовку" / explicit title search | CQL: `title ~ "keyword"` |
| Space listing ("что есть в SD") | `getPagesInConfluenceSpace(cloudId, spaceId)` |
| Children of page ("покажи все Design Documents") | `getConfluencePageDescendants(cloudId, pageId)` - resolve page from pages-registry or by title |
| Space + keyword | `space = "SD" AND text ~ "keyword"` |
| Date mentioned ("за последний месяц") | Add `AND lastModified >= "YYYY-MM-DD"` |

If ambiguous -> ask: "Искать по заголовкам или по содержимому страниц?"

### 2. Build CQL

**Default filters** (always apply unless user says otherwise):
- `type = "page"` - exclude blogposts, comments, attachments
- Space from user context, or `default_space` from `.confluence/config.yaml` if not specified

**Composable filters** (add based on user input):
- `space = "KEY"` - specific space
- `text ~ "keyword"` - fulltext content search
- `title ~ "keyword"` - title-only search
- `ancestor = PAGE_ID` - within page tree (e.g., all under "Design Documents")
- `label = "label"` - by Confluence label
- `lastModified >= "YYYY-MM-DD"` - date filter
- `creator = "accountId"` - by author (if needed)

**Example built CQL:**
```
type = "page" AND space = "SD" AND text ~ "timezone" AND lastModified >= "2026-03-01"
```

### 3. Execute Search

Use `searchConfluenceUsingCql(cloudId, cql, limit)`:
- Default limit: 20 results
- If results exceed limit -> inform: "Найдено {total} результатов, показываю первые 20. Уточнить запрос или показать больше?"

For space listing: use `getPagesInConfluenceSpace(cloudId, spaceId)` instead of CQL.
For page children: use `getConfluencePageDescendants(cloudId, pageId)`.

### 4. Display Results

```
Поиск: text ~ "timezone" in space SD
Найдено: 3 результата

| # | Title                              | Space | Modified   | Status          |
|---|------------------------------------|-------|------------|-----------------|
| 1 | ILT Event Viewer - Designer Input  | SD    | 2026-03-23 | OURS (registry) |
| 2 | Timezone Handling Guidelines        | SD    | 2026-02-15 | external        |
| 3 | ILT Calendar Page - Designer Input | SD    | 2026-03-23 | OURS (registry) |

Прочитать страницу? (номер / уточнить запрос / нет)
```

**Status column:**
- **OURS (registry)** - page exists in `.confluence/pages-registry.yaml` (we created/manage it)
- **external** - not in our registry (created by someone else or outside this skill)

Cross-reference each result's page ID against pages-registry to determine status.

### 5. Follow-up Actions

| User Response | Action |
|--------------|--------|
| Number (e.g., "1") | Transition to Read workflow for that page |
| "уточнить" / "refine" | Ask for additional filters, rebuild CQL |
| "показать больше" / "more" | Re-run with higher limit or next page of results |
| "нет" / "done" | End search |

The transition to Read workflow is seamless - pass the page ID from the search result directly.

## Search Tips

These are patterns to recognize in user input and translate to CQL:

| User Says | CQL Translation |
|-----------|----------------|
| "всё про X" / "everything about X" | `text ~ "X"` |
| "страницы с названием X" / "pages titled X" | `title ~ "X"` |
| "за последнюю неделю" / "last week" | `lastModified >= "YYYY-MM-DD"` (calculate date) |
| "за последний месяц" / "last month" | `lastModified >= "YYYY-MM-DD"` (calculate date) |
| "в SD" / "in SD space" | `space = "SD"` |
| "под Design Documents" / "under Design Documents" | `ancestor = 559710210` (look up in registry) |
| "мои страницы" / "my pages" | Search pages-registry locally (no API call needed) |

## Notes

- CQL is case-insensitive for `text ~` and `title ~` searches
- `text ~` searches page body content, not just title
- For "мои страницы" (our managed pages), first check pages-registry locally before hitting API
- Space keys are uppercase in CQL (SD, not sd)
- `getPagesInConfluenceSpace` requires numeric `spaceId`, not space key - resolve from config
