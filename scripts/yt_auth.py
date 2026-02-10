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
YouTube OAuth Authentication Script

Sets up and manages OAuth credentials for YouTube API access.
Tokens are stored at ~/.openclaw/skills-config/youtube/token.json

Usage:
    uv run yt_auth.py --setup    # Run OAuth flow (opens browser)
    uv run yt_auth.py --check    # Validate and refresh token if needed
    uv run yt_auth.py --revoke   # Revoke token and delete local file
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow OAuth over HTTP for localhost (required for local dev server callback)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for full YouTube access
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

CONFIG_DIR = Path.home() / ".openclaw" / "skills-config" / "youtube"
CLIENT_SECRET_PATH = CONFIG_DIR / "client_secret.json"
TOKEN_PATH = CONFIG_DIR / "token.json"


def setup_oauth() -> bool:
    """Run the OAuth consent flow and save credentials."""
    if not CLIENT_SECRET_PATH.exists():
        print(f"Error: client_secret.json not found at {CLIENT_SECRET_PATH}")
        print("Please copy your OAuth client credentials file there first.")
        return False

    print("Starting OAuth flow...")
    print("A browser window will open for you to authorize access.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)

    # Workaround: run_local_server() internally calls authorization_url(access_type="offline")
    # Some versions double-add access_type. Override the flow's code_verifier setup to avoid this.
    import webbrowser
    from wsgiref.simple_server import make_server
    import urllib.parse

    flow.redirect_uri = "http://localhost:8080/"
    auth_url, state = flow.authorization_url(access_type="offline")

    print(f"Opening browser for authorization...")
    webbrowser.open(auth_url)

    # Minimal local server to capture the callback
    auth_response = [None]
    class CallbackHandler:
        def __init__(self, environ, start_response):
            self.environ = environ
            self.start_response = start_response
        def __iter__(self):
            qs = self.environ.get("QUERY_STRING", "")
            auth_response[0] = f"http://localhost:8080/?{qs}"
            self.start_response("200 OK", [("Content-Type", "text/html")])
            yield b"<html><body><h1>Authorization complete!</h1><p>You can close this tab.</p></body></html>"

    server = make_server("localhost", 8080, CallbackHandler)
    server.handle_request()

    flow.fetch_token(authorization_response=auth_response[0])
    credentials = flow.credentials

    # Save credentials
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    print(f"\nSuccess! Token saved to {TOKEN_PATH}")
    print("You can now use the other YouTube scripts.")
    return True


def check_token() -> bool:
    """Validate token and refresh if needed."""
    if not TOKEN_PATH.exists():
        print(f"Error: No token found at {TOKEN_PATH}")
        print("Run with --setup first to authenticate.")
        return False

    try:
        creds = load_credentials()
        if creds is None:
            return False

        print(f"Token is valid.")
        print(f"Scopes: {', '.join(creds.scopes or [])}")
        return True
    except Exception as e:
        print(f"Error checking token: {e}")
        return False


def revoke_token() -> bool:
    """Revoke the token and delete the local file."""
    if not TOKEN_PATH.exists():
        print("No token file found. Nothing to revoke.")
        return True

    try:
        import requests
        creds = load_credentials()
        if creds and creds.token:
            # Revoke the token with Google
            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": creds.token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        TOKEN_PATH.unlink()
        print("Token revoked and deleted.")
        return True
    except Exception as e:
        print(f"Error revoking token: {e}")
        # Still try to delete local file
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
            print("Local token file deleted.")
        return False


def load_credentials() -> Credentials | None:
    """
    Load and refresh credentials from token.json.
    This function is duplicated in other scripts for standalone use.
    """
    if not TOKEN_PATH.exists():
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

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        print("Token expired, refreshing...")
        creds.refresh(Request())
        # Save refreshed token
        token_data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
        print("Token refreshed and saved.")

    return creds


def main():
    parser = argparse.ArgumentParser(
        description="YouTube OAuth Authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--setup", action="store_true", help="Run OAuth consent flow")
    group.add_argument("--check", action="store_true", help="Check if token is valid")
    group.add_argument("--revoke", action="store_true", help="Revoke and delete token")

    args = parser.parse_args()

    if args.setup:
        success = setup_oauth()
    elif args.check:
        success = check_token()
    elif args.revoke:
        success = revoke_token()
    else:
        parser.print_help()
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
