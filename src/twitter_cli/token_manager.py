"""Token and config management for Twitter OAuth 2.0"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import hashlib
import base64
import requests


# Config directory location:
# - macOS/Linux: ~/.twitter_cli/
# - Windows: C:\Users\YourName\.twitter_cli\
CONFIG_DIR = Path.home() / ".twitter_cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKENS_FILE = CONFIG_DIR / "tokens.json"


def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def save_config(client_id: str, client_secret: str) -> None:
    """Save client credentials to ~/.twitter_cli/config.json with secure permissions"""
    ensure_config_dir()
    config = {"client_id": client_id, "client_secret": client_secret}

    # Write to temporary file first
    temp_file = CONFIG_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(config, f)

    # Set permissions before moving (only owner can read/write)
    os.chmod(temp_file, 0o600)
    temp_file.replace(CONFIG_FILE)


def load_config() -> dict | None:
    """Load config from ~/.twitter_cli/config.json"""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to read config: {e}")


def save_tokens(
    access_token: str, refresh_token: str, expires_in: int, scope: str
) -> None:
    """Save tokens to ~/.twitter_cli/tokens.json with secure permissions"""
    ensure_config_dir()

    expires_at = int(time.time()) + expires_in
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "scope": scope,
    }

    # Write to temporary file first
    temp_file = TOKENS_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(tokens, f)

    # Set permissions before moving (only owner can read/write)
    os.chmod(temp_file, 0o600)
    temp_file.replace(TOKENS_FILE)


def load_tokens() -> dict | None:
    """Load tokens from ~/.twitter_cli/tokens.json"""
    if not TOKENS_FILE.exists():
        return None

    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to read tokens: {e}")


def is_token_expired(expires_at: int) -> bool:
    """Check if token is expired (with 60 second buffer)"""
    return int(time.time()) >= (expires_at - 60)


def get_valid_access_token() -> str:
    """Get a valid access token, refreshing if necessary"""
    tokens = load_tokens()

    if tokens is None:
        raise RuntimeError(
            "Not authenticated. Run 'twitter-cli auth' first."
        )

    if not is_token_expired(tokens["expires_at"]):
        return tokens["access_token"]

    # Token expired, refresh it
    return refresh_access_token()


def refresh_access_token() -> str:
    """Refresh access token using refresh token"""
    tokens = load_tokens()
    config = load_config()

    if tokens is None or config is None:
        raise RuntimeError(
            "Not authenticated. Run 'twitter-cli auth' first."
        )

    refresh_token = tokens["refresh_token"]
    client_id = config["client_id"]

    data = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "client_id": client_id,
    }

    try:
        response = requests.post(
            "https://api.x.com/2/oauth2/token",
            data=data,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to refresh token: {e}")

    try:
        token_data = response.json()
    except ValueError as e:
        raise RuntimeError(f"Invalid token response: {e}")

    # Save new tokens
    save_tokens(
        token_data["access_token"],
        token_data.get("refresh_token", refresh_token),  # Use old if not provided
        token_data["expires_in"],
        token_data.get("scope", tokens["scope"]),
    )

    return token_data["access_token"]


def clear_tokens() -> None:
    """Delete tokens.json file (for logout)"""
    if TOKENS_FILE.exists():
        TOKENS_FILE.unlink()


def get_token_expiration_time() -> datetime | None:
    """Get when the access token expires"""
    tokens = load_tokens()
    if tokens is None:
        return None
    return datetime.fromtimestamp(tokens["expires_at"])


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return load_tokens() is not None and load_config() is not None
