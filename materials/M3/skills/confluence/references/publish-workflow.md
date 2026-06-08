# Publish Workflow

Unified flow for creating new Confluence pages and updating existing ones from local markdown files.

## Input

User provides one of:
- Path to local file: "запуши design-input/ILT-Calendar-Page-Designer-Input.md"
- Path to folder: "запуши все design-input документы"
- Update request: "обнови страницу по фиче 14"
- Implicit: another skill suggests pushing (e.g., create-designer-input)

## Algorithm

### 1. Determine Document Type (Routing)

Auto-detect from file path:
- `design-input/` in path -> type: `design-input`
- `user-stories/` in path -> type: `user-stories`
- `technical-specs/` or `architecture/` in path -> type: `technical-specs`
- `pre-grooming` in filename -> type: `pre-grooming`

If not detected -> ask: "Какой тип документа? (design-input / technical-spec / user-stories / другой)"
User can always override: "запуши как technical-spec"

### 2. Resolve Destination

Look up `routing_rules` in `.confluence/config.yaml` by document type:
- **Rule exists** -> use `space`, `parent_page_id`, `title_pattern` from rule
- **Rule doesn't exist** -> ask:
  - "В какой space? (DEV / KB / другой)"
  - "Под какую parent page? (покажи список или дай ID)"

Resolve space key to numeric `spaceId` from `spaces` section of config.yaml. MCP requires numeric ID, not key.

### 3. Check Pages Registry

Search `.confluence/pages-registry.yaml` by `local_file` path:
- **Found** -> UPDATE mode (page already exists in Confluence)
- **Not found** -> CREATE mode

### 4. Content Preparation

1. Read the local file
2. Filter through banned_patterns from `.jira/config.yaml` (strip all matches)
3. Save filtered content to a temp file
4. Calculate MD5 hash of filtered content
5. Generate title from `title_pattern` in routing rule, or ask user
6. **Determine format** from `.confluence/config.yaml` -> `content_format` (default: `adf`). User can override per-push.

**If format is `adf`:**
- Run converter: `python3 .confluence/tools/md_to_adf.py <temp_filtered.md> <output.json>`
- Read the output JSON file
- Use JSON string as `body` with `contentFormat: "adf"`
- Blockquotes become info panels, tables get proper headers, code blocks become code macros

**If format is `markdown`:**
- Use filtered markdown directly as `body` with `contentFormat: "markdown"`

### 5a. CREATE Path

**Preview in terminal:**
```
--- New Confluence Page ---
Space: SD (your Development Team space)
Parent: Design Documents (559710210)
Title: ILT Calendar Page - Designer Input
Source: .../design-input/ILT-Calendar-Page-Designer-Input.md
Size: 60KB
Content preview:
  [first 500 chars of filtered content]
  ...

Создать? (да / нет / показать полностью / как черновик)
```

**On "да":** Execute `createConfluencePage`:
- `cloudId`: from `.confluence/config.yaml` -> `site_url`
- `spaceId`: numeric ID from `spaces` section (NOT space key)
- `parentId`: from routing rule or user input
- `title`: generated in Step 4
- `body`: filtered content
- `contentFormat`: `"markdown"`
- `status`: `"current"` (or `"draft"` if user chose "как черновик")

**Post-create:** Add to pages-registry:
```yaml
"NEW_PAGE_ID":
  title: "ILT Calendar Page - Designer Input"
  space: SD
  parent_id: "559710210"
  parent_title: "Design Documents"
  local_file: "path/to/local/file.md"
  jira_ticket: null  # ask user or infer from context
  jira_epic: null
  feature_folder: "13-ILT-Calendar-Page"
  created: "2026-03-23"
  last_pushed: "2026-03-23"
  content_hash: "abc123..."
  version: 1
  url: "https://yourcompany.atlassian.net/wiki/spaces/SD/pages/..."
  updates:
    - date: "2026-03-23"
      action: created
      summary: "Initial push (60KB markdown)"
```

### 5b. UPDATE Path

**Step 1 - Local change detection:**
Compare content_hash of current local file (after filtering) with stored `content_hash` in registry.
- **Hashes match** -> "Файл не изменился с последнего пуша ({date}). Всё равно обновить? (да / нет)"
- **Hashes differ** -> proceed to remote check

**Step 2 - Remote conflict detection:**
Fetch page via `getConfluencePage(cloudId, pageId, contentFormat: "markdown")`.
Compare remote version number with stored `version` in registry.
- **Remote version > stored version** (someone edited in Confluence) -> warning:
  > "Страница была изменена в Confluence после последнего пуша (remote v{N}, pushed as v{M}). Показать remote версию? (да / перезаписать / пропустить)"
- **Remote version == stored version** -> safe to update, proceed

**Step 3 - Preview:**
```
--- Update Confluence Page ---
Page: ILT Calendar Page - Designer Input (560300033)
Space: SD
Content changed: yes (hash abc123 -> def456)
Remote conflicts: none

Обновить? (да / нет)
```

**Step 4 - Execute:** `updateConfluencePage`:
- `cloudId`: from config
- `pageId`: from registry
- `body`: new filtered content
- `title`: existing title (or updated if changed)
- `contentFormat`: `"markdown"`
- `versionMessage`: `"Updated via Confluence skill"`

The API does NOT accept a version number for optimistic locking. Conflict detection is handled by the pre-check in Step 2.

**Step 5 - Record new version:**
After successful update, fetch page again (`getConfluencePage`) to get the new version number from the response.

**Step 6 - Update registry:**
Update pages-registry entry: `last_pushed`, `content_hash`, `version` (from response), append to `updates` list.

### 6. Log Operation

Append to `.confluence/operations-log.yaml`:
```yaml
- timestamp: "2026-03-23T15:30:00"
  type: create_page  # or update_page
  space: SD
  pages:
    - id: "560300033"
      title: "ILT Calendar Page - Designer Input"
      parent: "559710210"
  context: "Pushed Designer Input document (60KB markdown)"
```

### 7. Jira Cross-Link

If pages-registry has `jira_ticket` for this page -> offer linking:
> "Добавить ссылку в {jira_ticket}?
> 1. Комментарий
> 2. В description
> 3. Не линковать"

If no `jira_ticket` but has `jira_epic` -> ask: "Привязать к тикету? Какому?"
If neither -> skip.

### 8. Update Stats

Increment `stats.total_pushes` in config.yaml.

## Batch Push

If user points to a folder with multiple files:
1. List all matching files found
2. Ask: "Строгий ревью (по одному) или пакетный (все разом)?"
3. **Strict:** preview each file, wait for confirmation on each
4. **Batch:** preview all files in summary, single confirmation for all

Each successful push updates the registry immediately (not at end of batch). This is critical for partial failure recovery.

## Partial Batch Failure

If a page fails during batch push (e.g., page 2 of 5):
1. Successful pages are already logged (each push updates registry right after success)
2. Report what was pushed successfully (show page URLs)
3. Report what failed and why (show error message)
4. Ask: "Продолжить с оставшихся {N} файлов?"

## Notes

- **Default format is ADF** (better rendering). Use `.confluence/tools/md_to_adf.py` for conversion
- For ADF: `contentFormat: "adf"`, body is JSON string. For markdown: `contentFormat: "markdown"`, body is raw text
- User can override per-push: "запуши в markdown формате" skips ADF conversion
- `spaceId` must be numeric (e.g., "229377"), not space key (e.g., "SD")
- Draft status (`status: "draft"`) is available for pages not ready for the team
- ADF advantages: info panels (from blockquotes), proper table headers, code macros, smart links
