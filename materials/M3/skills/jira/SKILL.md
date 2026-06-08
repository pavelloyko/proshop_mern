---
name: jira
description: Use when user wants to push user stories to Jira, scan ticket updates, create ad-hoc tasks (designer, architect), pull bugs/history for documentation, or manage Jira backlog. Triggers on "jira push", "jira scan", "jira create", "jira pull", "запуши в jira", "просканируй jira", "что нового по тикетам", "создай таск в jira", "вытащи баги", "история тикета".
---

# Jira Integration Skill

Manage Jira integration for your projects: push user stories, scan updates, create tasks, pull data.

## Quick Reference

| File | When to Read |
|------|-------------|
| `references/push-workflow.md` | Pushing user stories to Jira |
| `references/scan-workflow.md` | Scanning tickets for updates |
| `references/create-task-workflow.md` | Creating ad-hoc tasks (epics, stories, tasks, design tasks, bugs) |
| `references/pull-workflow.md` | Pulling bugs, history, docs data |

## Key Data Files

| File | Purpose |
|------|---------|
| `.jira/config.yaml` | Cloud ID, default project, active projects, banned patterns |
| `.jira/team/team-mapping.yaml` | Team member names, aliases, roles -> Jira account IDs. Use for assignee resolution |
| `.jira/epics/{project}.yaml` | Epic registry - tracks epics, their children, and update history |
| `.jira/operations-log.yaml` | Append-only audit trail of ALL write operations |
| `.jira/mappings/{feature}.yaml` | Feature folder -> epic key, US -> Jira ticket mappings |
| `.jira/scans/` | Scan history and snapshots |
| `.jira/skill-feedback.yaml` | Self-improvement observations and proposals |

## Step 0: Bootstrap Check

If `.jira/config.yaml` does NOT exist:
1. Create `.jira/` folder structure: `config.yaml`, `projects/`, `mappings/`, `scans/snapshots/`, `pulls/`, `epics/`, `operations-log.yaml`
2. Ask user: "Jira ещё не настроена. Какой дефолтный проект? (MAIN / DEV / другой)"
3. Ask: "Site URL? (default: yourcompany.atlassian.net)"
4. Generate config.yaml from template with user answers
5. Proceed to Step 0.5

## Step 0.5: Load Config

1. Read `.jira/config.yaml` for site_url, default_project, active_projects, banned_patterns
2. Use `site_url` from config as `cloudId` for all MCP calls (NEVER hardcode)
3. If project not specified by user - ask: "Какой проект? MAIN (default), DEV, BACKEND, SUPPORT (or your keys)?"
4. Default to MAIN if user says "just do it" or doesn't specify

## Step 1: Determine Mode

| User Says | Mode | Reference |
|-----------|------|-----------|
| "push", "запуши", "push user stories", "закинь в jira" | **Push** | push-workflow.md |
| "scan", "просканируй", "что нового", "check tickets", "статус тикетов" | **Scan** | scan-workflow.md |
| "create task", "создай таск", "задачу дизайнеру", "таск архитектору" | **Create** | create-task-workflow.md |
| "pull", "вытащи", "баги", "история тикета", "комментарии", "для документации" | **Pull** | pull-workflow.md |

If ambiguous - ask user which mode they need.

## Step 2: Load Reference and Execute

Read the appropriate reference file and follow its workflow.

## Shared Rules (Apply to ALL Modes)

### Never Write to Jira Without Confirmation
- Always show preview in terminal before any create/update/comment
- User must explicitly say "ок" or "go" or "да" before execution
- If user says "не ок" - fix the content first, show again

### Replace Internal References with Jira References
When creating or updating Jira tickets, NEVER use internal feature numbering (13-ILT-Calendar-Page, 14-ILT-Event-Viewer, etc.).
Instead:
- If a Jira ticket exists for the referenced feature, use the Jira key + name (e.g., "LT-2103 ILT Calendar Page LWC")
- If no Jira ticket exists yet, use plain text description without internal numbering
- This applies to descriptions, comments, and any text pushed to Jira
- Reason: internal numbering is meaningless to the team; Jira keys are the shared language

### Resolve Assignees from Team Mapping
Read `.jira/team/team-mapping.yaml` for name-to-account-ID resolution.
When user says a name or role (e.g., "Lena", "designer", "Elisey"), match against aliases in the mapping file.
Fall back to `lookupJiraAccountId` only if not found in mapping.

### Filter Banned Content Before Push
Read banned_patterns from `.jira/config.yaml` and strip matches:
- Feature ID prefixes (13-ILT, 16-Instructor)
- AI tool references (Claude Code, Claude AI)
- Internal WIP references (work-in-progress, WIP-INDEX)
- Local file paths (/Users/...)
- Any other patterns defined in config

### Conflict Detection
When updating existing Jira tickets:
1. Check Jira `updated` timestamp vs `last_push` in mapping
2. If Jira was updated after last push - warn user: "Этот тикет был изменён в Jira после последнего пуша. Показать remote версию?"
3. User decides: overwrite, merge manually, or skip

### Log ALL Write Operations

Every create/update/comment operation MUST be logged. This is the audit trail - without it, we lose track of what was done and when.

**1. Operations Log (append-only):**
After EVERY write to Jira, append to `.jira/operations-log.yaml`:
```yaml
- timestamp: "2026-03-23T15:30:00"
  type: create_epic | create_story | create_task | create_design_task | create_subtask | update_description | update_fields | add_comment | transition | link_issues
  project: LT
  tickets:
    - key: LT-2103
      summary: "ILT Calendar Page LWC"
      parent: null  # or parent key
      assignee: "Name"
  context: "Brief description of why this was done"
```

**2. Epic Registry:**
When creating or updating an epic, update `.jira/epics/{project}.yaml`:
- New epic -> add entry with summary, feature_folder, created date, empty children
- New child under epic (story/task/design) -> add to parent's `children` list
- Update to epic or child -> append to its `updates` list with date, action, summary

**3. Feature Mappings:**
- Push user stories -> update `.jira/mappings/{feature}.yaml` (as before)
- The mapping also stores `epic_key` linking feature folder to its Jira epic

**4. Scan/Pull data:**
- `scans/scan-history.yaml` + snapshot - for scan operations
- `pulls/` - for pull operations

**Why this matters:** Without logging, the next session has no idea what happened. The operations log is the single source of truth for "what did we do in Jira". Epic registry tracks the hierarchy. Mappings track user stories. All three together give complete picture.

### Error Handling

**MCP / Auth errors:**
- OAuth expired mid-session -> tell user: "MCP отключился. Перезапусти Claude Code и пройди /mcp авторизацию."
- 403 Forbidden -> "Нет прав на этот проект/действие. Проверь permissions в Atlassian."
- 404 Not Found -> "Тикет не найден (удалён или ключ неверный)."
- 429 Rate Limit -> wait 5 seconds, retry once. If still 429 -> "Jira rate limit, попробуй через минуту."

**Partial state (push interrupted):**
- If push fails mid-batch (e.g., 3 of 8 stories pushed):
  1. Report what was pushed successfully (show Jira keys)
  2. Report what failed and why
  3. Mapping is already updated for successful pushes (each push updates mapping immediately)
  4. Ask user: "Продолжить с оставшихся 5 stories?"

**General rule:** On any unexpected error - STOP, show error, ask user. Never silently continue.

### MCP Tools Reference
All Jira operations use `mcp__atlassian-jira__*` tools with `cloudId` from `.jira/config.yaml` -> `site_url`.

Key tools:
- `searchJiraIssuesUsingJql` - search with JQL
- `getJiraIssue` - get issue details
- `createJiraIssue` - create issue
- `editJiraIssue` - update issue
- `addCommentToJiraIssue` - add comment
- `transitionJiraIssue` - change status
- `getJiraProjectIssueTypesMetadata` - get issue types for project
- `createIssueLink` - link issues
- `searchAtlassian` - Rovo search (natural language)

### Active Projects
Only work with: LT, VT, BACKEND, SUPPORT.
If user asks about other projects - remind them those are inactive in config.
SUPPORT is read-mostly (no push, only read/analyze/comment).

## Self-Improvement Protocol

This skill evolves through usage. After each invocation, follow this protocol.

### After Every Skill Use: Observe

If anything notable happened during this invocation, add an observation to `.jira/skill-feedback.yaml`:
- Something went wrong (error, wrong output, user had to correct)
- Something was clunky (too many confirmation steps, slow workflow)
- User explicitly said "this should work differently"
- A pattern emerged that isn't captured in the skill yet
- Something worked surprisingly well (worth reinforcing)

**Do NOT log** routine successful operations. Only log when there's signal.

### After 3+ Similar Observations: Propose

When you notice a pattern (3+ observations about the same area), create a proposal in `skill-feedback.yaml`:
1. Summarize the pattern and why it matters
2. Propose a specific change to a specific file
3. Explain the reasoning (not just "add MUST" - explain WHY)
4. Set status: `proposed`
5. Tell user: "Заметил паттерн: {description}. Предлагаю изменение: {proposal}. Одобряешь?"

### On User Approval: Apply

1. Apply the change to the skill files
2. Update proposal status to `applied`
3. Move to `applied_changes` with date and summary
4. If the change affects how other workflows reference this one, update those too

### Principles (from Anthropic Skill Creator)

- **Generalize, don't overfit.** If one push failed because of a specific edge case, don't add a rule for that exact case. Understand why the general rule didn't cover it and fix the general rule.
- **Keep it lean.** If a section of the skill isn't pulling its weight (nobody uses it, it adds confusion), propose removing it.
- **Explain the why.** Instead of rigid "ALWAYS do X" rules, explain the reasoning. Future Claude instances work better when they understand motivation, not just rules.
- **Look for repeated manual work.** If every invocation involves the same manual steps (e.g., looking up account IDs, building the same JQL), propose codifying it (cache in config, add template to workflow).
- **User feedback > self-assessment.** When the user says "this is wrong", that's gold. When Claude thinks something could be better, that's a suggestion. Different weights.
