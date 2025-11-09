"""X API wrapper for posting tweets"""

import requests
from typing import Optional


def post_tweet(text: str, access_token: str) -> dict:
    """
    Post a tweet using X API v2.

    POST https://api.x.com/2/tweets

    Args:
        text: Tweet content
        access_token: Valid OAuth 2.0 access token

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


def get_tweet_url(tweet_id: str, username: str) -> str:
    """Generate X URL for a tweet"""
    return f"https://x.com/{username}/status/{tweet_id}"
