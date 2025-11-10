"""Tweepy-based media posting using OAuth 1.0a"""

import os
import json
from pathlib import Path
from typing import Tuple


def get_media_credentials_path() -> Path:
    """Get path to media credentials file (~/.twitter_cli/media_credentials.json)"""
    credentials_dir = Path.home() / ".twitter_cli"
    credentials_dir.mkdir(mode=0o700, exist_ok=True)
    return credentials_dir / "media_credentials.json"


def save_media_credentials(consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str) -> None:
    """Save OAuth 1.0a credentials for media posting"""
    creds_path = get_media_credentials_path()
    credentials = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "access_token": access_token,
        "access_token_secret": access_token_secret,
    }

    with open(creds_path, "w") as f:
        json.dump(credentials, f)

    os.chmod(creds_path, 0o600)  # Secure file permissions


def load_media_credentials() -> dict:
    """Load OAuth 1.0a credentials for media posting"""
    creds_path = get_media_credentials_path()

    if not creds_path.exists():
        return {}

    with open(creds_path, "r") as f:
        return json.load(f)


def has_media_credentials() -> bool:
    """Check if media credentials are saved"""
    creds = load_media_credentials()
    required_keys = {"consumer_key", "consumer_secret", "access_token", "access_token_secret"}
    return required_keys.issubset(creds.keys())


def post_tweet_with_media(text: str, media_files: list) -> dict:
    """
    Post a tweet with media (images/videos) using tweepy and OAuth 1.0a.

    Args:
        text: Tweet content
        media_files: List of file paths to media files

    Returns:
        Dict with tweet data including ID

    Raises:
        RuntimeError: If credentials not found or tweet posting fails
    """
    try:
        import tweepy
    except ImportError:
        raise RuntimeError(
            "tweepy is not installed. Install it with: pip install tweepy"
        )

    # Load credentials
    creds = load_media_credentials()
    if not has_media_credentials():
        raise RuntimeError(
            "Media credentials not found. Run 'twitter-cli auth-media' first to set up OAuth 1.0a"
        )

    # Validate media files
    for media_file in media_files:
        media_file = os.path.expanduser(media_file)

        if not os.path.exists(media_file):
            raise RuntimeError(f"Media file not found: {media_file}")

        file_size = os.path.getsize(media_file)
        file_ext = os.path.splitext(media_file)[1].lower()

        # Validate file type and size
        valid_image_types = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        valid_video_types = ('.mp4', '.mov')

        if file_ext in valid_image_types:
            max_size = 15 * 1024 * 1024  # 15MB for images
        elif file_ext in valid_video_types:
            max_size = 512 * 1024 * 1024  # 512MB for videos
        else:
            raise RuntimeError(
                f"Unsupported file type: {file_ext}. Supported: {valid_image_types + valid_video_types}"
            )

        if file_size > max_size:
            raise RuntimeError(
                f"File too large: {media_file} ({file_size / (1024*1024):.1f}MB)"
            )

    try:
        # Create OAuth 1.0a handler
        auth = tweepy.OAuthHandler(creds["consumer_key"], creds["consumer_secret"])
        auth.set_access_token(creds["access_token"], creds["access_token_secret"])

        # Create API client
        api = tweepy.API(auth)

        # Upload media files
        media_ids = []
        for media_file in media_files:
            media_file = os.path.expanduser(media_file)
            try:
                response = api.media_upload(media_file)
                media_ids.append(str(response.media_id))
            except tweepy.TweepyException as e:
                raise RuntimeError(f"Failed to upload media {media_file}: {e}")

        # Post tweet with media
        try:
            status = api.update_status(status=text, media_ids=media_ids)
            return {
                "id": str(status.id),
                "text": status.text,
                "created_at": str(status.created_at),
            }
        except tweepy.TweepyException as e:
            raise RuntimeError(f"Failed to post tweet: {e}")

    except tweepy.TweepyException as e:
        raise RuntimeError(f"Authentication error: {e}")


def clear_media_credentials() -> None:
    """Clear saved media credentials"""
    creds_path = get_media_credentials_path()
    if creds_path.exists():
        creds_path.unlink()
