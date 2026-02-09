# YouTube Skill for OpenClaw

Access YouTube channel analytics, video metadata, and transcripts via official Google APIs + youtube-transcript-api.

## Features

- **Analytics** — Views, watch time, revenue, demographics, traffic sources (YouTube Studio data)
- **Channel** — Subscriber count, video list, search within channel
- **Video** — Metadata, comments, transcripts
- **Transcript Library** — Batch download all your transcripts, search across them, cache external videos

## Installation

```bash
# Clone to OpenClaw skills directory
git clone https://github.com/YOUR_USERNAME/youtube-skill.git ~/.openclaw/workspace/skills/youtube

# Create config directory
mkdir -p ~/.openclaw/skills-config/youtube

# Copy your OAuth credentials (from GCP Console)
cp /path/to/client_secret.json ~/.openclaw/skills-config/youtube/

# Run OAuth setup (opens browser)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_auth.py --setup
```

## Prerequisites

1. **Google Cloud Project** with these APIs enabled:
   - YouTube Data API v3
   - YouTube Analytics API

2. **OAuth 2.0 Client ID** (Desktop app type) downloaded as `client_secret.json`

3. **uv** installed ([astral.sh/uv](https://astral.sh/uv))

## Usage

```bash
# Channel info
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py info

# Analytics overview
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py overview --days 7

# Get any video's transcript
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py transcript VIDEO_ID

# Sync all your transcripts
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py sync

# Search across transcripts
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py search "topic"
```

See `SKILL.md` for full command reference.

## File Structure

```
~/.openclaw/workspace/skills/youtube/     # This repo
├── SKILL.md                              # Skill definition for OpenClaw
├── scripts/
│   ├── yt_auth.py                        # OAuth setup
│   ├── yt_channel.py                     # Channel info, video list
│   ├── yt_video.py                       # Video details, comments, transcripts
│   ├── yt_analytics.py                   # Studio analytics
│   └── yt_transcripts.py                 # Batch transcript management
└── references/
    └── youtube-api-quickref.md           # API reference

~/.openclaw/skills-config/youtube/        # NOT in repo (secrets)
├── client_secret.json                    # Your OAuth credentials
├── token.json                            # Generated after auth
└── transcripts/                          # Cached transcripts
```

## License

MIT
