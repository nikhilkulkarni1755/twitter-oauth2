"""Click CLI commands for Twitter OAuth 2.0 authentication and tweeting"""

import click
import webbrowser
from datetime import datetime

from . import oauth, token_manager, api, media_manager


@click.group()
def cli():
    """Twitter CLI - Post tweets from your terminal"""
    pass


@cli.command()
@click.option(
    "--client-id",
    default=None,
    help="OAuth 2.0 Client ID (will prompt if not provided)",
)
@click.option(
    "--client-secret",
    default=None,
    help="OAuth 2.0 Client Secret (will prompt if not provided)",
)
def auth(client_id: str, client_secret: str):
    """
    Authenticate with Twitter OAuth 2.0 PKCE.

    Guides user through browser-based OAuth flow.
    """
    try:
        # Prompt for credentials if not provided
        if not client_id:
            client_id = click.prompt("Enter your Client ID")

        if not client_secret:
            client_secret = click.prompt("Enter your Client Secret", hide_input=True)

        # Save config
        click.echo("Saving credentials...")
        token_manager.save_config(client_id, client_secret)

        # Generate PKCE pair
        click.echo("Generating PKCE challenge...")
        code_verifier, code_challenge = oauth.generate_pkce_pair()
        state = oauth.generate_state()

        # Build auth URL
        redirect_uri = "http://localhost:8085/callback"
        auth_url = oauth.build_auth_url(client_id, redirect_uri, code_challenge, state)

        # Open browser
        click.echo("\nOpening browser for authentication...")
        click.echo(f"If browser doesn't open, visit: {auth_url}\n")
        webbrowser.open(auth_url)

        # Start callback server
        click.echo("Waiting for authorization callback...")
        authorization_code = oauth.start_callback_server(state)

        # Exchange code for tokens
        click.echo("Exchanging authorization code for tokens...")
        token_data = oauth.exchange_code_for_tokens(
            authorization_code, code_verifier, client_id, client_secret, redirect_uri
        )

        # Save tokens
        token_manager.save_tokens(
            token_data["access_token"],
            token_data["refresh_token"],
            token_data["expires_in"],
            token_data.get("scope", ""),
        )

        # Get user info
        click.echo("Retrieving user information...")
        user_info = oauth.get_user_info(token_data["access_token"])
        username = user_info.get("username", "user")

        click.echo(f"\n✓ Successfully authenticated as @{username}")
        click.echo(f"Access token expires at: {token_manager.get_token_expiration_time()}")

    except Exception as e:
        click.echo(f"✗ Authentication failed: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("text")
def tweet(text: str):
    """
    Post a text-only tweet.

    Usage: twitter-cli tweet "Hello world"
    """
    try:
        # Check if authenticated
        if not token_manager.is_authenticated():
            click.echo(
                "✗ Not authenticated. Run 'twitter-cli auth' first.", err=True
            )
            raise SystemExit(1)

        # Get valid access token (auto-refresh if expired)
        click.echo("Posting tweet...")
        access_token = token_manager.get_valid_access_token()

        # Post tweet
        tweet_data = api.post_tweet(text, access_token)

        # Get user info to build URL
        user_info = oauth.get_user_info(access_token)
        username = user_info.get("username", "user")
        tweet_id = tweet_data.get("id", "")

        if tweet_id:
            tweet_url = api.get_tweet_url(tweet_id, username)
            click.echo(f"✓ Tweet posted: {tweet_url}")
        else:
            click.echo("✓ Tweet posted successfully")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("text")
@click.argument("media_paths", nargs=-1, required=True)
def tweet_media(text: str, media_paths):
    """
    Post a tweet with pictures and/or videos.

    Usage: twitter-cli tweet-media "Check this out!" /pictures/photo.jpg /videos/clip.mp4
    """
    try:
        # Check if authenticated
        if not token_manager.is_authenticated():
            click.echo(
                "✗ Not authenticated. Run 'twitter-cli auth' first.", err=True
            )
            raise SystemExit(1)

        # Get valid access token (auto-refresh if expired)
        access_token = token_manager.get_valid_access_token()

        # Post tweet with media (uploads handled internally)
        click.echo(f"Processing {len(media_paths)} media file(s)...")
        for i, media_path in enumerate(media_paths, 1):
            click.echo(f"  [{i}/{len(media_paths)}] {media_path}")

        click.echo("Uploading and posting tweet...")
        tweet_data = api.post_tweet(text, access_token, media_files=list(media_paths))

        # Get user info to build URL
        user_info = oauth.get_user_info(access_token)
        username = user_info.get("username", "user")
        tweet_id = tweet_data.get("id", "")

        if tweet_id:
            tweet_url = api.get_tweet_url(tweet_id, username)
            click.echo(f"✓ Tweet posted: {tweet_url}")
        else:
            click.echo("✓ Tweet posted successfully")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def status():
    """
    Show authentication status.

    Displays authentication status, username, token expiration, and scopes.
    """
    try:
        if not token_manager.is_authenticated():
            click.echo("✗ Not authenticated. Run 'twitter-cli auth' to get started.")
            return

        # Load tokens to get info
        tokens = token_manager.load_tokens()
        config = token_manager.load_config()

        if not tokens or not config:
            click.echo("✗ Configuration incomplete")
            return

        # Get user info
        access_token = token_manager.get_valid_access_token()
        user_info = oauth.get_user_info(access_token)
        username = user_info.get("username", "unknown")

        # Get expiration time
        expires_at = token_manager.get_token_expiration_time()
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S") if expires_at else "Unknown"

        click.echo(f"✓ Authenticated as @{username}")
        click.echo(f"Access token expires: {expires_str}")
        click.echo(f"Refresh token: valid")
        click.echo(f"Scopes: {tokens.get('scope', 'unknown')}")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def logout():
    """
    Logout and clear stored tokens.

    Removes stored authentication tokens and credentials.
    """
    try:
        if not token_manager.is_authenticated():
            click.echo("Not authenticated")
            return

        if click.confirm("Are you sure you want to logout?"):
            token_manager.clear_tokens()
            click.echo("✓ Logged out successfully")
            click.echo("Run 'twitter-cli auth' to authenticate again")
        else:
            click.echo("Logout cancelled")

    except Exception as e:
        click.echo(f"✗ Error during logout: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option(
    "--consumer-key",
    default=None,
    help="OAuth 1.0a Consumer Key (will prompt if not provided)",
)
@click.option(
    "--consumer-secret",
    default=None,
    help="OAuth 1.0a Consumer Secret (will prompt if not provided)",
)
@click.option(
    "--access-token",
    default=None,
    help="OAuth 1.0a Access Token (will prompt if not provided)",
)
@click.option(
    "--access-token-secret",
    default=None,
    help="OAuth 1.0a Access Token Secret (will prompt if not provided)",
)
def auth_media(consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):
    """
    Setup OAuth 1.0a credentials for media posting with tweepy.

    These credentials are different from the OAuth 2.0 credentials.
    You can find them in your Twitter Developer Portal:
    1. Go to https://developer.x.com/en/portal/dashboard
    2. Select your app
    3. Go to "Keys and tokens" tab
    4. Under "Authentication Tokens and Keys", you'll find:
       - API Key (Consumer Key)
       - API Key Secret (Consumer Secret)
       - Access Token
       - Access Token Secret
    """
    try:
        # Prompt for credentials if not provided
        if not consumer_key:
            consumer_key = click.prompt("Enter your Consumer Key (API Key)")

        if not consumer_secret:
            consumer_secret = click.prompt("Enter your Consumer Secret (API Key Secret)", hide_input=True)

        if not access_token:
            access_token = click.prompt("Enter your Access Token")

        if not access_token_secret:
            access_token_secret = click.prompt("Enter your Access Token Secret", hide_input=True)

        # Save credentials
        click.echo("Saving media credentials...")
        media_manager.save_media_credentials(consumer_key, consumer_secret, access_token, access_token_secret)

        click.echo("✓ Media credentials saved successfully")
        click.echo("You can now use 'twitter-cli tweet-media' to post tweets with images/videos")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("text")
@click.argument("media_paths", nargs=-1, required=True)
def tweet_media(text: str, media_paths):
    """
    Post a tweet with pictures and/or videos using OAuth 1.0a.

    Usage: twitter-cli tweet-media "Check this out!" /pictures/photo.jpg /videos/clip.mp4

    Note: You must run 'twitter-cli auth-media' first to set up OAuth 1.0a credentials.
    """
    try:
        # Check if media credentials are set up
        if not media_manager.has_media_credentials():
            click.echo(
                "✗ Media credentials not found. Run 'twitter-cli auth-media' first.", err=True
            )
            raise SystemExit(1)

        # Post tweet with media
        click.echo(f"Processing {len(media_paths)} media file(s)...")
        for i, media_path in enumerate(media_paths, 1):
            click.echo(f"  [{i}/{len(media_paths)}] {media_path}")

        click.echo("Uploading and posting tweet...")
        tweet_data = media_manager.post_tweet_with_media(text, list(media_paths))

        tweet_id = tweet_data.get("id", "")
        if tweet_id:
            tweet_url = f"https://x.com/i/web/status/{tweet_id}"
            click.echo(f"✓ Tweet posted: {tweet_url}")
        else:
            click.echo("✓ Tweet posted successfully")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def logout_media():
    """
    Logout from media posting by clearing stored OAuth 1.0a credentials.

    Removes stored media authentication credentials.
    """
    try:
        if not media_manager.has_media_credentials():
            click.echo("Media credentials not found")
            return

        if click.confirm("Are you sure you want to clear media credentials?"):
            media_manager.clear_media_credentials()
            click.echo("✓ Media credentials cleared successfully")
            click.echo("Run 'twitter-cli auth-media' to set up again")
        else:
            click.echo("Clear cancelled")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


# Auto-tweet commands
import sys
import os

# Add Auto-Tweet to path if available
auto_tweet_path = os.path.join(os.path.dirname(__file__), '../../Auto-Tweet')
if os.path.exists(auto_tweet_path):
    sys.path.insert(0, auto_tweet_path)


@cli.command()
@click.option(
    "--angle",
    default=None,
    help="Optional tweet angle. If not provided, generates one from Kubernetes docs",
)
def auto_tweet_once(angle: str):
    """
    Generate and post a single tweet based on Kubernetes documentation.

    Uses local Qwen LLM to generate a novel angle and tweet from Kubernetes docs.
    Tracks angles and tweets to avoid repetition.
    """
    try:
        if not token_manager.is_authenticated():
            click.echo(
                "✗ Not authenticated. Run 'twitter-cli auth' first.", err=True
            )
            raise SystemExit(1)

        import sys
        from pathlib import Path

        # Add Auto-Tweet to path
        auto_tweet_path = str(Path(__file__).parent.parent.parent / "Auto-Tweet")
        if auto_tweet_path not in sys.path:
            sys.path.insert(0, auto_tweet_path)

        from auto_tweeter import AutoTweeter

        click.echo("Initializing auto-tweeter...")
        auto_tweeter = AutoTweeter()

        # Check LLM health
        click.echo("Checking Qwen LLM connection...")
        if not auto_tweeter.qwen.health_check():
            click.echo(
                "✗ Cannot connect to Qwen LLM. Ensure LMStudio is running at http://192.168.1.98:1234/v1",
                err=True
            )
            raise SystemExit(1)

        # Get access token
        access_token = token_manager.get_valid_access_token()

        # Generate tweet
        click.echo("Fetching Kubernetes documentation...")
        kubernetes_content = auto_tweeter.fetch_kubernetes_content()

        if angle:
            click.echo(f"Using provided angle: {angle}")
        else:
            click.echo("Generating novel tweet angle...")
            angle = auto_tweeter.generate_tweet_angle(kubernetes_content)
            click.echo(f"Angle: {angle}")

        click.echo("Generating tweet from angle...")
        tweet_text = auto_tweeter.qwen.generate_tweet_from_angle(angle)
        click.echo(f"\nTweet:\n{tweet_text}\n")

        if click.confirm("Post this tweet?"):
            click.echo("Posting tweet...")
            tweet_data = auto_tweeter.post_tweet(tweet_text, access_token, angle=angle)
            tweet_id = tweet_data.get("id", "")

            if tweet_id:
                user_info = oauth.get_user_info(access_token)
                username = user_info.get("username", "user")
                tweet_url = api.get_tweet_url(tweet_id, username)
                click.echo(f"✓ Tweet posted: {tweet_url}")
            else:
                click.echo("✓ Tweet posted successfully")
        else:
            click.echo("Tweet cancelled")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option(
    "--count",
    default=1,
    help="Number of tweets to generate and post (default 1)",
)
def auto_tweet_batch(count: int):
    """
    Generate and post multiple tweets automatically.

    Each tweet will have a unique angle based on Kubernetes documentation.
    """
    try:
        if not token_manager.is_authenticated():
            click.echo(
                "✗ Not authenticated. Run 'twitter-cli auth' first.", err=True
            )
            raise SystemExit(1)

        import sys
        from pathlib import Path

        # Add Auto-Tweet to path
        auto_tweet_path = str(Path(__file__).parent.parent.parent / "Auto-Tweet")
        if auto_tweet_path not in sys.path:
            sys.path.insert(0, auto_tweet_path)

        from auto_tweeter import AutoTweeter

        click.echo("Initializing auto-tweeter...")
        auto_tweeter = AutoTweeter()

        # Check LLM health
        click.echo("Checking Qwen LLM connection...")
        if not auto_tweeter.qwen.health_check():
            click.echo(
                "✗ Cannot connect to Qwen LLM. Ensure LMStudio is running at http://192.168.1.98:1234/v1",
                err=True
            )
            raise SystemExit(1)

        # Get access token
        access_token = token_manager.get_valid_access_token()

        click.echo(f"Generating and posting {count} tweet(s)...")
        results = auto_tweeter.auto_tweet(access_token, count=count)

        for i, result in enumerate(results, 1):
            click.echo(f"\n[{i}/{count}]")
            if result.get("success"):
                tweet_text = result.get("tweet", "")[:60] + "..."
                angle = result.get("angle", "")
                click.echo(f"  Angle: {angle}")
                click.echo(f"  Tweet: {tweet_text}")
                click.echo("  ✓ Posted successfully")
            else:
                error = result.get("error", "Unknown error")
                click.echo(f"  ✗ Error: {error}")

        # Show stats
        stats = auto_tweeter.get_stats()
        click.echo(f"\nStats: {stats['total_tweets']} tweets posted, {stats['total_angles']} angles used")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option(
    "--hours",
    default=None,
    help="Comma-separated list of hours (0-23) to post tweets. E.g. '9,12,15,18'",
)
def auto_tweet_schedule(hours: str):
    """
    Schedule automatic hourly tweets.

    Tweets will be generated from Kubernetes documentation and posted at specified times.
    """
    try:
        if not token_manager.is_authenticated():
            click.echo(
                "✗ Not authenticated. Run 'twitter-cli auth' first.", err=True
            )
            raise SystemExit(1)

        import sys
        from pathlib import Path

        # Add Auto-Tweet to path
        auto_tweet_path = str(Path(__file__).parent.parent.parent / "Auto-Tweet")
        if auto_tweet_path not in sys.path:
            sys.path.insert(0, auto_tweet_path)

        from auto_tweeter import AutoTweeter
        from scheduler import TweetScheduler

        click.echo("Initializing scheduler...")
        auto_tweeter = AutoTweeter()

        # Check LLM health
        click.echo("Checking Qwen LLM connection...")
        if not auto_tweeter.qwen.health_check():
            click.echo(
                "✗ Cannot connect to Qwen LLM. Ensure LMStudio is running at http://192.168.1.98:1234/v1",
                err=True
            )
            raise SystemExit(1)

        # Get access token
        access_token = token_manager.get_valid_access_token()

        # Parse hours
        if hours:
            try:
                hour_list = [int(h.strip()) for h in hours.split(",")]
                for h in hour_list:
                    if not (0 <= h <= 23):
                        raise ValueError(f"Invalid hour: {h}. Must be 0-23.")
            except ValueError as e:
                click.echo(f"✗ Invalid hours format: {e}", err=True)
                raise SystemExit(1)
        else:
            # Default: every hour at minute 0
            hour_list = None

        scheduler = TweetScheduler(access_token, auto_tweeter=auto_tweeter)

        if hour_list:
            message = scheduler.schedule_multiple_hourly(hour_list)
            click.echo(f"✓ {message}")
        else:
            message = scheduler.schedule_hourly_tweet()
            click.echo(f"✓ {message}")

        # Start scheduler
        click.echo("Starting scheduler in background...")
        scheduler.start()

        # Show scheduled jobs
        jobs = scheduler.get_scheduled_jobs()
        click.echo(f"✓ Scheduler is now running with {len(jobs)} job(s)")
        click.echo("\nScheduled jobs:")
        for job in jobs:
            click.echo(f"  - Next run: {job['next_run']}")

        click.echo("\nScheduler is running in the background.")
        click.echo("Keep this CLI running to maintain scheduled tweets.")
        click.echo("Press Ctrl+C to stop the scheduler.\n")

        # Keep running until interrupted
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\nStopping scheduler...")
            scheduler.stop()
            click.echo("✓ Scheduler stopped")

    except RuntimeError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def auto_tweet_stats():
    """
    Show statistics about auto-tweeting activity.

    Displays number of tweets posted and angles used.
    """
    try:
        import sys
        from pathlib import Path

        # Add Auto-Tweet to path if not already there
        auto_tweet_path = str(Path(__file__).parent.parent.parent / "Auto-Tweet")
        if auto_tweet_path not in sys.path:
            sys.path.insert(0, auto_tweet_path)

        from auto_tweeter import AutoTweeter

        auto_tweeter = AutoTweeter()
        stats = auto_tweeter.get_stats()

        click.echo("Auto-Tweet Statistics:")
        click.echo(f"  Total tweets posted: {stats['total_tweets']}")
        click.echo(f"  Total angles used: {stats['total_angles']}")
        click.echo(f"  Recent tweets (last 10): {stats['recent_tweets']}")
        click.echo(f"  Recent angles (last 10): {stats['recent_angles']}")

        # Show recent tweets
        recent = auto_tweeter.logger.get_recent_tweets(5)
        if recent:
            click.echo("\nRecent tweets:")
            for tweet in recent:
                text = tweet.get("text", "")[:60] + "..."
                angle = tweet.get("angle", "N/A")
                timestamp = tweet.get("timestamp", "")[:10]
                click.echo(f"  [{timestamp}] {text}")
                click.echo(f"    Angle: {angle}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
