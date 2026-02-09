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
YouTube Analytics Script

Get YouTube Studio analytics data.

Usage:
    uv run yt_analytics.py overview [--days 28]          # Channel overview
    uv run yt_analytics.py top-videos [--days 28] [--max 10]  # Top performers
    uv run yt_analytics.py video <VIDEO_ID> [--days 28]  # Single video stats
    uv run yt_analytics.py demographics [--days 28]      # Age/gender breakdown
    uv run yt_analytics.py traffic [--days 28]           # Traffic sources
    uv run yt_analytics.py geography [--days 28]         # Views by country
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
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


def get_analytics_service():
    """Build YouTube Analytics API service."""
    creds = load_credentials()
    if not creds:
        sys.exit(1)
    return build("youtubeAnalytics", "v2", credentials=creds)


def get_youtube_service():
    """Build YouTube Data API service."""
    creds = load_credentials()
    if not creds:
        sys.exit(1)
    return build("youtube", "v3", credentials=creds)


def get_date_range(days: int) -> tuple[str, str]:
    """Get start and end dates for analytics query."""
    end = datetime.now() - timedelta(days=1)  # Analytics has 1-2 day delay
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_channel_id() -> str:
    """Get authenticated user's channel ID."""
    youtube = get_youtube_service()
    response = youtube.channels().list(part="id", mine=True).execute()
    if not response.get("items"):
        print("No channel found for authenticated user.")
        sys.exit(1)
    return response["items"][0]["id"]


def format_duration(minutes: float) -> str:
    """Format watch time minutes to human readable."""
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f} hrs"
    days = hours / 24
    return f"{days:.1f} days"


def cmd_overview(args):
    """Get channel overview analytics."""
    analytics = get_analytics_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,comments,shares,estimatedRevenue",
    ).execute()

    if not response.get("rows"):
        print("No data available for this period.")
        return

    row = response["rows"][0]
    views, watch_minutes, subs_gained, subs_lost, likes, comments, shares, revenue = row

    print(f"Channel Overview ({args.days} days: {start_date} to {end_date})")
    print("=" * 50)
    print()
    print(f"Views:           {int(views):>12,}")
    print(f"Watch Time:      {format_duration(watch_minutes):>12}")
    print(f"Subscribers:     {int(subs_gained - subs_lost):>+12,} ({int(subs_gained):,} gained, {int(subs_lost):,} lost)")
    print()
    print(f"Likes:           {int(likes):>12,}")
    print(f"Comments:        {int(comments):>12,}")
    print(f"Shares:          {int(shares):>12,}")
    print()
    if revenue > 0:
        print(f"Est. Revenue:    ${revenue:>11,.2f}")


def cmd_top_videos(args):
    """Get top performing videos."""
    analytics = get_analytics_service()
    youtube = get_youtube_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,estimatedRevenue",
        dimensions="video",
        sort="-views",
        maxResults=args.max,
    ).execute()

    if not response.get("rows"):
        print("No data available for this period.")
        return

    # Get video titles
    video_ids = [row[0] for row in response["rows"]]
    videos_response = youtube.videos().list(
        part="snippet",
        id=",".join(video_ids[:50])
    ).execute()

    title_map = {v["id"]: v["snippet"]["title"] for v in videos_response.get("items", [])}

    print(f"Top {args.max} Videos ({args.days} days)")
    print("=" * 80)
    print()
    print(f"{'Title':<45} {'Views':>10} {'Watch Time':>12} {'Revenue':>10}")
    print("-" * 80)

    for row in response["rows"]:
        video_id, views, watch_minutes, revenue = row
        title = title_map.get(video_id, video_id)[:43]
        watch_str = format_duration(watch_minutes)

        revenue_str = f"${revenue:.2f}" if revenue > 0 else "-"
        print(f"{title:<45} {int(views):>10,} {watch_str:>12} {revenue_str:>10}")


def cmd_video(args):
    """Get analytics for a specific video."""
    analytics = get_analytics_service()
    youtube = get_youtube_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    # Get video title
    video_response = youtube.videos().list(
        part="snippet",
        id=args.video_id
    ).execute()

    video_title = args.video_id
    if video_response.get("items"):
        video_title = video_response["items"][0]["snippet"]["title"]

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares,estimatedRevenue",
        filters=f"video=={args.video_id}",
    ).execute()

    if not response.get("rows"):
        print(f"No data available for video: {args.video_id}")
        return

    row = response["rows"][0]
    views, watch_minutes, avg_duration, subs, likes, comments, shares, revenue = row

    print(f"Video: {video_title}")
    print(f"ID: {args.video_id}")
    print(f"Period: {start_date} to {end_date} ({args.days} days)")
    print("=" * 50)
    print()
    print(f"Views:            {int(views):>12,}")
    print(f"Watch Time:       {format_duration(watch_minutes):>12}")
    print(f"Avg View Duration:{int(avg_duration):>11}s")
    print()
    print(f"Subscribers:      {int(subs):>+12,}")
    print(f"Likes:            {int(likes):>12,}")
    print(f"Comments:         {int(comments):>12,}")
    print(f"Shares:           {int(shares):>12,}")
    print()
    if revenue > 0:
        print(f"Est. Revenue:     ${revenue:>11,.2f}")


def cmd_demographics(args):
    """Get viewer demographics."""
    analytics = get_analytics_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="viewerPercentage",
        dimensions="ageGroup,gender",
    ).execute()

    if not response.get("rows"):
        print("No demographic data available.")
        return

    print(f"Viewer Demographics ({args.days} days)")
    print("=" * 40)
    print()

    # Organize by gender
    male_data = {}
    female_data = {}

    for row in response["rows"]:
        age_group, gender, percentage = row
        if gender == "male":
            male_data[age_group] = percentage
        else:
            female_data[age_group] = percentage

    age_groups = ["age13-17", "age18-24", "age25-34", "age35-44", "age45-54", "age55-64", "age65-"]
    age_labels = ["13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

    print(f"{'Age':<10} {'Male':>10} {'Female':>10}")
    print("-" * 30)

    for group, label in zip(age_groups, age_labels):
        male_pct = male_data.get(group, 0)
        female_pct = female_data.get(group, 0)
        print(f"{label:<10} {male_pct:>9.1f}% {female_pct:>9.1f}%")


def cmd_traffic(args):
    """Get traffic source breakdown."""
    analytics = get_analytics_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views",
        dimensions="insightTrafficSourceType",
        sort="-views",
    ).execute()

    if not response.get("rows"):
        print("No traffic data available.")
        return

    print(f"Traffic Sources ({args.days} days)")
    print("=" * 50)
    print()

    total_views = sum(row[1] for row in response["rows"])

    print(f"{'Source':<35} {'Views':>10} {'%':>8}")
    print("-" * 55)

    source_names = {
        "YT_SEARCH": "YouTube Search",
        "EXT_URL": "External Websites",
        "RELATED_VIDEO": "Suggested Videos",
        "YT_CHANNEL": "Channel Pages",
        "YT_OTHER_PAGE": "Other YouTube",
        "SUBSCRIBER": "Subscriptions",
        "NOTIFICATION": "Notifications",
        "PLAYLIST": "Playlists",
        "NO_LINK_OTHER": "Direct/Unknown",
        "END_SCREEN": "End Screens",
        "ANNOTATION": "Cards",
        "SHORTS": "Shorts Feed",
        "YT_PLAYLIST_PAGE": "Playlist Page",
        "HASHTAGS": "Hashtags",
    }

    for row in response["rows"]:
        source, views = row
        source_name = source_names.get(source, source)
        pct = (views / total_views) * 100 if total_views > 0 else 0
        print(f"{source_name:<35} {int(views):>10,} {pct:>7.1f}%")


def cmd_geography(args):
    """Get views by country."""
    analytics = get_analytics_service()
    channel_id = get_channel_id()
    start_date, end_date = get_date_range(args.days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched",
        dimensions="country",
        sort="-views",
        maxResults=20,
    ).execute()

    if not response.get("rows"):
        print("No geographic data available.")
        return

    print(f"Top Countries ({args.days} days)")
    print("=" * 50)
    print()

    total_views = sum(row[1] for row in response["rows"])

    print(f"{'Country':<25} {'Views':>12} {'Watch Time':>12}")
    print("-" * 50)

    for row in response["rows"]:
        country, views, watch_minutes = row
        watch_str = format_duration(watch_minutes)
        print(f"{country:<25} {int(views):>12,} {watch_str:>12}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Analytics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # overview command
    overview_parser = subparsers.add_parser("overview", help="Channel overview")
    overview_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")

    # top-videos command
    top_parser = subparsers.add_parser("top-videos", help="Top performing videos")
    top_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")
    top_parser.add_argument("--max", type=int, default=10, help="Max videos (default: 10)")

    # video command
    video_parser = subparsers.add_parser("video", help="Single video analytics")
    video_parser.add_argument("video_id", help="YouTube video ID")
    video_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")

    # demographics command
    demo_parser = subparsers.add_parser("demographics", help="Viewer demographics")
    demo_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")

    # traffic command
    traffic_parser = subparsers.add_parser("traffic", help="Traffic sources")
    traffic_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")

    # geography command
    geo_parser = subparsers.add_parser("geography", help="Views by country")
    geo_parser.add_argument("--days", type=int, default=28, help="Days to analyze (default: 28)")

    args = parser.parse_args()

    commands = {
        "overview": cmd_overview,
        "top-videos": cmd_top_videos,
        "video": cmd_video,
        "demographics": cmd_demographics,
        "traffic": cmd_traffic,
        "geography": cmd_geography,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
