# YouTube Skill for OpenClaw

Access YouTube channel analytics, video metadata, and transcripts via official Google APIs + youtube-transcript-api.

Built by **[Aaron Nev](https://github.com/aaronnev)** ([@aaron_nev](https://twitter.com/aaron_nev)) with **[Claude](https://claude.ai)**.

If you find this useful, give it a ⭐ — it helps others discover it!

---

## Features

- **Analytics** — Views, watch time, revenue, demographics, traffic sources (YouTube Studio data)
- **Channel** — Subscriber count, video list, search within channel
- **Video** — Metadata, comments, transcripts
- **Transcript Library** — Batch download all your transcripts, search across them, cache external videos for research

## Quick Start

```bash
# Clone to OpenClaw skills directory
git clone https://github.com/aaronnev/youtube-skill.git ~/.openclaw/workspace/skills/youtube

# Create config directory
mkdir -p ~/.openclaw/skills-config/youtube

# Copy your OAuth credentials (from GCP Console)
cp /path/to/client_secret.json ~/.openclaw/skills-config/youtube/

# Run OAuth setup (opens browser)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_auth.py --setup

# Test it
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py info
```

## Prerequisites

1. **Google Cloud Project** with these APIs enabled:
   - YouTube Data API v3
   - YouTube Analytics API

2. **OAuth 2.0 Client ID** (Desktop app type) — download as `client_secret.json`

3. **[uv](https://astral.sh/uv)** installed

## Usage Examples

```bash
# Channel info
uv run yt_channel.py info

# Last 7 days analytics
uv run yt_analytics.py overview --days 7

# Top performing videos
uv run yt_analytics.py top-videos --days 30

# Get any video's transcript (yours or anyone's)
uv run yt_video.py transcript VIDEO_ID

# Download all your channel's transcripts
uv run yt_transcripts.py sync

# Search across all your videos
uv run yt_transcripts.py search "burnout"
# Returns timestamps + clickable YouTube links
```

See **[SKILL.md](SKILL.md)** for the full command reference.

## How It Works

| Component | Source | Auth Required |
|-----------|--------|---------------|
| Analytics (Studio data) | YouTube Analytics API | Yes (OAuth) |
| Channel info & video list | YouTube Data API v3 | Yes (OAuth) |
| Transcripts | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) | No |

Transcripts use `youtube-transcript-api` which works on **any public video** — not just your own. Great for researching competitors or saving inspiring content.

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

~/.openclaw/skills-config/youtube/        # Secrets (not in repo)
├── client_secret.json                    # Your OAuth credentials
├── token.json                            # Generated after auth
└── transcripts/                          # Cached transcripts
```

## Contributing

PRs welcome! If you build something cool on top of this, let me know.

## Credits

- **[Aaron Nev](https://github.com/aaronnev)** — Creator
  - Twitter/X: [@aaron_nev](https://twitter.com/aaron_nev)
  - YouTube: [@aaron_nev](https://youtube.com/@aaron_nev)
- **[Claude](https://claude.ai)** (Anthropic) — Pair programmer, security reviewer, co-author

Built for [OpenClaw](https://github.com/openclaw) — an open-source AI agent framework.

## License

MIT — do whatever you want with it.
