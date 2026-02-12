# YouTube Skill

Access YouTube channel analytics, video metadata, and transcripts via official Google APIs.

## Triggers

Use this skill when the user asks about:
- YouTube stats, analytics, or performance
- Channel subscribers, views, or growth
- Video performance, views, or engagement
- YouTube Studio metrics
- Video transcripts or captions
- Top performing videos
- Audience demographics
- Traffic sources
- Revenue or monetization data
- "How are my videos doing?"
- "What videos performed best?"
- "When did I talk about X?"
- "Find clips where I mention X"
- "Search my videos for X"
- Content patterns or themes across videos

## Prerequisites

Authentication must be set up first:
```bash
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_auth.py --setup
```

## Commands

### Channel Information
```bash
# Get channel stats (subscribers, total views, video count)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py info

# List recent videos
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py videos --max 20

# List videos by view count
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py videos --max 20 --order viewCount

# Search within channel (costs 100 quota units)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_channel.py search "topic keywords"
```

### Video Details
```bash
# Get full video metadata
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py details VIDEO_ID

# Get top comments
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py comments VIDEO_ID --max 20

# Get transcript (plain text)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py transcript VIDEO_ID

# Get transcript with timestamps
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py transcript VIDEO_ID --timed

# Search for a specific moment in a video (returns timestamps + deeplinks)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py transcript VIDEO_ID --search "keyword or phrase"

# Search with more surrounding context (default: 1 line either side)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_video.py transcript VIDEO_ID --search "phrase" --context 3
```

### Transcript Library (Phase 2)
```bash
# Download all channel transcripts (one-time, then incremental)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py sync

# Force re-download all
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py sync --force

# Search across ALL your video transcripts
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py search "burnout"
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py search "creative block" --max 50

# List cached transcripts
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py list

# Get single transcript (uses cache or fetches)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py get VIDEO_ID
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_transcripts.py get VIDEO_ID --timed
```

### Analytics
```bash
# Channel overview (last 28 days by default)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py overview
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py overview --days 7

# Top performing videos
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py top-videos --days 30 --max 10

# Single video performance
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py video VIDEO_ID --days 14

# Audience demographics (age/gender)
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py demographics --days 28

# Traffic sources
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py traffic --days 28

# Geographic breakdown
uv run ~/.openclaw/workspace/skills/youtube/scripts/yt_analytics.py geography --days 28
```

## API Quota Notes

YouTube Data API has a daily quota of 10,000 units:
- `videos.list`: 1 unit per call
- `channels.list`: 1 unit per call
- `search.list`: **100 units per call** (use sparingly)
- `commentThreads.list`: 1 unit per call
- `captions.list`: 50 units per call
- `captions.download`: 200 units per call

YouTube Analytics API has separate, generous quotas.

## Transcript Support

Transcripts work for **any public YouTube video** (yours or others) via `youtube-transcript-api`.
- Auto-generated captions: ✓
- Manual captions: ✓
- External videos: ✓ (cached locally for searching)

**Note:** Videos with captions disabled or region-locked will not have transcripts available.

## Example Workflows

**Weekly performance check:**
```bash
uv run yt_analytics.py overview --days 7
uv run yt_analytics.py top-videos --days 7 --max 5
```

**Deep dive on a video:**
```bash
uv run yt_video.py details VIDEO_ID
uv run yt_analytics.py video VIDEO_ID --days 28
uv run yt_video.py comments VIDEO_ID --max 20
```

**Content analysis:**
```bash
uv run yt_channel.py videos --max 50 --order viewCount
uv run yt_video.py transcript VIDEO_ID
```

**Find when you talked about something:**
```bash
# First sync (one-time setup)
uv run yt_transcripts.py sync

# Then search anytime
uv run yt_transcripts.py search "impostor syndrome"
# Returns: timestamps + direct YouTube links (youtu.be/VIDEO?t=SECONDS)
```

**Content theme research:**
```bash
uv run yt_transcripts.py search "motivation" --max 50
uv run yt_transcripts.py search "creativity" --max 50
# Cross-reference with top performers:
uv run yt_analytics.py top-videos --days 365
```

**Research external videos:**
```bash
# Get transcript from any public YouTube video
uv run yt_video.py transcript dQw4w9WgXcQ

# Cache it for future searching
uv run yt_transcripts.py get dQw4w9WgXcQ

# Now it's searchable alongside your own videos
uv run yt_transcripts.py search "keyword"
```
