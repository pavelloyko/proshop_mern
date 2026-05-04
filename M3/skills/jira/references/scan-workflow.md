# Scan Workflow

Scan Jira tickets for updates, save snapshots, show reports.

## Input

User says one of:
- "Просканируй всё" / "scan all" -> all active epics from mappings
- "Что нового по фиче 13" -> specific feature (find epic from mapping)
- "Посмотри PROJ-456" -> specific ticket
- "Что нового по LT" -> entire project

## Algorithm

### 1. Determine Scope

| Input | Scope | JQL Strategy |
|-------|-------|-------------|
| Specific ticket (PROJ-456) | Ticket + subtasks + linked | `key = PROJ-456` then follow links |
| Feature (13-ILT-Calendar) | Epic tree from mapping | Read `.jira/mappings/{feature}.yaml` -> get `epic_key` and all known `jira_key`s -> `"Epic Link" = {epic_key} OR parent = {epic_key}` |
| Project (LT) | All issues in project | `project = LT AND updated >= -7d` |
| "All" | All active epics | Iterate over all mappings |

### 2. Check Scan History

Read `.jira/scans/scan-history.yaml`:
- **No previous scan** -> full scan, tell user: "Первый скан, покажу всё."
- **Has previous scan** -> ask: "Полный скан или с последнего ({date})?"
  - Full -> get everything
  - Delta -> add `AND updated >= "{last_scan_date}"` to JQL

### 3. Collect Data from Jira

For each ticket in scope, fetch:
- `summary`, `status`, `assignee`, `issuetype`, `priority`, `updated`, `created`
- Comments (use `getJiraIssue` with expand or separate call)
- Linked issues (`issuelinks` field)
- Subtasks
- Remote links (merge requests, if available)

Use `searchJiraIssuesUsingJql` for bulk queries, `getJiraIssue` for individual details.

### 4. Save Snapshot

Write to `.jira/scans/snapshots/{date}-{scope-slug}.yaml`:

```yaml
scan_date: 2026-03-23T15:00:00
scope: feature/13-ILT-Calendar-Page
scope_type: feature  # feature | ticket | project | all
epic: PROJ-123

tickets:
  - key: PROJ-456
    type: Story
    summary: "Calendar View"
    status: In Progress
    assignee: TeamMember
    priority: Medium
    updated: 2026-03-22T10:00:00
    comments_count: 3
    latest_comment:
      author: TeamMember
      date: 2026-03-22T10:00:00
      text: "Need clarification on timezone handling"
    linked_issues:
      - key: PROJ-789
        type: Bug
        relationship: "is blocked by"
    subtasks: []
    merge_requests: []  # if available from remote links

changes_since_last_scan:  # only if delta scan
  new_tickets:
    - "PROJ-789 created (Bug) - 2026-03-21"
  status_changes:
    - "PROJ-456: To Do -> In Progress (2026-03-22)"
  new_comments:
    - "PROJ-456: TeamMember: 'Need clarification on timezone' (2026-03-22)"
  assignee_changes: []
```

### 5. Update Scan History

Append to `.jira/scans/scan-history.yaml`:

```yaml
scans:
  - date: 2026-03-23T15:00:00
    scope: feature/13-ILT-Calendar-Page
    scope_type: feature
    tickets_scanned: 12
    snapshot_file: snapshots/2026-03-23-13-ilt-calendar.yaml
```

### 6. Show Report in Terminal

**Tree view format:**

```
=== Scan: 13-ILT-Calendar-Page (PROJ-123) ===
Date: 2026-03-23 15:00

PROJ-123 [Epic] ILT Calendar Page - In Progress
  |
  +-- PROJ-456 [Story] Calendar View - In Progress (@teammember)
  |     +-- Bug PROJ-789 "Filter breaks on empty date" - Open
  |     +-- MR: feature/calendar-filter (2 commits)
  |     +-- Comment (Mar 22): "Need clarification on timezone"
  |
  +-- PROJ-457 [Story] Event Filter - To Do
  +-- PROJ-458 [Task] Design Calendar Layout - Done (@Lena)

--- Changes since last scan (2026-03-20) ---
  NEW: PROJ-789 (Bug) created
  STATUS: PROJ-456 To Do -> In Progress
  COMMENTS: 2 new comments on PROJ-456
```

**For "all" scope** - show summary table first, then details per epic.

### 7. Compare with Previous Snapshot (if delta)

If previous snapshot exists for same scope:
- Diff ticket statuses
- Identify new tickets
- Count new comments
- Show in "Changes since last scan" section

## Warning for Large Scans

If scope = "all" and more than 5 epics:
> "Это просканирует {N} эпиков (~{estimated_tickets} тикетов). Продолжить?"

## Notes

- For SUPPORT project: read-only scan, different format (show customer info, case numbers)
- Merge request links depend on Jira-Git integration being configured
- Snapshots accumulate - consider manual cleanup periodically
