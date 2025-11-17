# Twitter CLI - OAuth 2.0 PKCE with Media Support

Post tweets from your terminal using Twitter's OAuth 2.0 Authorization Code Flow with PKCE, plus optional media support (images/videos) via OAuth 1.0a.

## Features

- **Browser-based authentication** - One-time OAuth 2.0 PKCE flow with browser authorization
- **Text tweets** - Post text-only tweets via OAuth 2.0
- **Media tweets** - Post tweets with images and videos via OAuth 1.0a (requires elevated access)
- **Automatic token refresh** - Access tokens are automatically refreshed when expired
- **Secure storage** - Credentials stored with restricted file permissions (0o600)
- **Simple CLI** - Easy-to-use command-line interface with Click
- **HTTP Server** - Background OAuth 2.0 server for posting tweets via HTTP requests
- **Agent-friendly** - Can be called from scripts and automation tools
- **Interactive API docs** - Swagger UI for testing endpoints

## Prerequisites

1. **X Developer Account**
   - Go to [developer.x.com](https://developer.x.com)
   - Create a new application
   - Select "Automated App or Bot" as the application type (confidential client)

2. **Python 3.11+**
   - Install from [python.org](https://www.python.org)

3. **uv Package Manager**
   - Install from [astral.sh/uv](https://astral.sh/uv)

## Installation

### Basic Installation (Text-only tweets)

```bash
# Clone or download this project
cd twitter-cli

# Install dependencies
uv sync

# Install the CLI tool in editable mode
uv pip install -e .
```

### With Media Support (Images/Videos)

```bash
# Install with media support (includes tweepy)
uv pip install -e ".[media]"
```

## Setup - Get Your Credentials

1. **Go to [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)**

2. **Create a new app** (if you don't have one)
   - Click "Create App"
   - Choose "Automated App or Bot" type
   - Fill in app details

3. **Configure OAuth 2.0**
   - Go to your app's "Settings" tab
   - Scroll to "Authentication Settings"
   - Turn on "OAuth 2.0"
   - Under "Redirect URIs", add: `http://localhost:8085/callback`
   - Under "App permissions", select "Read and write"
   - Copy **Client ID** and **Client Secret** (you'll need these)

4. **Note the required scopes:**
   - `tweet.read` - Read tweets
   - `tweet.write` - Write tweets
   - `users.read` - Read user information
   - `offline.access` - Access tokens refresh token

## Usage

### Twitter OAuth2.0 Server

Run a background HTTP server that accepts POST requests to post tweets. Perfect for:
- RAG systems generating tweets
- Multiple local services posting to a central OAuth endpoint
- Scheduled tweet posting via HTTP requests

**Start the server:**

```bash
python -m twitter_server
```

Server runs on `http://127.0.0.1:8000` by default. To use a different port:

```bash
python -m twitter_server 9000
```

Or to specify host and port:

```bash
python -m twitter_server 192.168.1.100 8000
```

**API endpoints:**

```bash
# Health check
curl http://127.0.0.1:8000/health

# Get server status and auth info
curl http://127.0.0.1:8000/status

# Post a text tweet (requires authentication)
curl -X POST http://127.0.0.1:8000/tweet \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the server!"}'

# Post a tweet with media
curl -X POST http://127.0.0.1:8000/tweet-media \
  -H "Content-Type: application/json" \
  -d '{"text": "Check this out!", "media_paths": ["/path/to/image.jpg"]}'

# API docs (interactive Swagger UI)
open http://127.0.0.1:8000/docs
```

**Usage in Python:**

```python
import requests

# Post a tweet
response = requests.post(
    "http://127.0.0.1:8000/tweet",
    json={"text": "Hello from Python!"}
)

if response.status_code == 200:
    print(f"Tweet posted: {response.json()['tweet_id']}")
else:
    print(f"Error: {response.text}")
```

**Important:** The server uses the same OAuth 2.0 credentials as the CLI tool. You must authenticate first:

```bash
twitter-cli auth
```

Then the server can use those stored credentials automatically.

**Testing the server:**

Use the provided test client script:

```bash
python examples/test_server_client.py
```

### First Time: Authenticate

```bash
twitter-cli auth
```

When you run this command:
1. You'll be prompted for your **Client ID** and **Client Secret**
2. Your default browser will open for authentication
3. Approve the permissions (you'll only see this once)
4. You'll be redirected back to the CLI
5. Your tokens are saved securely in `~/.twitter_cli/`

Example:
```bash
$ twitter-cli auth
Enter your Client ID: [paste your Client ID]
Enter your Client Secret: [paste your Client Secret]
Saving credentials...
Generating PKCE challenge...

Opening browser for authentication...
If browser doesn't open, visit: https://x.com/i/oauth2/authorize?...

Waiting for authorization callback...
Exchanging authorization code for tokens...
Retrieving user information...

 Successfully authenticated as @yourhandle
Access token expires at: 2025-11-15 20:33:45
```

### Post a Tweet

```bash
twitter-cli tweet "Your tweet text here"
```

Example:
```bash
$ twitter-cli tweet "Hello from my Twitter CLI!"
Posting tweet...
 Tweet posted: https://x.com/yourhandle/status/1234567890
```

### Post Tweets with Media (Images/Videos)

**Setup (one-time):** Configure OAuth 1.0a credentials for media posting:

```bash
twitter-cli auth-media
```

You'll be prompted for OAuth 1.0a credentials from [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard):
- Consumer Key (API Key)
- Consumer Secret (API Key Secret)
- Access Token
- Access Token Secret

**Post tweets with media:**

```bash
# Single image
twitter-cli tweet-media "Check this out!" /pictures/photo.jpg

# Multiple images
twitter-cli tweet-media "Great photos!" /pictures/photo1.jpg /pictures/photo2.png

# Video
twitter-cli tweet-media "Watch this!" /videos/clip.mp4

# Mixed media
twitter-cli tweet-media "My collection" /pictures/photo.jpg /videos/video.mp4
```

**Supported formats:**
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` (max 15MB)
- Videos: `.mp4`, `.mov` (max 512MB)

**Requirements:** Media posting needs **elevated API access**. Request it at [developer.x.com/en/portal/product](https://developer.x.com/en/portal/product).

### Check Authentication Status

```bash
twitter-cli status
```

Example output:
```bash
$ twitter-cli status
 Authenticated as @yourhandle
Access token expires: 2025-11-15 20:33:45
Refresh token: valid
Scopes: tweet.read tweet.write users.read offline.access
```

### Logout (Text Tweets)

```bash
twitter-cli logout
```

This will:
- Delete stored tokens from `~/.twitter_cli/tokens.json`
- Keep your client credentials (so you can auth again without re-entering them)
- Require you to authenticate again to post tweets

### Clear Media Credentials

```bash
twitter-cli logout-media
```

This will:
- Delete stored OAuth 1.0a credentials from `~/.twitter_cli/media_credentials.json`
- Require you to run `twitter-cli auth-media` again to post media

## Auto-Tweet: Automated Kubernetes Tweet Generation

Generate and post creative tweets about Kubernetes automatically using a local Qwen LLM!

### Quick Start

```bash
# Generate and post a single tweet (asks for confirmation)
uv run twitter-cli auto-tweet-once

# Generate and post 5 tweets automatically
uv run twitter-cli auto-tweet-batch --count 5

# Schedule tweets at specific times (9 AM, 12 PM, 3 PM, 6 PM)
uv run twitter-cli auto-tweet-schedule --hours "9,12,15,18"

# View tweet activity and statistics
uv run twitter-cli auto-tweet-stats
```

### How It Works

1. **Fetches random Kubernetes documentation** from official docs
2. **Generates novel angles** using local Qwen LLM (via LMStudio)
3. **Prevents duplicates** by tracking last 10 tweets and angles
4. **Converts to tweets** ensuring 280 character limit
5. **Posts to Twitter/X** with your existing OAuth credentials

### Requirements

- **LMStudio** running with Qwen model at `http://192.168.1.98:1234/v1`
- **Already authenticated** with `twitter-cli auth`

### Documentation

- **[QUICKSTART_AUTO_TWEET.md](QUICKSTART_AUTO_TWEET.md)** - Get started in 5 minutes
- **[AUTO_TWEET.md](AUTO_TWEET.md)** - Full feature documentation
- **[AUTO_TWEET_CONFIG.md](AUTO_TWEET_CONFIG.md)** - Configuration and customization
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details and architecture

### Features

✅ Local LLM (no API costs, fully private)
✅ Novel angle generation (prevents repetition)
✅ Hourly scheduling support
✅ Tweet logging and analytics
✅ Kubernetes doc integration
✅ Single/batch/scheduled posting modes
✅ Fully customizable (prompts, sources, timing)

## Usage in Scripts

Since the CLI works with saved tokens, you can easily integrate it into scripts and automation:

```bash
#!/bin/bash

# Get some data
message=$(python generate_tweet.py)

# Post it to Twitter
twitter-cli tweet "$message"
```

Or in Python:

```python
import subprocess
import sys

tweet_text = "Hello from Python!"
result = subprocess.run(
    ["twitter-cli", "tweet", tweet_text],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Tweet posted!")
else:
    print(f"Error: {result.stderr}")
    sys.exit(1)
```

## File Locations

Your authentication data is stored securely in your home directory:

### OAuth 2.0 (Text Tweets)

- **`~/.twitter_cli/config.json`** - Your OAuth 2.0 Client ID and Client Secret
  - Permissions: 0o600 (owner read/write only)

- **`~/.twitter_cli/tokens.json`** - Your OAuth 2.0 access and refresh tokens
  - Permissions: 0o600 (owner read/write only)
  - Automatically updated when tokens are refreshed

### OAuth 1.0a (Media Posting)

- **`~/.twitter_cli/media_credentials.json`** - Your OAuth 1.0a credentials (optional)
  - Permissions: 0o600 (owner read/write only)
  - Only created if you use `twitter-cli auth-media` command
  - Contains: Consumer Key, Consumer Secret, Access Token, Access Token Secret

## OAuth 2.0 Flow

This CLI implements the OAuth 2.0 Authorization Code Flow with PKCE (Proof Key for Code Exchange):

1. **Local Server** - Starts an HTTP server on localhost:8085 to receive the callback
2. **Browser Authentication** - Opens your browser to Twitter's OAuth authorization page
3. **User Consent** - You approve the requested permissions
4. **Authorization Code** - Twitter redirects back to localhost with an authorization code
5. **Code Exchange** - The CLI exchanges the code for an access token (using PKCE)
6. **Token Storage** - Access and refresh tokens are saved securely
7. **Token Refresh** - When access tokens expire, the refresh token is used to get new ones

## Troubleshooting

### "Not authenticated. Run 'twitter-cli auth' first."

This means you haven't authenticated yet. Run:
```bash
twitter-cli auth
```

### "Port 8085 already in use"

Another process is using port 8085. Either:
- Kill the process using that port
- Wait a few seconds and try again
- Modify the code to use a different port

### "Authorization callback timeout"

The browser authentication took too long. Try running `twitter-cli auth` again.

### "Invalid refresh token"

Your refresh token has expired. Re-authenticate:
```bash
twitter-cli logout
twitter-cli auth
```

### "API Error: 403 Forbidden"

Your app may not have write permissions. Check your app settings at [developer.x.com](https://developer.x.com) and make sure:
- Permissions are set to "Read and write"
- Scopes include `tweet.write`

### "API Error: 429 Rate Limited"

You've exceeded Twitter's rate limits. Wait a few minutes before posting again.

## Security Notes

1. **File Permissions** - Your tokens are stored with 0o600 permissions (readable/writable by owner only)
2. **HTTPS Only** - All API calls use HTTPS
3. **State Verification** - CSRF protection via state parameter in OAuth flow
4. **No Logging** - Tokens and secrets are never logged
5. **Keep Secrets Safe** - Never share your Client ID or Client Secret

## Limitations

- **Rate Limits** - Twitter API has rate limits:
  - ~300 tweets per 3 hours per user
  - Tweet lookup: 900 requests per 15 minutes

- **Media Access** - Media posting requires elevated API access from Twitter
  - Must request elevation at [developer.x.com/en/portal/product](https://developer.x.com/en/portal/product)
  - Dual authentication: OAuth 2.0 for text tweets, OAuth 1.0a for media

- **Platform** - Requires local HTTP server on port 8085 for OAuth 2.0 callback

## Future Enhancements

Possible additions:
- Thread/conversation support
- Delete tweets
- Reply to tweets
- Like/retweet functionality
- Direct message support
- Configurable refresh token handling
- Custom port configuration for OAuth callback
- Batch tweet posting

## Contributing

Found a bug? Have a feature request? Feel free to open an issue or submit a pull request.

## License

This project is open source and available under the MIT License.

## Support

For issues with:
- **Twitter API** - See [docs.x.com](https://docs.x.com)
- **This CLI** - Check the troubleshooting section above
- **OAuth 2.0** - See [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- **PKCE** - See [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
