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
YouTube Video Script

Get video details, comments, and transcripts.

Usage:
    uv run yt_video.py details <VIDEO_ID>                          # Full metadata
    uv run yt_video.py comments <VIDEO_ID> [--max N]               # Top comments
    uv run yt_video.py transcript <VIDEO_ID>                       # Get transcript (any public video)
    uv run yt_video.py transcript <VIDEO_ID> --timed               # With timestamps
    uv run yt_video.py transcript <VIDEO_ID> --search "keyword"    # Find moments matching keyword
    uv run yt_video.py transcript <VIDEO_ID> --search "keyword" --context 2  # With surrounding lines
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


def parse_duration(duration: str) -> str:
    """Convert ISO 8601 duration to human readable."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return duration

    hours, minutes, seconds = match.groups()
    hours = int(hours or 0)
    minutes = int(minutes or 0)
    seconds = int(seconds or 0)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    total_seconds = int(seconds)
    h, remainder = divmod(total_seconds, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def cmd_details(args):
    """Get full video details."""
    youtube = get_youtube_service()

    response = youtube.videos().list(
        part="snippet,statistics,contentDetails,status",
        id=args.video_id
    ).execute()

    if not response.get("items"):
        print(f"Video not found: {args.video_id}")
        return

    video = response["items"][0]
    snippet = video["snippet"]
    stats = video["statistics"]
    content = video["contentDetails"]
    status = video["status"]

    print(f"Title: {snippet['title']}")
    print(f"ID: {video['id']}")
    print(f"Channel: {snippet['channelTitle']}")
    print(f"Published: {snippet['publishedAt']}")
    print()
    print(f"Duration: {parse_duration(content['duration'])}")
    print(f"Definition: {content.get('definition', 'N/A').upper()}")
    print(f"Privacy: {status.get('privacyStatus', 'N/A')}")
    print()
    print(f"Views: {int(stats.get('viewCount', 0)):,}")
    print(f"Likes: {int(stats.get('likeCount', 0)):,}")
    print(f"Comments: {int(stats.get('commentCount', 0)):,}")
    print()
    print(f"Tags: {', '.join(snippet.get('tags', [])[:10])}")
    print()
    print("Description:")
    print("-" * 40)
    print(snippet.get("description", "No description"))


def cmd_comments(args):
    """Get top comments on a video."""
    youtube = get_youtube_service()

    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=args.video_id,
            maxResults=args.max,
            order="relevance"
        ).execute()
    except Exception as e:
        if "commentsDisabled" in str(e):
            print("Comments are disabled on this video.")
            return
        raise

    if not response.get("items"):
        print("No comments found.")
        return

    print(f"Top {len(response['items'])} comments:\n")

    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]
        author = comment["authorDisplayName"]
        text = comment["textDisplay"][:200]
        likes = comment["likeCount"]

        # Clean HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)

        print(f"• {author} ({likes:,} likes)")
        print(f"  {text}")
        print()


def cmd_transcript(args):
    """Get video transcript using youtube-transcript-api."""
    try:
        ytt = YouTubeTranscriptApi()
        # Fetch transcript - tries English first via list, then direct fetch
        transcript_meta = None
        try:
            transcript_list = ytt.list(args.video_id)
            for t in transcript_list:
                if t.language_code in ('en', 'en-US', 'en-GB'):
                    transcript_meta = t
                    break
            if not transcript_meta:
                # Take whatever is available
                for t in transcript_list:
                    transcript_meta = t
                    break
        except Exception:
            pass

        if transcript_meta:
            result = transcript_meta.fetch()
            lang_label = f"{transcript_meta.language} - {'auto-generated' if transcript_meta.is_generated else 'manual'}"
        else:
            # Direct fetch as fallback
            result = ytt.fetch(args.video_id)
            lang_label = f"{result.language} - {'auto-generated' if result.is_generated else 'manual'}"

        snippets = result.snippets if hasattr(result, 'snippets') else result
        snippet_list = list(snippets)

        print(f"Transcript ({lang_label}):")
        print(f"Video: https://youtu.be/{args.video_id}")
        print("-" * 40)

        if args.search:
            # Search mode: find matching segments with context
            search_lower = args.search.lower()
            context = getattr(args, 'context', 1)
            matches = []
            seen = set()

            # Build sliding window of combined text for phrase matching
            for i, segment in enumerate(snippet_list):
                # Combine current + next few segments for phrase matching across boundaries
                window_texts = []
                for j in range(i, min(i + 3, len(snippet_list))):
                    window_texts.append(snippet_list[j].text.lower())
                combined = ' '.join(window_texts)

                if search_lower in combined:
                    # Add surrounding context lines
                    start = max(0, i - context)
                    end = min(len(snippet_list), i + context + 1)
                    for j in range(start, end):
                        if j not in seen:
                            seen.add(j)
                            matches.append(snippet_list[j])

            if not matches:
                print(f"No matches found for: {args.search}")
                return

            print(f"Found {len(matches)} segments matching '{args.search}':\n")
            for segment in matches:
                ts = format_timestamp(segment.start)
                t_sec = int(segment.start)
                text = segment.text.replace('\n', ' ')
                link = f"https://youtu.be/{args.video_id}?t={t_sec}"
                print(f"[{ts}] {text}")
                print(f"       → {link}")
                print()

        elif args.timed:
            for segment in snippet_list:
                ts = format_timestamp(segment.start)
                text = segment.text.replace('\n', ' ')
                print(f"[{ts}] {text}")
        else:
            full_text = ' '.join(segment.text.replace('\n', ' ') for segment in snippet_list)
            full_text = re.sub(r'\s+', ' ', full_text)
            print(full_text)

    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
    except VideoUnavailable:
        print("Video is unavailable (private, deleted, or region-locked).")
    except NoTranscriptFound:
        print("No transcript found for this video.")
    except Exception as e:
        print(f"Error fetching transcript: {e}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Video Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # details command
    details_parser = subparsers.add_parser("details", help="Get video details")
    details_parser.add_argument("video_id", help="YouTube video ID")

    # comments command
    comments_parser = subparsers.add_parser("comments", help="Get top comments")
    comments_parser.add_argument("video_id", help="YouTube video ID")
    comments_parser.add_argument("--max", type=int, default=10, help="Maximum comments (default: 10)")

    # transcript command
    transcript_parser = subparsers.add_parser("transcript", help="Get video transcript")
    transcript_parser.add_argument("video_id", help="YouTube video ID")
    transcript_parser.add_argument("--timed", action="store_true", help="Include timestamps")
    transcript_parser.add_argument("--search", type=str, help="Search for keyword/phrase in transcript")
    transcript_parser.add_argument("--context", type=int, default=1, help="Number of surrounding lines to show with search results (default: 1)")

    args = parser.parse_args()

    if args.command == "details":
        cmd_details(args)
    elif args.command == "comments":
        cmd_comments(args)
    elif args.command == "transcript":
        cmd_transcript(args)


if __name__ == "__main__":
    main()
