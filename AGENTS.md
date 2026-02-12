# AGENTS.md — YouTube Skill (Machine-Readable Reference)

This file is for AI agents (Claude Code, OpenClaw, Cursor, Copilot, etc.). For human docs, see [README.md](README.md).

## Setup

Credentials directory: `~/.openclaw/skills-config/youtube/`
Required files: `client_secret.json` (Google OAuth Desktop app), `token.json` (created by auth)

```bash
uv run scripts/yt_auth.py --setup  # One-time OAuth flow (opens browser)
```

## Commands

All scripts use `uv run` (auto-installs dependencies). No virtualenv needed.

### yt_video.py — Single Video Operations

```bash
# Get video metadata (title, views, likes, duration, tags, description)
uv run scripts/yt_video.py details <VIDEO_ID>

# Get top comments
uv run scripts/yt_video.py comments <VIDEO_ID> --max <N>

# Get full transcript (plain text)
uv run scripts/yt_video.py transcript <VIDEO_ID>

# Get transcript with timestamps
uv run scripts/yt_video.py transcript <VIDEO_ID> --timed

# Search transcript for a keyword or phrase (returns timestamps + youtu.be deeplinks)
uv run scripts/yt_video.py transcript <VIDEO_ID> --search "<query>"

# Search with more surrounding context lines (default: 1)
uv run scripts/yt_video.py transcript <VIDEO_ID> --search "<query>" --context <N>
```

**Transcript works on ANY public YouTube video.** No auth needed for transcripts.

### yt_channel.py — Channel Operations

```bash
# Channel stats (subscribers, views, video count)
uv run scripts/yt_channel.py info

# List recent videos (default: 10)
uv run scripts/yt_channel.py videos --max <N>

# List by view count
uv run scripts/yt_channel.py videos --max <N> --order viewCount

# Search within channel (costs 100 API quota units — use sparingly)
uv run scripts/yt_channel.py search "<query>"
```

### yt_analytics.py — YouTube Studio Analytics

```bash
# Channel overview (views, watch time, subscribers, revenue)
uv run scripts/yt_analytics.py overview --days <N>

# Top performing videos
uv run scripts/yt_analytics.py top-videos --days <N> --max <N>

# Single video analytics
uv run scripts/yt_analytics.py video <VIDEO_ID> --days <N>

# Audience demographics (age + gender)
uv run scripts/yt_analytics.py demographics --days <N>

# Traffic sources
uv run scripts/yt_analytics.py traffic --days <N>

# Geographic breakdown
uv run scripts/yt_analytics.py geography --days <N>
```

### yt_transcripts.py — Batch Transcript Library

```bash
# Sync all channel transcripts (incremental after first run)
uv run scripts/yt_transcripts.py sync

# Force re-download all
uv run scripts/yt_transcripts.py sync --force

# Search across ALL cached transcripts (returns timestamps + youtu.be deeplinks)
uv run scripts/yt_transcripts.py search "<query>" --max <N>

# Fetch and cache a single video's transcript
uv run scripts/yt_transcripts.py get <VIDEO_ID>
uv run scripts/yt_transcripts.py get <VIDEO_ID> --timed

# List cached transcripts
uv run scripts/yt_transcripts.py list
```

## When to Use What

| Task | Command |
|------|---------|
| "Find where X is mentioned in a specific video" | `yt_video.py transcript <ID> --search "X"` |
| "Find where I talked about X across all my videos" | `yt_transcripts.py search "X"` |
| "How did my channel do this week?" | `yt_analytics.py overview --days 7` |
| "What are my best performing videos?" | `yt_analytics.py top-videos --days 30` |
| "Get the full transcript of this video" | `yt_video.py transcript <ID>` |
| "What are people saying in the comments?" | `yt_video.py comments <ID> --max 20` |
| "How many subscribers do I have?" | `yt_channel.py info` |

## Output Formats

- **Transcript search** (`--search`): Timestamped lines with `youtu.be/<ID>?t=<seconds>` deeplinks
- **Timed transcript** (`--timed`): `[MM:SS] text` per line
- **Plain transcript**: Single block of text, whitespace-normalized
- **Analytics/channel**: Key-value pairs, human-readable labels
- **All output is stdout**. Parse with standard text tools.

## Video ID Extraction

Video IDs are 11 characters. Extract from URLs:
- `https://www.youtube.com/watch?v=dQw4w9WgXcQ` → `dQw4w9WgXcQ`
- `https://youtu.be/dQw4w9WgXcQ` → `dQw4w9WgXcQ`
- `https://youtu.be/dQw4w9WgXcQ?t=42` → `dQw4w9WgXcQ`

## API Quota (YouTube Data API v3)

Daily limit: 10,000 units. Key costs:
- `search.list`: **100 units** (avoid in loops)
- `videos.list`, `channels.list`, `commentThreads.list`: 1 unit
- Transcripts (via youtube-transcript-api): **0 units** (no quota cost)
- Analytics API: separate generous quota

## Error States

- `No token found` → Run `uv run scripts/yt_auth.py --setup`
- `Transcripts are disabled` → Video has captions turned off
- `Video is unavailable` → Private, deleted, or region-locked
- `No transcript found` → No captions available in any language
