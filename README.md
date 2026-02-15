# youtube-skill

Give your AI agent the ability to read and understand YouTube. Built for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [OpenClaw](https://openclaw.ai).

## What It Does

Your YouTube Studio analytics + transcripts from any public video on YouTube. All accessible to your AI agent.

- **Search across your entire channel** — "when did I talk about burnout?" → timestamps + clickable YouTube links
- **Pull any video's transcript** — yours, MrBeast's, anyone's. Free, unlimited.
- **Real Studio data** — demographics, traffic sources, watch time, revenue. Not just public view counts.
- **Automated briefings** — "how did my videos do this week?" every morning via OpenClaw
- **Free** — uses Google's free API tier (10,000 units/day) + transcript pulls cost nothing
- **Secure** — OAuth 2.0, credentials stay on your machine. No third-party services, no proxies.

## Getting Started

You need [uv](https://astral.sh/uv) (Python package runner) and a Google Cloud project.

### 1. Google Cloud setup (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable **YouTube Data API v3** and **YouTube Analytics API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID** (Desktop app)
5. Download the JSON → rename to `client_secret.json`

### 2. Install

```bash
git clone https://github.com/aaronnev/youtube-skill.git
cd youtube-skill
mkdir -p ~/.openclaw/skills-config/youtube
cp /path/to/client_secret.json ~/.openclaw/skills-config/youtube/
```

### 3. Authenticate

```bash
uv run scripts/yt_auth.py --setup
```

Opens a browser, one-time setup. That's it. `uv` handles all Python dependencies automatically.

### 4. Try it

```bash
uv run scripts/yt_channel.py info
```

## How to Use

### Ask your agent

If you're using OpenClaw or Claude Code, just ask naturally:

```
"find every time MrBeast mentions money"
"how did my last video perform?"
"pull the transcript from Lex Fridman's latest"
"when did MKBHD talk about the iPhone camera?"
"search all my videos for when I said burnout"
```

### Real things I've done with it

- Downloaded 29 video transcripts in one command, then searched across all of them for recurring themes
- Set up automated morning briefings: "how did my videos do this week?" via OpenClaw on Telegram
- Researched competitor channels by pulling their transcripts and finding what topics they cover
- Found the exact timestamp where I mentioned a topic 8 months ago — with a clickable link that jumps right to it

### Transcript search

This is the killer feature. Search across ALL your videos with timestamps and clickable links:

```
Found 7 matches for 'burnout':

📹 Why I Almost Quit YouTube
  [4:23] "...the burnout hit different this time because I was..."
         https://youtu.be/abc123?t=263
  [12:07] "...dealing with burnout is not about working less..."
          https://youtu.be/abc123?t=727
```

Every match links directly to that moment in the video.

### Search within a single video

```bash
# Find every mention of "camera" in an MKBHD video with 2 lines of context
uv run scripts/yt_video.py transcript dQw4w9WgXcQ --search "camera" --context 2
```

## Commands

### Channel

```bash
uv run scripts/yt_channel.py info                              # Channel stats
uv run scripts/yt_channel.py videos --max 20                   # Recent videos
uv run scripts/yt_channel.py videos --max 20 --order viewCount # By views
uv run scripts/yt_channel.py search "topic keywords"           # Search your channel
```

### Analytics

```bash
uv run scripts/yt_analytics.py overview --days 7        # Views, watch time, subs, revenue
uv run scripts/yt_analytics.py top-videos --days 30     # Top performing videos
uv run scripts/yt_analytics.py video VIDEO_ID --days 28 # Single video deep dive
uv run scripts/yt_analytics.py demographics --days 28   # Age + gender breakdown
uv run scripts/yt_analytics.py traffic --days 28        # Traffic sources
uv run scripts/yt_analytics.py geography --days 28      # Geographic breakdown
```

### Video

```bash
uv run scripts/yt_video.py details VIDEO_ID              # Full metadata
uv run scripts/yt_video.py comments VIDEO_ID --max 20    # Top comments
uv run scripts/yt_video.py transcript VIDEO_ID           # Plain transcript
uv run scripts/yt_video.py transcript VIDEO_ID --timed   # With timestamps
uv run scripts/yt_video.py transcript VIDEO_ID --search "keyword"             # Search within video
uv run scripts/yt_video.py transcript VIDEO_ID --search "keyword" --context 3 # With surrounding lines
```

### Transcripts (batch)

```bash
uv run scripts/yt_transcripts.py sync                  # Download all your channel's transcripts
uv run scripts/yt_transcripts.py sync --force           # Re-download everything
uv run scripts/yt_transcripts.py search "burnout"       # Search across ALL videos
uv run scripts/yt_transcripts.py search "creative block" --max 50
uv run scripts/yt_transcripts.py get VIDEO_ID           # Fetch + cache any video's transcript
uv run scripts/yt_transcripts.py list                   # Everything in your library
```

## Cost

Free. Google's YouTube Data API gives you 10,000 units/day at no cost. Transcript pulls use `youtube-transcript-api` which costs nothing. Analytics uses YouTube Analytics API v2 (also free).

The only thing that costs quota is channel search (100 units per call). Normal use won't come close to the daily limit.

## How It Works

Five standalone Python scripts, each with inline dependency declarations ([PEP 723](https://peps.python.org/pep-0723/)). Run any of them with `uv run` — dependencies install automatically on first run.

| Script | What it does | API |
|--------|-------------|-----|
| `yt_auth.py` | OAuth setup, token refresh, revoke | Google OAuth 2.0 |
| `yt_channel.py` | Channel stats, video list, search | YouTube Data API v3 |
| `yt_video.py` | Video metadata, comments, transcript + search | YouTube Data API v3 + youtube-transcript-api |
| `yt_analytics.py` | Studio analytics (views, revenue, demographics, traffic, geography) | YouTube Analytics API v2 |
| `yt_transcripts.py` | Batch sync, full-text search, transcript caching | YouTube Data API v3 + youtube-transcript-api |

**Transcripts work on any public YouTube video** — yours or anyone else's. No API key needed for that part.

**Analytics gives you the real data** — the same numbers you see in YouTube Studio. Not just the public view count.

**Credentials** live in `~/.openclaw/skills-config/youtube/` (outside the repo). Transcripts are cached locally as JSON with full-text indexes for fast searching.

### For OpenClaw / Claude Code

Drop this repo in `~/.openclaw/workspace/skills/youtube/` and the `SKILL.md` file tells the agent when and how to use each command. Works out of the box.

## Credits

1,597 lines of Python across 5 scripts. Built by **[Aaron Nev](https://github.com/aaronnev)** with **[Claude](https://claude.ai)**.

- X: [@aaronnev_](https://x.com/aaronnev_)
- YouTube: [@aaron_nev](https://youtube.com/@aaron_nev)

Built for [OpenClaw](https://openclaw.ai) — an open-source AI agent platform.

## For AI Agents

If you're an AI agent (Claude Code, Cursor, Copilot, OpenClaw, etc.), see **[AGENTS.md](AGENTS.md)** for a machine-readable command reference with every flag, output format, and decision table.

## License

MIT
