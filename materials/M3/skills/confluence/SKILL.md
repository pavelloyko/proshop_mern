---
name: confluence
description: >
  Use when user wants to push documents to Confluence, update existing pages,
  read/check Confluence pages, or search Confluence content.
  Triggers on "confluence push", "запуши в confluence", "confluence update",
  "обнови страницу", "confluence read", "прочитай из confluence",
  "confluence search", "найди в confluence", "опубликуй в confluence",
  "что сейчас в confluence", "синхронизируй с confluence",
  "залей в confluence", "confluence page", "страница в confluence".
  Also triggers when user mentions pushing design documents, technical specs,
  or any local markdown files to a wiki or shared documentation space.
---

# Confluence Integration Skill

Manage Confluence pages from Claude Code: publish local documents, update existing pages, read page status, search content.

## Quick Reference

| File | When to Read |
|------|-------------|
| `references/publish-workflow.md` | Publishing (create or update) pages from local files |
| `references/read-workflow.md` | Reading pages, checking sync status, viewing diffs |
| `references/search-workflow.md` | Searching Confluence content (fulltext, title, CQL) |

## Key Data Files

| File | Purpose |
|------|---------|
| `.confluence/config.yaml` | Site URL, default space, spaces registry, routing rules, stats |
| `.confluence/pages-registry.yaml` | Tracks pages we created/manage, local file mappings, sync state |
| `.confluence/operations-log.yaml` | Append-only audit trail of ALL write operations |
| `.confluence/skill-feedback.yaml` | Self-improvement observations and proposals |

## Step 0: Bootstrap Check

If `.confluence/config.yaml` does NOT exist:
1. Create `.confluence/` structure: `config.yaml`, `pages-registry.yaml`, `operations-log.yaml`
2. Ask: "Confluence ещё не настроен. Какой default space? (SD / AKB / другой)"
3. Ask: "Site URL? (default: yourcompany.atlassian.net)"
4. Generate config.yaml from answers
5. Proceed to Step 0.5

## Step 0.5: Load Config

1. Read `.confluence/config.yaml` for site_url, default_space, spaces, routing_rules
2. Use `site_url` from `.confluence/config.yaml` as `cloudId` for ALL MCP calls (NEVER hardcode UUID or URL)
3. Read `.confluence/pages-registry.yaml` for existing page mappings
4. **Registry migration:** If any page entry lacks `content_hash` or `version` fields (legacy entries from before skill existed):
   - Calculate `content_hash` from local file (read -> filter banned patterns -> MD5)
   - Fetch `version` via `getConfluencePage(cloudId, pageId, contentFormat: "markdown")`
   - Update the registry entry with both values
5. If `stats` section missing from config.yaml, initialize: `total_pushes: 3`, `storage_format_reminder_shown: false`

## Step 1: Determine Mode

| User Says | Mode | Reference |
|-----------|------|-----------|
| "push", "запуши", "опубликуй", "залей" | **Publish** | publish-workflow.md |
| "update", "обнови", "синхронизируй" | **Publish** | publish-workflow.md |
| "read", "прочитай", "покажи страницу", "что там сейчас" | **Read** | read-workflow.md |
| "search", "найди", "поиск", "где упоминается" | **Search** | search-workflow.md |

If ambiguous - ask user which mode they need.

## Step 2: Load Reference and Execute

Read the appropriate reference file and follow its workflow.

## Shared Rules (Apply to ALL Modes)

### Never Write to Confluence Without Confirmation
- Always show preview before any create/update
- User must explicitly say "ок" / "да" / "go" before execution
- If "не ок" - fix content, show again

### Filter Banned Content Before Push
Read banned_patterns from `.jira/config.yaml` (shared with Jira skill) and strip matches:
- Feature ID prefixes (13-ILT, 16-Instructor, etc.)
- AI tool references (Claude Code, Claude AI)
- Internal WIP references (work-in-progress, WIP-INDEX)
- Local file paths (/Users/...)
- Any other patterns defined in config

The rationale: these are internal identifiers meaningless to the team. Confluence pages are visible to everyone, so content must be clean.

### Log ALL Write Operations

Every create/update operation MUST be logged. Without logging, the next session loses all context about what was done.

**1. Operations Log** - append to `.confluence/operations-log.yaml`:
```yaml
- timestamp: "2026-03-23T15:30:00"
  type: create_page | update_page
  space: SD
  pages:
    - id: "559218693"
      title: "ILT Event Viewer - Designer Input"
      parent: "559710210"
  context: "Brief description of why"
```

**2. Pages Registry** - update `.confluence/pages-registry.yaml`:
- New page -> add full entry (id, title, space, parent, local_file, url, content_hash, version, jira_ticket, jira_epic, feature_folder, created, last_pushed, updates)
- Updated page -> update last_pushed, content_hash, version, append to updates list

### Jira Cross-Link

After create/update, if pages-registry has `jira_ticket` for this page, offer linking options:
> "Добавить ссылку на Confluence страницу в {jira_ticket}?
> 1. Комментарий (addCommentToJiraIssue)
> 2. Добавить URL в description (editJiraIssue)
> 3. Не линковать"

Remote links (external URLs in Jira Links section) are NOT supported by current MCP tools - only Jira-to-Jira links via `createIssueLink`. If this changes in the future, add as option.

User chooses. If no `jira_ticket` but has `jira_epic` - ask which ticket to link to. If neither - skip silently.

### Format Awareness

ADF is the default format (better rendering). If ADF conversion fails or produces bad output:
1. Warn user: "ADF конвертация дала плохой результат. Запушить в markdown вместо?"
2. Fall back to markdown if user agrees
3. Log the issue in skill-feedback.yaml for converter improvement

User can always override: "запуши в markdown формате" skips ADF conversion entirely.

### Error Handling

- OAuth expired mid-session -> "MCP отключился. Перезапусти Claude Code и пройди /mcp авторизацию."
- 403 Forbidden -> "Нет прав на этот space/страницу. Проверь permissions в Atlassian."
- 404 Not Found -> "Страница не найдена (удалена или ID неверный)."
- 429 Rate Limit -> wait 5 seconds, retry once. Still 429 -> "Confluence rate limit, попробуй через минуту."
- On any unexpected error: STOP, show error, ask user. Never silently continue.

### MCP Tools Reference

All Confluence operations use `mcp__atlassian-jira__*` tools (same MCP server as Jira).

**IMPORTANT: Content Format.** Default is ADF (Atlassian Document Format). Read `content_format` from `.confluence/config.yaml`:
- **`adf`** (default): Convert markdown to ADF JSON using `.confluence/tools/md_to_adf.py`, then pass with `contentFormat: "adf"`. Better rendering: info panels, proper table headers, code macros.
- **`markdown`**: Pass raw markdown with `contentFormat: "markdown"`. Simpler but basic rendering.
- User can override per-push: "запуши в markdown" or "запуши в adf"
- For `getConfluencePage`: always use `contentFormat: "markdown"` for readable output regardless of push format.

**IMPORTANT:** `createConfluencePage` requires numeric `spaceId` (e.g., `"229377"`), NOT space key (e.g., `"SD"`). Resolve space key to numeric ID from `spaces` section of config.yaml.

**ADF Conversion Pipeline:**
1. Read markdown file
2. Filter through banned_patterns
3. Run `python3 .confluence/tools/md_to_adf.py input.md output.json`
4. Read output JSON
5. Pass JSON string as `body` with `contentFormat: "adf"`

Key tools:
- `createConfluencePage(cloudId, spaceId, body, title, parentId, contentFormat, status)` - create page. For ADF: body is JSON string, contentFormat is "adf"
- `updateConfluencePage(cloudId, pageId, body, title, spaceId, contentFormat, status, versionMessage)` - update page (no version param for locking; use pre-check)
- `getConfluencePage(cloudId, pageId, contentFormat)` - read page. Always use contentFormat "markdown" for readable output
- `searchConfluenceUsingCql(cloudId, cql, limit)` - CQL search
- `getConfluenceSpaces(cloudId)` - list spaces
- `getPagesInConfluenceSpace(cloudId, spaceId)` - list pages in space
- `getConfluencePageDescendants(cloudId, pageId)` - page children/tree
- `createConfluenceFooterComment` / `createConfluenceInlineComment` - add comments
- `getConfluencePageFooterComments` / `getConfluencePageInlineComments` / `getConfluenceCommentChildren` - read comments

### Active Spaces

Spaces we work with (from config.yaml):
- **DEV** (your-space-id) — Development Team space: design docs, technical specs
- **KB** (your-space-id) — Knowledge Base space: product docs, how-to guides

If user mentions a space not in config - ask to confirm, then suggest adding it.

## Self-Improvement Protocol

This skill evolves through usage. Same protocol as Jira skill.

### After Every Skill Use: Observe

If anything notable happened, add an observation to `.confluence/skill-feedback.yaml`:
- Something went wrong (error, wrong output, user had to correct)
- Workflow was clunky (too many steps, unnecessary questions)
- User said "this should work differently"
- A pattern emerged not captured in the skill
- Something worked surprisingly well

Do NOT log routine successful operations. Only log when there's signal worth capturing.

### After 3+ Similar Observations: Propose

When you notice a pattern (3+ observations about the same area):
1. Summarize the pattern and why it matters
2. Propose a specific change to a specific file
3. Explain the reasoning
4. Tell user: "Заметил паттерн: {description}. Предлагаю: {proposal}. Одобряешь?"

### On User Approval: Apply

1. Apply the change to skill files
2. Update proposal status to `applied` with date
3. If the change affects other workflows, update those too

### Principles

- **Generalize, don't overfit.** Fix the general rule, not the specific case.
- **Keep it lean.** Remove sections that don't pull their weight.
- **Explain the why.** Reasoning > rigid rules.
- **Look for repeated manual work.** If every invocation involves the same steps, codify them.
- **User feedback > self-assessment.** When the user says "this is wrong" - that's gold.
