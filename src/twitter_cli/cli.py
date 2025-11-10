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


if __name__ == "__main__":
    cli()
