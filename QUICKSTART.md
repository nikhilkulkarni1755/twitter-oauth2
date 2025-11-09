# Quick Start Guide - Twitter CLI

Get up and running in 5 minutes.

## 1. Get Your Credentials (2 minutes)

1. Go to [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Click "Create App" → Select "Automated App or Bot"
3. Go to "Settings" tab → "Authentication Settings"
4. Turn on "OAuth 2.0"
5. Add Redirect URI: `http://localhost:8085/callback`
6. Copy your **Client ID** and **Client Secret**

## 2. Install the CLI (1 minute)

```bash
# Make sure you have Python 3.11+ and uv installed
cd twitter-cli
uv sync
uv pip install -e .
```

## 3. Authenticate (1 minute)

```bash
twitter-cli auth
```

- Paste your Client ID
- Paste your Client Secret
- Your browser will open for approval
- Click approve
- You're done! Tokens are saved

## 4. Post Your First Tweet (1 minute)

```bash
twitter-cli tweet "Hello world! This is my first tweet from the CLI"
```

That's it! You can now post tweets anytime.

## Common Commands

```bash
# Check if you're authenticated
twitter-cli status

# Post a tweet
twitter-cli tweet "Your message here"

# Logout
twitter-cli logout
```

## Troubleshooting

**Q: Port 8085 already in use?**
A: Close any other apps using that port or kill the process: `lsof -ti:8085 | xargs kill`

**Q: Browser didn't open?**
A: Copy the URL that appears in the terminal and paste it in your browser manually

**Q: Token expired error?**
A: The CLI auto-refreshes tokens. If it fails, just run `twitter-cli auth` again

**Q: Where are my credentials stored?**
A: In `~/.twitter_cli/` with secure permissions (0o600)

## Next Steps

- Check `examples.md` for advanced usage
- Integrate with scripts and automation
- See `README.md` for complete documentation

Happy tweeting! 🐦
