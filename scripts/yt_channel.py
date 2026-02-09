#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-auth>=2.0.0",
#     "google-auth-oauthlib>=1.0.0",
#     "google-api-python-client>=2.0.0",
# ]
# ///
"""
YouTube Channel Script

Get channel information and list videos.

Usage:
    uv run yt_channel.py info                           # Channel stats
    uv run yt_channel.py videos [--max N] [--order X]   # List videos
    uv run yt_channel.py search <query> [--max N]       # Search channel videos

Orders: date (default), viewCount, rating, title
"""

import argparse
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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


def cmd_info(args):
    """Get channel information."""
    youtube = get_youtube_service()

    # Get authenticated user's channel
    response = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        mine=True
    ).execute()

    if not response.get("items"):
        print("No channel found for authenticated user.")
        return

    channel = response["items"][0]
    snippet = channel["snippet"]
    stats = channel["statistics"]

    print(f"Channel: {snippet['title']}")
    print(f"ID: {channel['id']}")
    print(f"Custom URL: {snippet.get('customUrl', 'N/A')}")
    print()
    print(f"Subscribers: {int(stats.get('subscriberCount', 0)):,}")
    print(f"Total Views: {int(stats.get('viewCount', 0)):,}")
    print(f"Video Count: {int(stats.get('videoCount', 0)):,}")
    print()
    print(f"Description: {snippet.get('description', 'N/A')[:200]}...")

    # Store channel ID for other commands
    uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"\nUploads Playlist ID: {uploads_playlist}")


def cmd_videos(args):
    """List channel videos."""
    youtube = get_youtube_service()

    # First get the uploads playlist ID
    channel_response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    if not channel_response.get("items"):
        print("No channel found.")
        return

    uploads_playlist = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Get videos from uploads playlist
    videos = []
    next_page_token = None
    max_results = args.max

    while len(videos) < max_results:
        request_count = min(50, max_results - len(videos))
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist,
            maxResults=request_count,
            pageToken=next_page_token
        ).execute()

        videos.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    # Get video statistics
    video_ids = [v["contentDetails"]["videoId"] for v in videos]

    stats_response = youtube.videos().list(
        part="statistics,contentDetails",
        id=",".join(video_ids[:50])  # API limit
    ).execute()

    stats_map = {v["id"]: v for v in stats_response.get("items", [])}

    # Sort if requested
    if args.order == "viewCount":
        videos.sort(
            key=lambda v: int(stats_map.get(v["contentDetails"]["videoId"], {}).get("statistics", {}).get("viewCount", 0)),
            reverse=True
        )

    print(f"{'Title':<50} {'Views':>12} {'Published'}")
    print("-" * 80)

    for video in videos[:max_results]:
        vid_id = video["contentDetails"]["videoId"]
        title = video["snippet"]["title"][:48]
        published = video["snippet"]["publishedAt"][:10]
        stats = stats_map.get(vid_id, {}).get("statistics", {})
        views = int(stats.get("viewCount", 0))

        print(f"{title:<50} {views:>12,} {published}")
        print(f"  ID: {vid_id}")


def cmd_search(args):
    """Search within own channel."""
    youtube = get_youtube_service()

    # Get channel ID
    channel_response = youtube.channels().list(
        part="id",
        mine=True
    ).execute()

    if not channel_response.get("items"):
        print("No channel found.")
        return

    channel_id = channel_response["items"][0]["id"]

    # Search within channel (costs 100 quota units)
    response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        q=args.query,
        type="video",
        maxResults=args.max,
        order="relevance"
    ).execute()

    if not response.get("items"):
        print(f"No videos found matching '{args.query}'")
        return

    print(f"Search results for '{args.query}':\n")

    for item in response["items"]:
        snippet = item["snippet"]
        video_id = item["id"]["videoId"]
        print(f"• {snippet['title']}")
        print(f"  ID: {video_id}")
        print(f"  Published: {snippet['publishedAt'][:10]}")
        print()


def main():
    parser = argparse.ArgumentParser(description="YouTube Channel Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info command
    subparsers.add_parser("info", help="Get channel information")

    # videos command
    videos_parser = subparsers.add_parser("videos", help="List channel videos")
    videos_parser.add_argument("--max", type=int, default=10, help="Maximum videos (default: 10)")
    videos_parser.add_argument("--order", choices=["date", "viewCount"], default="date", help="Sort order")

    # search command
    search_parser = subparsers.add_parser("search", help="Search channel videos")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max", type=int, default=10, help="Maximum results (default: 10)")

    args = parser.parse_args()

    if args.command == "info":
        cmd_info(args)
    elif args.command == "videos":
        cmd_videos(args)
    elif args.command == "search":
        cmd_search(args)


if __name__ == "__main__":
    main()
