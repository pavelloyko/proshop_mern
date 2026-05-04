# Pull Workflow

Pull data from Jira for analysis, documentation, or review.

## Input

User says one of:
- "Вытащи баги по фиче 13" -> pull bugs for feature
- "История тикета PROJ-456" -> full ticket history
- "Собери данные для документации по эпику PROJ-123" -> docs pipeline
- "Покажи комментарии по PROJ-456" -> comments only
- "Какие баги на саппорте за последнюю неделю?" -> SUPPORT analysis

## Scenarios

### A) Pull Bugs

**Input:** scope (feature/epic/project) + optional filters (status, date range)

1. Build JQL: `project = LT AND issuetype = Bug AND "Epic Link" = PROJ-123`
   - Add status filter: `AND status in (Open, "In Progress")`
   - Add date filter: `AND created >= "2026-03-01"`
2. Fetch bugs via `searchJiraIssuesUsingJql`
3. Show table in terminal:

```
Bugs for PROJ-123 (ILT Calendar Page):

| Key | Summary | Status | Assignee | Created | Priority |
|-----|---------|--------|----------|---------|----------|
| PROJ-789 | Filter breaks on empty date | Open | - | Mar 21 | High |
| PROJ-791 | Timezone offset in event display | In Progress | Nadya | Mar 22 | Medium |
```

4. Save to `.jira/pulls/{date}-bugs-{scope}.yaml`

### B) Ticket History

**Input:** ticket key (e.g., PROJ-456)

1. Fetch full issue via `getJiraIssue` with all fields
2. Fetch comments via issue data
3. Compile chronological history:

```
=== PROJ-456: Calendar View ===
Type: Story | Status: In Progress | Priority: Medium
Assignee: TeamMember | Reporter: User
Epic: PROJ-123 (ILT Calendar Page)
Created: 2026-03-15 | Updated: 2026-03-22

--- Description ---
[full description text]

--- Comments (3) ---
[2026-03-16] User: "Added acceptance criteria for timezone support"
[2026-03-20] TeamMember: "Starting implementation, question about DST handling"
[2026-03-22] TeamMember: "Need clarification on timezone handling"

--- Linked Issues ---
PROJ-789 (Bug) "Filter breaks on empty date" - blocks this
PROJ-123 (Task) "Design Calendar Layout" - relates to

--- Subtasks ---
(none)

--- Remote Links / MRs ---
(if available)
```

4. Save to `.jira/pulls/{date}-history-{ticket-key}.md`

### C) Collect for Documentation

**Input:** feature/epic scope

1. Fetch all tickets in epic tree (stories, tasks, bugs, subtasks)
2. For each ticket: get description, comments, status, linked issues
3. Filter noise:
   - Skip automated comments (CI/CD, bot messages)
   - Skip status-only comments ("moved to In Progress")
   - Keep substantive discussions
4. Structure as documentation input:

```markdown
# Documentation Input: ILT Calendar Page (PROJ-123)

## Overview
Epic: PROJ-123
Total tickets: 12 (5 stories, 3 tasks, 4 bugs)
Status: 3 Done, 5 In Progress, 4 To Do

## Stories

### PROJ-456: Calendar View
Status: In Progress
Description: [text]
Key discussions:
  - Timezone handling approach (TeamMember, Mar 20-22)
Bugs: PROJ-789 (filter issue)

### PROJ-457: Event Filter
...

## Design Decisions (from comments)
- Timezone: decided to use user's local timezone (PROJ-456 comments)
- Layout: grid view confirmed by designer (PROJ-123)

## Open Questions
- DST handling still unclear (PROJ-456, Mar 22)
```

5. Save to `.jira/pulls/{date}-docs-{feature-slug}.md`

### D) SUPPORT Analysis [Phase 2 - Basic version now, advanced analytics later]

**Input:** query (time range, keywords, product area)
**Note:** Current version provides basic ticket listing and stats. Advanced analytics
(customer pain point trends, MR/DevOps correlation, volume patterns) will be added after
first real usage when we understand what queries are most valuable.

1. Build JQL for SUPPORT project:
   - `project = SUPPORT AND created >= "-7d"` (last week)
   - Add keyword filters if provided
2. Fetch and show summary:

```
SUPPORT tickets (last 7 days): 15

By Type:  Bug: 8 | Task: 5 | Story: 2
By Status: Open: 6 | In Progress: 5 | Waiting: 3 | Done: 1

Top issues:
1. SUPPORT-19519 - ILT Class date offset (Bug, Waiting)
2. SUPPORT-19516 - Can't add Media to LP Sections (Bug, Open)
...
```

3. Save to `.jira/pulls/{date}-support-analysis.yaml`

## Notes

- SUPPORT is read-only in config - no creates/updates, only reads and comments
- For docs pipeline: output format will evolve based on create-documentation skill needs
- Large pulls (100+ tickets) - warn user about volume first
- Comments in SUPPORT can be added via `addCommentToJiraIssue` if user explicitly asks
