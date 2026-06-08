# Push Workflow

Push user stories from local markdown files to Jira (create new or update existing).

## Input

User provides one of:
- Path to single US file: `US-01-Calendar-View.md`
- Path to multiple US files
- Path to feature folder or `user-stories/vN/` folder (push all)

## Algorithm

### 1. Determine Scope

- Single file -> push one story
- Multiple files -> push selected stories
- Folder -> find all `US-*.md` files EXCLUDING `*-tech-details.md`
- **Version folders:** US live in `user-stories/v1/`, `v2/`, `v3/` etc.
  - If user points to specific vN/ folder -> use that
  - If user points to feature folder -> use latest (highest vN/)
  - **CONFIRM with user:** "Вижу версии v1, v2, v3. Пушу из v3 (последняя)? Или другую?"

### 2. Identify Feature and Read Mapping

- Determine feature from folder path (e.g., `13-ILT-Calendar-Page`)
- Read `.jira/mappings/{feature-slug}.yaml`
- If mapping doesn't exist - this is first push for this feature
- **Mapping is per-feature, not per-version.** US-01 in v1 and US-01 in v2 map to ONE Jira ticket.
  - First push (v1) -> CREATE tickets
  - Later pushes (v2, v3) -> UPDATE existing tickets with new content
  - **CONFIRM:** "US-01 уже запушена как PROJ-456 (из v1). Обновить содержимое из v2?"

### 3. For Each US File

1. **Read file** - extract content
2. **Parse Title** - from H1 heading or first `## User Story:` line
3. **Parse Description** - extract from US file using these rules:
   - **Title:** H1 heading, strip "User Story:" prefix if present
   - **Description:** Include sections: Description, Acceptance Criteria, Affected User Roles (if present)
   - **Exclude:** Tech Details references, internal notes, Phase markers, file paths
   - **Format:** Send as markdown (`contentFormat: "markdown"`)
   - NOTE: These rules are v1 baseline. Will be refined after first real push
4. **Filter** - run through banned_patterns from config, strip matches
5. **Check mapping** - does this US already have a Jira key?
   - **No key** -> CREATE mode
   - **Has key** -> UPDATE mode

### 4. Handle Updates (if UPDATE mode)

1. Compare local content hash with stored `content_hash` in mapping
2. If hashes match - skip (no changes), tell user
3. If hashes differ - check Jira `updated` timestamp vs `last_push`
4. If Jira updated after last push - show warning, ask user
5. If only local changed - proceed with update

### 5. Ask Review Mode

Before first ticket, ask:
> "Строгий ревью (по одному) или пакетный (все разом)?"

Default: **strict (one by one).**

**IMPORTANT: Early stage verification policy.**
On every step that involves writing to Jira (create, update, comment), ALWAYS confirm with user.
This is intentionally verbose for the testing phase. Extra verification steps will be removed later
as the workflow matures and user builds confidence.

Verification checkpoints:
- Before each CREATE: show preview, wait for "ок"
- Before each UPDATE: show diff (old vs new), wait for "ок"
- Before linking to epic: confirm epic key
- After push: show Jira URL, confirm it looks right
- If anything unexpected: STOP and ask

### 6. Preview Each Ticket

Show in terminal:
```
--- US-01-Calendar-View.md ---
Mode: CREATE | UPDATE (PROJ-456)
Epic: PROJ-123 (if known)
Type: Story
Project: MAIN

Title: Calendar View for ILT Events
Description:
  [first 500 chars of filtered description]
  ...

Ок? (да / нет / пропустить / показать полностью)
```

### 7. Execute

- **User says "да/ок"** -> push to Jira
  - **For CREATE:** Two-step process (CRITICAL - see create-task-workflow.md for details):
    1. `createJiraIssue` WITHOUT description (only summary, parent, assignee)
    2. Immediately `editJiraIssue` with `contentFormat: "markdown"` and `fields: { "description": "..." }`
    This avoids literal `\n` rendering bug in createJiraIssue's description parameter.
  - For CREATE under epic: set `parent` field to epic key in step 1
  - **For UPDATE:** use `editJiraIssue` with `contentFormat: "markdown"` and `fields: { "summary": "...", "description": "..." }`
- **User says "нет"** -> ask what to fix, edit the US file, re-preview
- **User says "пропустить/skip"** -> skip this US, move to next

### 8. Update Mapping

After successful push, update `.jira/mappings/{feature-slug}.yaml`:

```yaml
feature: 13-ILT-Calendar-Page
epic_key: PROJ-123
last_push_date: 2026-03-23T15:30:00
stories:
  - us_id: US-01  # stable ID across all versions (v1, v2, v3...)
    file: US-01-Calendar-View.md
    current_version: v2  # latest pushed version folder
    jira_key: PROJ-456
    last_push: 2026-03-23T15:30:00
    content_hash: <md5 of pushed content>
    status: synced
    push_history:
      - version: v1
        date: 2026-03-15T10:00:00
        action: create
      - version: v2
        date: 2026-03-23T15:30:00
        action: update
  - us_id: US-02
    file: US-02-Event-Filter.md
    current_version: null
    jira_key: null
    status: not_pushed
```

## First Push for a Feature

If no mapping exists:
1. Ask user for Epic key (or create new epic?)
2. Create mapping file
3. Proceed with push workflow

## Epic Not Known

If user hasn't provided epic key:
1. Search Jira: `project = LT AND issuetype = Epic AND summary ~ "feature name"`
2. Show results, ask user to confirm or provide key
3. Store in mapping

## Notes

- Only push US files, never tech-details
- US format for Jira will be refined before first real push
- Story points and Sprint fields are NOT set (Elisey manages those)
- Labels: TBD, skip for now unless user specifies
