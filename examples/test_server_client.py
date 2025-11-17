#!/usr/bin/env python3
"""Example client script for testing the Twitter OAuth2.0 server"""

import requests
import json
from pathlib import Path

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def check_server_health():
    """Check if the server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Server is running")
            return True
        else:
            print("✗ Server returned unexpected status code:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Start it with: python -m twitter_server")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False


def get_server_status():
    """Get server status and authentication info"""
    try:
        response = requests.get(f"{SERVER_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print("\n--- Server Status ---")
            print(f"Authenticated: {data.get('authenticated')}")
            print(f"Username: {data.get('username')}")
            print(f"Token expires at: {data.get('token_expires_at')}")
            scopes = data.get('scopes', [])
            if scopes:
                print(f"Scopes: {', '.join(scopes)}")
            return True
        elif response.status_code == 401:
            print("\n✗ Server is not authenticated")
            print("  Run: twitter-cli auth")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def post_text_tweet(text):
    """Post a text-only tweet"""
    try:
        payload = {"text": text}
        response = requests.post(
            f"{SERVER_URL}/tweet",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Tweet posted successfully!")
            print(f"  Tweet ID: {data.get('tweet_id')}")
            print(f"  URL: https://x.com/search?q={data.get('tweet_id')}")
            return True
        else:
            print(f"\n✗ Failed to post tweet: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def post_tweet_with_media(text, media_paths):
    """Post a tweet with media"""
    try:
        payload = {"text": text, "media_paths": media_paths}
        response = requests.post(
            f"{SERVER_URL}/tweet-media",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Tweet with media posted successfully!")
            print(f"  Tweet ID: {data.get('tweet_id')}")
            print(f"  Media count: {data.get('media_count')}")
            return True
        else:
            print(f"\n✗ Failed to post tweet: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Interactive test client"""
    print("Twitter OAuth2.0 Server - Test Client")
    print("====================================\n")

    # Check server health
    if not check_server_health():
        return

    # Get status
    get_server_status()

    # Interactive menu
    while True:
        print("\n--- Options ---")
        print("1. Post a text tweet")
        print("2. Post a tweet with media")
        print("3. Check server status")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            text = input("Enter tweet text: ").strip()
            if text:
                post_text_tweet(text)

        elif choice == "2":
            text = input("Enter tweet text: ").strip()
            if text:
                media_input = input("Enter comma-separated media file paths: ").strip()
                media_paths = [p.strip() for p in media_input.split(",") if p.strip()]
                if media_paths:
                    post_tweet_with_media(text, media_paths)
                else:
                    print("No media paths provided")

        elif choice == "3":
            get_server_status()

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
