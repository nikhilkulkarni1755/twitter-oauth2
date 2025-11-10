"""X API wrapper for posting tweets"""

import requests
import os
from typing import Optional, List
from pathlib import Path


def upload_media(file_path: str, access_token: str) -> str:
    """
    Upload a media file (image or video) to X and get media_id.

    Uses the v1.1 media/upload endpoint with OAuth 2.0 Bearer token.

    Args:
        file_path: Path to the media file (image or video)
        access_token: Valid OAuth 2.0 access token

    Returns:
        media_id: The ID of uploaded media (as string)

    Raises:
        RuntimeError: On upload error or invalid file
    """
    file_path = os.path.expanduser(file_path)

    if not os.path.exists(file_path):
        raise RuntimeError(f"Media file not found: {file_path}")

    file_size = os.path.getsize(file_path)

    # Validate file type and size
    valid_image_types = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    valid_video_types = ('.mp4', '.mov')
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in valid_image_types:
        max_size = 15 * 1024 * 1024  # 15MB for images
        media_type = "image"
    elif file_ext in valid_video_types:
        max_size = 512 * 1024 * 1024  # 512MB for videos
        media_type = "video"
    else:
        raise RuntimeError(f"Unsupported file type: {file_ext}. Supported: {valid_image_types + valid_video_types}")

    if file_size > max_size:
        raise RuntimeError(f"File too large. Max size for {media_type}: {max_size / (1024*1024):.0f}MB")

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        with open(file_path, 'rb') as f:
            files = {'media_data': f}
            response = requests.post(
                "https://upload.x.com/1.1/media/upload.json",
                files=files,
                headers=headers,
                timeout=30,
            )
        response.raise_for_status()
    except requests.RequestException as e:
        try:
            error_data = response.json()
            if "errors" in error_data:
                error_msg = error_data["errors"][0].get("message", str(e))
            elif "error" in error_data:
                error_msg = error_data.get("error_description", error_data.get("error", str(e)))
            else:
                error_msg = str(e)
        except Exception:
            error_msg = str(e)

        # Check if 403 - might be permission issue
        if "403" in str(e):
            error_msg += " (Hint: Check that your app has 'Read and write' permissions in Twitter Developer Portal)"

        raise RuntimeError(f"Failed to upload media: {error_msg}")

    try:
        data = response.json()
        media_id = data.get("media_id_string") or str(data.get("media_id", ""))
        if not media_id:
            raise RuntimeError("No media_id in response")
        return media_id
    except (ValueError, KeyError) as e:
        raise RuntimeError(f"Invalid media upload response: {e}")


def post_tweet(text: str, access_token: str, media_files: Optional[List[str]] = None) -> dict:
    """
    Post a tweet using X API v2 with optional media files.

    POST https://api.x.com/2/tweets

    Args:
        text: Tweet content
        access_token: Valid OAuth 2.0 access token
        media_files: Optional list of file paths to media files to attach

    Returns:
        Response dict with tweet data

    Raises:
        RuntimeError: On API error with clear message
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {"text": text}

    # If media files provided, read them and send as multipart form data instead
    if media_files:
        # For media, we need to use multipart/form-data instead of JSON
        return _post_tweet_with_media(text, access_token, media_files)

    try:
        response = requests.post(
            "https://api.x.com/2/tweets",
            json=body,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        # Try to extract X API error message
        try:
            error_data = response.json()
            if "errors" in error_data:
                error_msg = error_data["errors"][0].get("message", str(e))
            else:
                error_msg = str(e)
        except (ValueError, KeyError, IndexError):
            error_msg = str(e)

        raise RuntimeError(f"Failed to post tweet: {error_msg}")

    try:
        data = response.json()
        return data.get("data", {})
    except ValueError as e:
        raise RuntimeError(f"Invalid tweet response: {e}")


def _post_tweet_with_media(text: str, access_token: str, media_files: List[str]) -> dict:
    """
    Post a tweet with media using the v1.1 endpoint with raw file uploads.

    Note: The v1.1 media upload endpoint requires OAuth 1.0a signatures, but we're
    using OAuth 2.0. This is a limitation of Twitter's API - they require OAuth 1.0a
    for v1.1 endpoints and OAuth 2.0 for v2 endpoints, but v2 doesn't support media
    uploads through the same mechanism.

    Workaround: We'll use the v1.1 statuses/update endpoint directly via the legacy
    API which should accept OAuth 2.0 Bearer tokens.
    """
    import mimetypes

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    media_ids = []

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
            raise RuntimeError(f"Unsupported file type: {file_ext}. Supported: {valid_image_types + valid_video_types}")

        if file_size > max_size:
            raise RuntimeError(f"File too large: {media_file} ({file_size / (1024*1024):.1f}MB)")

        # Upload via multipart file upload (raw binary)
        with open(media_file, 'rb') as f:
            files = {'media': f}
            try:
                response = requests.post(
                    "https://upload.x.com/1.1/media/upload.json",
                    files=files,
                    headers=headers,
                    timeout=60,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", str(e))
                except Exception:
                    error_msg = str(e)

                if "403" in str(e):
                    error_msg += "\n\nNote: Twitter's v1.1 media endpoint requires OAuth 1.0a signatures."
                    error_msg += "\nYour app is using OAuth 2.0, which the v1.1 endpoint doesn't accept."
                    error_msg += "\nConsider using the Twitter web interface or a tool with OAuth 1.0a support."

                raise RuntimeError(f"Failed to upload media: {error_msg}")

        try:
            data = response.json()
            media_id = data.get("media_id_string") or str(data.get("media_id", ""))
            if not media_id:
                raise RuntimeError("No media_id in response")
            media_ids.append(media_id)
        except (ValueError, KeyError) as e:
            raise RuntimeError(f"Invalid media upload response: {e}")

    # Now post the tweet with the media IDs
    headers_json = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "text": text,
        "media": {
            "media_ids": media_ids
        }
    }

    try:
        response = requests.post(
            "https://api.x.com/2/tweets",
            json=body,
            headers=headers_json,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        try:
            error_data = response.json()
            if "errors" in error_data:
                error_msg = error_data["errors"][0].get("message", str(e))
            else:
                error_msg = str(e)
        except Exception:
            error_msg = str(e)

        raise RuntimeError(f"Failed to post tweet: {error_msg}")

    try:
        data = response.json()
        return data.get("data", {})
    except ValueError as e:
        raise RuntimeError(f"Invalid tweet response: {e}")


def get_tweet_url(tweet_id: str, username: str) -> str:
    """Generate X URL for a tweet"""
    return f"https://x.com/{username}/status/{tweet_id}"
