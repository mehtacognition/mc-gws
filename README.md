# mc-gws — Virtual Chief of Staff

A CLI-based Virtual Chief of Staff that connects Google Workspace, Notion, and Claude to keep you organized. It surfaces what matters most, suggests actions, and sends you scheduled iMessage briefings.

## What It Does

**Smart Path** (LLM-powered, 30-90s):
- `g briefing` — Strategic morning digest with weather, calendar conflicts, priorities
- `g midday` — Midday check-in on what's urgent
- `g prep "meeting"` — Meeting preparation with related emails, docs, and context
- `g wrap` — End-of-day summary with tomorrow's preview
- `g weekly` — Monday week-ahead overview with financial snapshot
- `g chat "question"` — Freeform chief-of-staff conversation

**Fast Path** (instant, no LLM):
- `g calendar [today|tomorrow|week]` — Calendar view
- `g email` — Unread emails / `g email "query"` to search
- `g email reply <id> "body"` — Reply to a thread
- `g email send "to" "subject" "body"` — Send email
- `g drive recent` — Recent files / `g drive "query"` to search
- `g search "query"` — Unified search across Drive, Gmail, Calendar
- `g tasks` — Google Tasks / `g tasks add "title"`
- `g people "name"` — Contact lookup
- `g followups` — Follow-up tracking

**Scheduled Automation** (via macOS launchd):
- Morning briefing, midday check-in, end-of-day wrap, Monday weekly digest
- Delivered as iMessage notifications

## Prerequisites

- **macOS** (for iMessage notifications and launchd scheduling)
- **Python 3.9+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** installed and authenticated (`claude -p` must work)
- **[Google Workspace CLI (gws)](https://github.com/googleworkspace/cli)** v0.5+ installed

## Setup

### 1. Install gws CLI

Download the latest release from [github.com/googleworkspace/cli/releases](https://github.com/googleworkspace/cli/releases) for your platform. Place the binary somewhere on your PATH (e.g., `~/.local/bin/gws`).

### 2. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable these APIs: Gmail, Calendar, Drive, Sheets, Tasks, People
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the client secret JSON
6. Save it: `mkdir -p ~/.config/gws && cp ~/Downloads/client_secret_*.json ~/.config/gws/client_secret.json`
7. Authenticate:
   ```bash
   gws auth login --account you@example.com --scopes "https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/tasks,https://www.googleapis.com/auth/contacts.readonly"
   ```

### 3. Install mc-gws

```bash
git clone https://github.com/mehtacognition/mc-gws.git
cd mc-gws
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 4. Configure

```bash
mkdir -p ~/.config/mc-gws
cp config.example.json ~/.config/mc-gws/config.json
```

Edit `~/.config/mc-gws/config.json` with your values:

| Field | Description |
|-------|-------------|
| `account` | Your Google Workspace email |
| `owner_name` | Your name and role (personalizes the AI prompts) |
| `self_reminder_phone` | Your iMessage phone number for notifications |
| `schedule.timezone` | Your IANA timezone (e.g., `America/New_York`) |
| `location.lat/lon/name` | Your city coordinates for weather in briefings |
| `notion.*_db` | Notion database IDs (optional, for meeting notes/projects/clients/people) |
| `vcfo.*` | Virtual CFO integration (optional) |

### 5. Verify it works

```bash
source venv/bin/activate
g calendar today
g email
g briefing
```

### 6. Set up scheduled automation (optional)

The install script copies launchd plists and loads them:

```bash
bash install_launchd.sh
```

This sets up:
- **Briefing** — Mon-Fri at 7:28 AM
- **Midday** — Mon-Fri at 11:58 AM
- **Wrap** — Mon-Fri at 4:58 PM
- **Weekly** — Monday at 7:25 AM

Times are 2 minutes early to account for LLM latency. Edit the plists before installing to change times.

Verify they're loaded:
```bash
launchctl list | grep mcgws
```

### 7. Claude Code slash command (optional)

To use `/gws` inside Claude Code for a conversational chief-of-staff experience, create `~/.claude/commands/gws.md` with the slash command prompt. See the project's design doc for the full template.

## Architecture

```
g <command>
    |
    ├── Fast Path (no LLM)
    |     calendar, email, drive, tasks, people, search, followups
    |     → gws CLI → Google Workspace APIs → formatted output
    |
    └── Smart Path (LLM-powered)
          briefing, midday, prep, wrap, weekly, chat
          → gws CLI (data fetch) → claude -p (reasoning) → output/iMessage
```

- **`gws` CLI** handles all Google Workspace API calls with OAuth
- **`claude -p`** provides the intelligence layer (chief-of-staff reasoning)
- **iMessage via AppleScript** for scheduled notifications
- **Open-Meteo API** for local weather (free, no API key)
- **Notion MCP** for meeting notes, projects, clients context (via `/gws` slash command)

## Configuration Reference

See `config.example.json` for all available options with sensible defaults.

## Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## Author

Built by [Nishant Mehta](https://mehtacognition.com) / [MehtaCognition](https://github.com/mehtacognition) — a leadership consultancy that helps organizations think and act more strategically.

## License

MIT
