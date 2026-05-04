---
name: telegram-cli
description: Interact with Telegram directly from Claude Code - send/read messages, manage chats, search conversations, download media, manage contacts, and automate Telegram workflows. Use when the user needs to send a Telegram message, read chat history, search messages, manage groups/channels, download or upload media, work with contacts, or perform any Telegram operation.
allowed-tools: Bash(tg:*)
---

# Telegram CLI - Agent-First Telegram Client

## Prerequisites

The `tg` command must be available. Install globally:

```bash
npm install -g @miolamio/tg-cli
```

You must be authenticated before using any command (except `tg auth login`):

```bash
tg auth status
```

If not logged in, the user must authenticate interactively (requires TTY):

```bash
tg auth login
```

### ⚠️ Auth bootstrap — read this BEFORE every session

Current `tg-cli` ignores `~/.config/telegram-cli/config.json` for `apiId`/`apiHash`.
You **must** export them as env vars in front of every command, otherwise everything
fails with `CREDENTIAL_ERROR`. The values live in the config file — read once, then
export inline.

```bash
# 1. Read creds (one-time per shell session)
TG_API_ID=$(python3 -c "import json; print(json.load(open('$HOME/.config/telegram-cli/config.json'))['apiId'])")
TG_API_HASH=$(python3 -c "import json; print(json.load(open('$HOME/.config/telegram-cli/config.json'))['apiHash'])")
export TG_API_ID TG_API_HASH

# 2. Now any tg command works
tg auth status
```

For one-shot Bash invocations, prepend inline:

```bash
export TG_API_ID=... TG_API_HASH=...; tg chat info @channel
```

If `tg auth status` returns `CREDENTIAL_ERROR` → you forgot the env vars. Don't try
`tg config set` — it doesn't help in the current build.

### ⚠️ Log noise on stdout — strip before parsing JSON

`tg` (gramJS underneath) prints connection logs **to stdout, not stderr**, even with
`--quiet`. They look like:

```
[33m[2026-04-11T21:30:10.173] [INFO] - [Running gramJS version 2.26.21][0m
[33m[2026-04-11T21:30:10.176] [INFO] - [Connecting to ...][0m
{
  "ok": true,
  "data": { ... }
}
```

Naively piping to a file or `jq` will break with `JSONDecodeError: Expecting value`.
`2>/dev/null` doesn't fix it (logs aren't on stderr). `--quiet` doesn't fix it either.
There's no env var (`LOG_LEVEL`, `GRAMJS_LOG_LEVEL`) that silences gramJS in the
current build — verified.

**Canonical clean pipe** — strip ANSI codes, then drop log lines starting with `[2`:

```bash
tg <command> 2>/dev/null \
  | sed -E $'s/\\x1b\\[[0-9;]*m//g' \
  | grep -v $'^\\[2'
```

Then `python3 -c "import json,sys; ..."` or `jq` works on the result.

Full example — fetch and parse channel info:

```bash
tg chat info @yourchannel 2>/dev/null \
  | sed -E $'s/\\x1b\\[[0-9;]*m//g' \
  | grep -v $'^\\[2' \
  | jq '.data.memberCount'
```

The `grep -v $'^\\[2'` filter is safe because:
- gramJS log lines start with `[2026-...` (year) after ANSI strip
- JSON envelope lines start with `{`, `}`, `"`, or whitespace — never `[2`
- A top-level JSON array would start with `[`, but `tg` always wraps in `{ok, data}`

### ⚠️ Reactions quirk — `history` doesn't return them, `get` does

This caught me once. Worth knowing:

- `tg message history <chat>` → returns: `id, text, date, senderId, replyToMsgId, forwardFrom, mediaType, views, forwards, media`. **No `reactions` field.**
- `tg message get <chat> <ids>` → returns the same fields **plus** `reactions: [{emoji, count}, ...]` and `editDate`.

If you need reaction data on many posts, you must batch through `message get`. Limit
is **100 IDs per request** (returns `TOO_MANY_IDS` at 101). Pattern:

```python
# Scan reactions across a whole channel
for start in range(1, MAX_ID + 1, 100):
    end = min(start + 99, MAX_ID)
    ids = ','.join(str(i) for i in range(start, end + 1))
    resp = call_tg(['message', 'get', '@channel', ids])
    for m in resp['data']['messages']:
        if m.get('reactions'):
            ...  # process
```

A 4000-post channel scans in roughly 1 minute (~40 batches × ~1.5s).

Don't store post text when scanning at scale — extract only metadata you need
(`id, date, views, forwards, reactions, mediaType`) to keep snapshots compact.

### Capturing snapshots (members, history) for later diffing

Pattern for saving a clean JSON snapshot to disk:

```bash
mkdir -p "snapshots/$(date +%Y-%m-%d_%H%M)"
tg chat members @channel --limit 200 2>/dev/null \
  | sed -E $'s/\\x1b\\[[0-9;]*m//g' \
  | grep -v $'^\\[2' \
  > "snapshots/$(date +%Y-%m-%d_%H%M)/members.json"
```

Always verify the file parses immediately after writing:

```bash
python3 -c "import json; d=json.load(open('PATH')); print('OK, count:', len(d['data']['members']))"
```

To diff two snapshots (find who joined/left a channel):

```python
import json
old = json.load(open('snapshots/old/members.json'))['data']['members']
new = json.load(open('snapshots/new/members.json'))['data']['members']
old_ids = {m['id'] for m in old}
new_ids = {m['id'] for m in new}
left   = [m for m in old if m['id'] in (old_ids - new_ids)]
joined = [m for m in new if m['id'] in (new_ids - old_ids)]
```

## Quick start

```bash
# check auth
tg auth status
# list your chats
tg chat list --limit 10
# read recent messages from a chat
tg message history @username --limit 20
# send a message
tg message send @username "Hello from Claude Code!"
# search across all chats
tg message search --query "meeting notes"
# download media from a message
tg media download @channel 42
```

## Output modes

All commands support 4 output modes. Default is JSON.

```bash
tg chat list                          # JSON (default) - structured envelope { ok, data }
tg chat list --human                  # Human-readable - formatted for display
tg chat list --jsonl                  # JSONL streaming - one JSON object per line, no envelope
tg chat list --toon                   # TOON - token-efficient for LLMs (31-40% savings)
tg chat list --fields "id,title"      # Select specific fields (dot notation for nested)
```

**For agent workflows:** prefer `--toon` for large outputs (saves tokens) or `--jsonl` for streaming list data. Use `--fields` to narrow output to only what you need.

**Mutually exclusive:** `--toon` / `--human` / `--jsonl` (pick one).

## Global options

Available on every command:

```bash
--json              # JSON output (default)
--human             # Human-readable output
--jsonl             # One JSON object per line (list commands)
--toon              # Token-efficient TOON output
--fields <fields>   # Comma-separated field selection (dot notation)
-v, --verbose       # Show extra info on stderr
-q, --quiet         # Suppress stderr output
--profile <name>    # Use named profile (default: "default")
--config <path>     # Custom config file path
```

## Commands

### Auth

```bash
tg auth login                         # Interactive login (TTY required)
tg auth status                        # Check if logged in, show current user
tg auth logout                        # Destroy session
```

### Session

```bash
tg session export                     # Export portable session string
tg session import <session>           # Import session (argument or stdin)
tg session import --skip-verify       # Import without verifying connection
```

### Chat

```bash
tg chat list                          # List all dialogs
tg chat list --type user              # Filter: user, group, channel, supergroup
tg chat list --limit 20 --offset 5    # Paginate
tg chat info <chat>                   # Get chat details (title, members, permissions)
tg chat join <target>                 # Join by username, @username, or invite link
tg chat leave <chat>                  # Leave a chat
tg chat resolve <input>              # Resolve username/ID/phone to full entity
tg chat invite-info <link>            # Check invite link without joining
tg chat members <chat>                # List members
tg chat members <chat> --search "John"  # Search members by name
tg chat members <chat> --limit 50 --offset 0
tg chat topics <chat>                 # List forum topics (supergroups only)
```

### Message - Reading

```bash
tg message history <chat>             # Read message history (default: 50 messages)
tg message history <chat> --limit 100
tg message history <chat> --since 2026-03-01T00:00:00Z
tg message history <chat> --until 2026-03-13T23:59:59Z
tg message history <chat> --topic <id>  # Forum topic messages
tg message get <chat> <ids>           # Get specific messages by ID (comma-separated, max 100)
tg message pinned <chat>              # Get pinned messages
tg message pinned <chat> --limit 10 --offset 0
tg message replies <channel> <ids>    # Read replies/comments on channel posts
tg message replies <channel> <ids> --limit 50
```

### Message - Searching

```bash
tg message search --query "keyword"                   # Search across all chats
tg message search --query "keyword" --chat @username   # Search in specific chat
tg message search --chat @channel --filter photos      # Filter by media type
tg message search --chat @group --topic <id>           # Search within forum topic
tg message search --limit 20 --offset 0               # Paginate results
```

**Search filters (17 types):**
`photos`, `videos`, `photo_video`, `documents`, `urls`, `gifs`, `voice`, `music`, `round`, `round_voice`, `chat_photos`, `phone_calls`, `mentions`, `geo`, `contacts`, `pinned`

### Message - Sending & Interaction

```bash
tg message send <chat> "Hello!"                       # Send text message
tg message send <chat> "Reply" --reply-to 42          # Reply to a message
tg message send <chat> "Topic msg" --topic <id>       # Send to forum topic
echo "piped text" | tg message send <chat> -          # Send from stdin
tg message edit <chat> <id> "Updated text"            # Edit sent message (48h window)
echo "new text" | tg message edit <chat> <id> -       # Edit from stdin
tg message forward <from> <ids> <to>                  # Forward messages (comma-separated IDs)
tg message react <chat> <id> <emoji>                  # React to a message
tg message react <chat> <id> <emoji> --remove         # Remove reaction
tg message delete <chat> <ids> --revoke               # Delete for everyone
tg message delete <chat> <ids> --for-me               # Delete for self only
tg message pin <chat> <id>                            # Pin message (silent)
tg message pin <chat> <id> --notify                   # Pin with notification
tg message unpin <chat> <id>                          # Unpin message
```

### Message - Polls

```bash
tg message poll <chat> --question "Lunch?" --option "Pizza" --option "Sushi" --option "Tacos"
tg message poll <chat> --question "Capital of France?" --option "London" --option "Paris" --option "Berlin" --quiz --correct 1 --solution "Paris is the capital"
tg message poll <chat> --question "Pick all" --option "A" --option "B" --option "C" --multiple
tg message poll <chat> --question "Vote" --option "Yes" --option "No" --public
tg message poll <chat> --question "Quick?" --option "A" --option "B" --close-in 3600
```

### Media

```bash
tg media download <chat> <ids>                        # Download media from messages
tg media download <chat> <ids> -o ./photo.jpg         # Save to specific path
tg media send <chat> ./photo.jpg                      # Upload and send single file
tg media send <chat> ./a.jpg ./b.jpg                  # Send as album (multiple files)
tg media send <chat> ./doc.pdf --caption "Report"     # With caption
tg media send <chat> ./img.png --reply-to 42          # Reply with media
tg media send <chat> ./img.png --topic <id>           # Send to forum topic
```

### User

```bash
tg user profile <users>               # Get profiles (comma-separated IDs/usernames)
tg user block <user>                  # Block user
tg user unblock <user>                # Unblock user
tg user blocked                       # List blocked users
tg user blocked --limit 20 --offset 0
```

### Contact

```bash
tg contact list                       # List all contacts
tg contact list --limit 50 --offset 0
tg contact add @username              # Add by username or ID
tg contact add +1234567890 --first-name "John" --last-name "Doe"  # Add by phone
tg contact delete <user>              # Delete contact
tg contact search "query"             # Search contacts
tg contact search "query" --global    # Search all Telegram users
tg contact search "query" --limit 10
```

## Chat identifiers

Most commands accept `<chat>` which can be:
- **Username:** `durov` or `@durov`
- **Numeric ID:** `123456789` or `-100123456789`
- **Phone number:** `+1234567890`

## Examples

### Monitor a channel for new messages

```bash
tg message history @channel --limit 5 --toon
```

### Search and read a conversation thread

```bash
tg message search --query "project update" --chat @team_group --limit 10
# then read replies to a specific message
tg message replies @team_group 1234 --limit 20
```

### Send a file with context

```bash
tg media send @colleague ./report.pdf --caption "Q1 Report - see page 3 for highlights"
```

### Get overview of a group

```bash
tg chat info @group_name
tg chat members @group_name --limit 10
tg message pinned @group_name
tg message history @group_name --limit 10 --toon
```

### Forward messages between chats

```bash
tg message forward @source_chat 100,101,102 @destination_chat
```

### Create a poll

```bash
tg message poll @team_chat --question "Sprint retrospective: what went well?" --option "CI/CD improvements" --option "Code review process" --option "Documentation" --option "Testing coverage" --multiple --public
```

### Export session for use in another environment

```bash
tg session export
# Copy the session string to the new environment
tg session import "exported_session_string_here"
```

### Narrow output with --fields

```bash
tg chat list --fields "id,title,type" --limit 5
tg message history @chat --fields "id,text,date,senderId" --limit 10
tg user profile @username --fields "id,username,firstName,bio"
```

## Specific tasks

* **Authentication & sessions** [references/authentication.md](references/authentication.md)
* **Message workflows** [references/message-workflows.md](references/message-workflows.md)
* **Media handling** [references/media-handling.md](references/media-handling.md)
* **Output modes & field selection** [references/output-modes.md](references/output-modes.md)
* **Agent automation patterns** [references/agent-patterns.md](references/agent-patterns.md)
