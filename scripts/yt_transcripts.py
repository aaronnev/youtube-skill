#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-auth>=2.0.0",
#     "google-auth-oauthlib>=1.0.0",
#     "google-api-python-client>=2.0.0",
#     "youtube-transcript-api>=1.0.0",
# ]
# ///
"""
YouTube Transcript Manager

Batch download and search across all channel transcripts.
Works with any public YouTube video (yours or others).

Usage:
    uv run yt_transcripts.py sync [--force]           # Download all YOUR channel's transcripts
    uv run yt_transcripts.py search <query> [--max N] # Search across transcripts
    uv run yt_transcripts.py list                     # List cached transcripts
    uv run yt_transcripts.py get <VIDEO_ID> [--timed] # Get any video's transcript (cached or fetch)
"""

import argparse
import json
import re
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

CONFIG_DIR = Path.home() / ".openclaw" / "skills-config" / "youtube"
TOKEN_PATH = CONFIG_DIR / "token.json"
TRANSCRIPTS_DIR = CONFIG_DIR / "transcripts"
INDEX_PATH = CONFIG_DIR / "transcript_index.json"


def load_credentials() -> Credentials | None:
    """Load and refresh credentials from token.json."""
    if not TOKEN_PATH.exists():
        print(f"Error: No token found at {TOKEN_PATH}")
        print("Run: uv run yt_auth.py --setup")
        return None

    token_data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(token_data, indent=2))

    return creds


def get_youtube_service():
    """Build YouTube API service."""
    creds = load_credentials()
    if not creds:
        sys.exit(1)
    return build("youtube", "v3", credentials=creds)


def load_index() -> dict:
    """Load transcript index."""
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {"videos": {}}


def save_index(index: dict):
    """Save transcript index."""
    INDEX_PATH.write_text(json.dumps(index, indent=2))


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    total_seconds = int(seconds)
    h, remainder = divmod(total_seconds, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fetch_transcript(video_id: str) -> list[dict] | None:
    """
    Fetch transcript for any public video using youtube-transcript-api.
    Returns list of segments [{start, text}] or None.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try English first (manual or auto-generated)
        transcript = None
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            except NoTranscriptFound:
                # Get any available transcript
                for t in transcript_list:
                    transcript = t
                    break

        if not transcript:
            return None

        raw_segments = transcript.fetch()

        # Normalize to our format
        segments = [
            {"start": int(seg["start"]), "text": seg["text"].replace('\n', ' ')}
            for seg in raw_segments
        ]

        return segments

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception:
        return None


def cmd_sync(args):
    """Download all channel transcripts."""
    youtube = get_youtube_service()
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    index = load_index()

    # Get uploads playlist
    channel_response = youtube.channels().list(
        part="contentDetails,snippet",
        mine=True
    ).execute()

    if not channel_response.get("items"):
        print("No channel found.")
        return

    channel = channel_response["items"][0]
    channel_title = channel["snippet"]["title"]
    uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    print(f"Syncing transcripts for: {channel_title}")
    print()

    # Get all videos
    videos = []
    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        videos.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    print(f"Found {len(videos)} videos")
    print()

    synced = 0
    skipped = 0
    failed = 0

    for i, video in enumerate(videos, 1):
        video_id = video["contentDetails"]["videoId"]
        title = video["snippet"]["title"]

        # Check if already synced (unless --force)
        transcript_path = TRANSCRIPTS_DIR / f"{video_id}.json"
        if transcript_path.exists() and not args.force:
            skipped += 1
            continue

        print(f"[{i}/{len(videos)}] {title[:50]}...", end=" ", flush=True)

        segments = fetch_transcript(video_id)

        if segments:
            # Save transcript
            transcript_data = {
                "video_id": video_id,
                "title": title,
                "published": video["snippet"]["publishedAt"],
                "channel": channel_title,
                "is_own_video": True,
                "segments": segments,
                "full_text": " ".join(s["text"] for s in segments)
            }
            transcript_path.write_text(json.dumps(transcript_data, indent=2))

            # Update index
            index["videos"][video_id] = {
                "title": title,
                "published": video["snippet"]["publishedAt"],
                "has_transcript": True,
                "is_own_video": True
            }

            print(f"✓ ({len(segments)} segments)")
            synced += 1
        else:
            # Mark as no transcript available
            index["videos"][video_id] = {
                "title": title,
                "published": video["snippet"]["publishedAt"],
                "has_transcript": False,
                "is_own_video": True
            }
            print("✗ (no captions)")
            failed += 1

    save_index(index)

    print()
    print(f"Done: {synced} synced, {skipped} skipped, {failed} no captions")
    print(f"Transcripts saved to: {TRANSCRIPTS_DIR}")


def cmd_search(args):
    """Search across all transcripts."""
    if not TRANSCRIPTS_DIR.exists():
        print("No transcripts found. Run 'sync' first.")
        return

    query = args.query.lower()
    results = []

    # Search all transcript files
    for transcript_path in TRANSCRIPTS_DIR.glob("*.json"):
        data = json.loads(transcript_path.read_text())
        video_id = data["video_id"]
        title = data["title"]

        # Search segments for query
        for segment in data.get("segments", []):
            if query in segment["text"].lower():
                results.append({
                    "video_id": video_id,
                    "title": title,
                    "timestamp": segment["start"],
                    "text": segment["text"],
                    "is_own": data.get("is_own_video", True)
                })

    if not results:
        print(f"No matches found for '{args.query}'")
        return

    # Sort by relevance (group by video, then by timestamp)
    results.sort(key=lambda r: (r["video_id"], r["timestamp"]))

    print(f"Found {len(results)} matches for '{args.query}':\n")

    shown = 0
    current_video = None

    for result in results:
        if shown >= args.max:
            remaining = len(results) - shown
            if remaining > 0:
                print(f"... and {remaining} more matches")
            break

        # Print video header when it changes
        if result["video_id"] != current_video:
            current_video = result["video_id"]
            marker = "" if result["is_own"] else " [external]"
            print(f"\n📹 {result['title'][:60]}{marker}")

        ts = format_timestamp(result["timestamp"])
        url = f"https://youtu.be/{result['video_id']}?t={result['timestamp']}"
        text = result["text"][:80]

        print(f"  [{ts}] \"{text}{'...' if len(result['text']) > 80 else ''}\"")
        print(f"         {url}")

        shown += 1


def cmd_list(args):
    """List cached transcripts."""
    index = load_index()

    if not index["videos"]:
        print("No transcripts indexed. Run 'sync' first.")
        return

    own_with = sum(1 for v in index["videos"].values() if v.get("has_transcript") and v.get("is_own_video", True))
    own_without = sum(1 for v in index["videos"].values() if not v.get("has_transcript") and v.get("is_own_video", True))
    external = sum(1 for v in index["videos"].values() if not v.get("is_own_video", True))

    print(f"Transcript Index")
    print(f"  Your videos: {own_with} with captions, {own_without} without")
    if external:
        print(f"  External videos: {external}")
    print(f"  Storage: {TRANSCRIPTS_DIR}")
    print()

    # List recent with transcripts
    videos_with = [
        (vid, info) for vid, info in index["videos"].items()
        if info.get("has_transcript")
    ]
    videos_with.sort(key=lambda x: x[1].get("published", ""), reverse=True)

    print("Recent videos with transcripts:")
    for video_id, info in videos_with[:15]:
        marker = "" if info.get("is_own_video", True) else " [ext]"
        print(f"  • {info['title'][:55]}{marker} ({video_id})")


def cmd_get(args):
    """Get transcript for a single video (cached or fetch)."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPTS_DIR / f"{args.video_id}.json"

    if transcript_path.exists():
        data = json.loads(transcript_path.read_text())
        print(f"Title: {data['title']}")
        print(f"Video: https://youtu.be/{args.video_id}")
        if not data.get("is_own_video", True):
            print("(External video)")
        print("-" * 40)

        if args.timed:
            for segment in data["segments"]:
                ts = format_timestamp(segment["start"])
                print(f"[{ts}] {segment['text']}")
        else:
            print(data["full_text"])
        return

    # Fetch if not cached
    print(f"Fetching transcript for {args.video_id}...")

    segments = fetch_transcript(args.video_id)

    if not segments:
        print("No transcript available for this video.")
        return

    # Try to get video title from API
    title = args.video_id
    published = ""
    channel = "Unknown"

    try:
        youtube = get_youtube_service()
        video_response = youtube.videos().list(
            part="snippet",
            id=args.video_id
        ).execute()

        if video_response.get("items"):
            snippet = video_response["items"][0]["snippet"]
            title = snippet["title"]
            published = snippet["publishedAt"]
            channel = snippet["channelTitle"]
    except Exception:
        pass  # Continue without metadata

    # Determine if it's our video
    is_own = False
    try:
        youtube = get_youtube_service()
        channel_response = youtube.channels().list(part="id", mine=True).execute()
        if channel_response.get("items"):
            my_channel_id = channel_response["items"][0]["id"]
            video_response = youtube.videos().list(part="snippet", id=args.video_id).execute()
            if video_response.get("items"):
                is_own = video_response["items"][0]["snippet"]["channelId"] == my_channel_id
    except Exception:
        pass

    # Cache it
    transcript_data = {
        "video_id": args.video_id,
        "title": title,
        "published": published,
        "channel": channel,
        "is_own_video": is_own,
        "segments": segments,
        "full_text": " ".join(s["text"] for s in segments)
    }
    transcript_path.write_text(json.dumps(transcript_data, indent=2))

    # Update index
    index = load_index()
    index["videos"][args.video_id] = {
        "title": title,
        "published": published,
        "has_transcript": True,
        "is_own_video": is_own
    }
    save_index(index)

    print(f"Title: {title}")
    print(f"Channel: {channel}")
    print(f"Video: https://youtu.be/{args.video_id}")
    if not is_own:
        print("(External video - cached for searching)")
    print("-" * 40)

    if args.timed:
        for segment in segments:
            ts = format_timestamp(segment["start"])
            print(f"[{ts}] {segment['text']}")
    else:
        print(transcript_data["full_text"])


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcript Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Download all YOUR channel's transcripts")
    sync_parser.add_argument("--force", action="store_true", help="Re-download existing")

    # search command
    search_parser = subparsers.add_parser("search", help="Search transcripts")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max", type=int, default=20, help="Max results (default: 20)")

    # list command
    subparsers.add_parser("list", help="List cached transcripts")

    # get command
    get_parser = subparsers.add_parser("get", help="Get any video's transcript")
    get_parser.add_argument("video_id", help="YouTube video ID")
    get_parser.add_argument("--timed", action="store_true", help="Include timestamps")

    args = parser.parse_args()

    commands = {
        "sync": cmd_sync,
        "search": cmd_search,
        "list": cmd_list,
        "get": cmd_get,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
