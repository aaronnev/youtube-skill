# YouTube Skill

Give your AI agent full access to YouTube. Analytics, transcripts, video data — the stuff you actually need.

1,597 lines of Python across 5 scripts. Not a wrapper around one endpoint. A full toolkit that lets Claude (or any AI agent) pull YouTube Studio analytics, download transcripts from any public video, and search across your entire channel's content.

Built for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [OpenClaw](https://github.com/openclaw). Works standalone too.

## What you can actually do with this

Ask your AI agent things like:

**Analytics — real YouTube Studio data, not just public view counts:**
```
"How did my channel do this week?"
"What are my top 10 videos in the last 30 days?"
"Show me traffic sources — where are viewers finding me?"
"Break down my audience demographics"
"Which countries are watching the most?"
```

**Transcripts — this is the killer feature:**
```
"Download all my video transcripts"
"When did I talk about burnout?" → returns timestamps + clickable YouTube links
"Search all my videos for 'creative block'"
"Get the transcript from this MrBeast video"
"Pull transcripts from these 5 competitor channels"
```

**Channel & video data:**
```
"How many subscribers do I have?"
"List my last 20 videos sorted by views"
"Show me the top comments on this video"
"Get full metadata for this video"
```

**Real things I've done with it:**
- Downloaded 29 video transcripts in one command, then searched across all of them for recurring themes
- Set up an automated morning briefing: "how did my videos do this week?" via OpenClaw on Telegram
- Researched competitor channels by pulling their transcripts and finding what topics they cover
- Found the exact timestamp where I mentioned a topic 8 months ago — with a clickable link that jumps right to it

## Quick start

You need [uv](https://astral.sh/uv) (Python package runner) and a Google Cloud project with YouTube APIs enabled.

```bash
# 1. Clone it
git clone https://github.com/aaronnev/youtube-skill.git
cd youtube-skill

# 2. Set up your credentials directory
mkdir -p ~/.openclaw/skills-config/youtube

# 3. Drop in your Google OAuth client_secret.json
#    (Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client → Desktop app)
cp /path/to/client_secret.json ~/.openclaw/skills-config/youtube/

# 4. Authenticate (opens browser, one-time setup)
uv run scripts/yt_auth.py --setup

# 5. Try it
uv run scripts/yt_channel.py info
```

That's it. `uv` handles all Python dependencies automatically — no virtualenv, no pip install, no requirements.txt.

### Google Cloud setup (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable **YouTube Data API v3** and **YouTube Analytics API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID** (Desktop app)
5. Download the JSON → rename to `client_secret.json`

## Commands

### Channel

```bash
# Channel stats (subscribers, total views, video count)
uv run scripts/yt_channel.py info

# List recent videos
uv run scripts/yt_channel.py videos --max 20

# List by view count
uv run scripts/yt_channel.py videos --max 20 --order viewCount

# Search within your channel (costs 100 API quota units)
uv run scripts/yt_channel.py search "topic keywords"
```

### Analytics

```bash
# Channel overview (views, watch time, subscribers, revenue)
uv run scripts/yt_analytics.py overview --days 7

# Top performing videos
uv run scripts/yt_analytics.py top-videos --days 30 --max 10

# Single video deep dive
uv run scripts/yt_analytics.py video VIDEO_ID --days 28

# Audience demographics (age + gender breakdown)
uv run scripts/yt_analytics.py demographics --days 28

# Traffic sources (search, suggested, external, etc.)
uv run scripts/yt_analytics.py traffic --days 28

# Geographic breakdown
uv run scripts/yt_analytics.py geography --days 28
```

### Video

```bash
# Full metadata (title, duration, views, likes, tags, description)
uv run scripts/yt_video.py details VIDEO_ID

# Top comments
uv run scripts/yt_video.py comments VIDEO_ID --max 20

# Transcript — works on ANY public video, not just yours
uv run scripts/yt_video.py transcript VIDEO_ID

# Transcript with timestamps
uv run scripts/yt_video.py transcript VIDEO_ID --timed
```

### Transcripts (batch)

This is where it gets interesting.

```bash
# Download ALL your channel's transcripts (one-time sync, then incremental)
uv run scripts/yt_transcripts.py sync

# Force re-download everything
uv run scripts/yt_transcripts.py sync --force

# Search across ALL your videos — returns timestamps + clickable YouTube links
uv run scripts/yt_transcripts.py search "burnout"
uv run scripts/yt_transcripts.py search "creative block" --max 50

# Fetch and cache any external video's transcript
uv run scripts/yt_transcripts.py get dQw4w9WgXcQ

# List everything in your transcript library
uv run scripts/yt_transcripts.py list
```

Search output looks like this:
```
Found 7 matches for 'burnout':

📹 Why I Almost Quit YouTube
  [4:23] "...the burnout hit different this time because I was..."
         https://youtu.be/abc123?t=263
  [12:07] "...dealing with burnout is not about working less..."
          https://youtu.be/abc123?t=727

📹 My Creative Process (Honest Version)
  [8:41] "...after the burnout period I changed how I..."
         https://youtu.be/def456?t=521
```

Every match links directly to that moment in the video.

## How it works

Five standalone Python scripts, each with inline dependency declarations ([PEP 723](https://peps.python.org/pep-0723/)). Run any of them with `uv run` — dependencies install automatically on first run.

| Script | What it does | API |
|--------|-------------|-----|
| `yt_auth.py` | OAuth setup, token refresh, revoke | Google OAuth 2.0 |
| `yt_channel.py` | Channel stats, video list, search | YouTube Data API v3 |
| `yt_video.py` | Video metadata, comments, transcripts | YouTube Data API v3 + [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| `yt_analytics.py` | Studio analytics (views, revenue, demographics, traffic, geography) | YouTube Analytics API v2 |
| `yt_transcripts.py` | Batch sync, full-text search, transcript caching | YouTube Data API v3 + youtube-transcript-api |

**Transcripts work on any public YouTube video** — yours or anyone else's. They use `youtube-transcript-api` which pulls auto-generated or manual captions directly. No API key needed for that part.

**Analytics gives you the real data** — the same numbers you see in YouTube Studio. Demographics, traffic sources, revenue, watch time. Not just the public view count.

**Credentials** live in `~/.openclaw/skills-config/youtube/` (outside the repo). Transcripts are cached locally as JSON with full-text indexes for fast searching.

### For OpenClaw / Claude Code

Drop this repo in `~/.openclaw/workspace/skills/youtube/` and the `SKILL.md` file tells the agent when and how to use each command. Works out of the box with OpenClaw's skill auto-discovery.

For Claude Code, the scripts work directly — just point Claude at the `scripts/` directory.

## Credits

Built by **[Aaron Nev](https://github.com/aaronnev)** with **[Claude](https://claude.ai)**.

- X: [@aaronnev_](https://x.com/aaronnev_)
- YouTube: [@aaron_nev](https://youtube.com/@aaron_nev)

Built for [OpenClaw](https://github.com/openclaw) — an open-source AI agent platform.

## License

MIT
