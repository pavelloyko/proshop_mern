# Create Task Workflow

Create ad-hoc tasks in Jira: for designer, architect, devs, or any other purpose.

## Input

User describes what to create:
- "Создай таск дизайнеру на фичу 13 - нарисовать Calendar Page"
- "Таск архитектору - ревью подхода к ILT Events API"
- "Закинь баг в PROJ-456 - кнопка не работает на мобильном"
- "Создай эпик для новой фичи ILT Waitlist"

## Algorithm

### 1. Collect Information

From user request, extract or ask:

| Field | How to Get |
|-------|-----------|
| **Project** | From context or ask. Default: LT |
| **Type** | Epic, Story, Task, Bug, Sub-task. Infer from context or ask |
| **Summary** | From user description |
| **Description** | From user description, expand if needed |
| **Parent** | For Story/Task/Sub-task under epic: ask or infer from feature |
| **Assignee** | If "designer" -> lookup role in config.yaml. Otherwise ask or leave unassigned |

### 2. Resolve Assignee (if role mentioned)

Read `.jira/config.yaml` -> `roles` mapping:
```yaml
roles:
  designer: Lena
  architect: TBD
```

If role has a name -> use `lookupJiraAccountId` to find account ID.
If TBD -> leave unassigned, tell user.

### 3. Resolve Parent (if needed)

For Stories/Tasks under an epic:
1. Check if user specified epic key (PROJ-123)
2. If user said "фича 13" -> look up epic from `.jira/mappings/13-*.yaml`
3. If no mapping -> search: `project = LT AND issuetype = Epic AND summary ~ "keyword"`
4. Show results, confirm with user

### 4. Prepare Ticket

Build ticket fields:
- `projectKey`: from step 1
- `issueTypeName`: Epic / Story / Task / Bug / Sub-task
- `summary`: cleaned title
- `description`: cleaned description (run through banned patterns filter)
- `parent`: epic key (if applicable)
- `assignee_account_id`: resolved account ID (if applicable)

### 5. Preview

Show in terminal:
```
--- New Task ---
Project: LT (your project)
Type: Task
Parent: PROJ-123 (ILT Calendar Page)
Summary: Design Calendar Page layout for LWR
Description: Create Figma mockups for the ILT Calendar Page...
Assignee: Lena

Создать? (да / нет / изменить)
```

### 6. Execute

- **"нет"** -> cancel
- **"изменить"** -> ask what to change, update, re-preview
- **"да"** -> Two-step process (see below)

**CRITICAL: Two-Step Creation (Description Formatting Fix)**

The `createJiraIssue` tool's top-level `description` parameter does NOT render markdown properly - newlines appear as literal `\n` text in Jira. This is a known MCP tool limitation.

**Always use this two-step process:**

**Step 1:** Create the ticket WITHOUT description:
```
createJiraIssue(
  projectKey, issueTypeName, summary,
  parent (if applicable),
  assignee_account_id (if applicable)
)
```

**Step 2:** Immediately update with description via `editJiraIssue`:
```
editJiraIssue(
  issueIdOrKey: "LT-XXXX",  // key from Step 1
  contentFormat: "markdown",
  fields: { "description": "## Heading\n\nParagraph text.\n\n- Bullet 1\n- Bullet 2" }
)
```

**Why this works:** `editJiraIssue` passes description inside the `fields` JSON object where `\n` is properly interpreted as newlines. Combined with `contentFormat: "markdown"`, Jira renders headings, lists, bold, etc. correctly.

**Markdown features supported:** `##` headings, `**bold**`, `` `code` ``, `- ` bullet lists, `1. ` numbered lists, tables, code blocks.

**NEVER use `createJiraIssue`'s `description` parameter directly.** Always create first, then edit.

### 7. Confirm

Show created ticket:
```
Создан: PROJ-123 (Task)
URL: https://yourcompany.atlassian.net/browse/PROJ-123
```

### 8. Log the Operation

After EVERY successful create/update, log immediately:

**A. Operations Log** - append to `.jira/operations-log.yaml`:
```yaml
- timestamp: "2026-03-23T15:30:00"
  type: create_task  # or create_epic, create_design_task, create_subtask, update_description, add_comment
  project: LT
  tickets:
    - key: PROJ-123
      summary: "Design Calendar Page layout for LWR"
      parent: PROJ-123
      assignee: Lena Gotovska
  context: "Designer task for ILT Calendar Page feature"
```

**B. Epic Registry** - if this is an epic or a child of an epic, update `.jira/epics/{project}.yaml`:
- **Created epic** -> add new entry under `epics:`
- **Created child** (task/story/design under epic) -> add to parent epic's `children` list
- **Updated ticket** -> append to the ticket's `updates` list:
  ```yaml
  updates:
    - date: "2026-03-23"
      action: updated_description  # or created, add_comment, transition
      summary: "Added Designer Input document content"
  ```

**C. Feature Mapping** - if this ticket relates to a feature folder, ensure `.jira/mappings/{feature}.yaml` has `epic_key` set.

**This step is NOT optional.** Without logging, the next session loses all context about what was done.

## Linking Tasks

If user wants to link to existing ticket:
- Use `createIssueLink` after creation
- Common link types: "Blocks", "Relates", "is caused by"
- Use `getIssueLinkTypes` to see available types if unsure

## Sub-task Example

Sub-tasks **require** a parent issue (Story, Task, or Epic). Example:
- "Создай sub-task под PROJ-456 - написать unit тесты для calendar filter"
- Parent: PROJ-456 (required, ask if not provided)
- Type: Sub-task
- The `parent` field in `createJiraIssue` must be set to parent key

## SUPPORT Project Restriction

SUPPORT is read-mostly. If user tries to create task in SUPPORT:
> "SUPPORT проект отмечен как read-only в конфиге. Создать там таск? Обычно там только комментарии."

Proceed only if user confirms.

## Notes

- Do NOT set story points or sprint (Elisey manages those)
- Labels: skip unless user explicitly provides
- For bulk creation (e.g., "создай 5 тасков") - show all previews, then batch confirm
