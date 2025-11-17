# Twitter OAuth2.0 Server

HTTP server that accepts POST requests to post tweets using OAuth 2.0.

## Quick Start

**Install dependencies:**
```bash
uv pip install -e .
```

**Authenticate (one time):**
```bash
twitter-cli auth
```

**Start the server:**
```bash
python -m twitter_server
```

Server runs on `http://127.0.0.1:8000`

## Usage

**Post a tweet:**
```bash
curl -X POST http://127.0.0.1:8000/tweet \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the server!"}'
```

**Check server status:**
```bash
curl http://127.0.0.1:8000/status
```

**Interactive API docs:**
Visit `http://127.0.0.1:8000/docs` in your browser

## Endpoints

- `POST /tweet` - Post text-only tweet
- `POST /tweet-media` - Post tweet with media files
- `GET /status` - Server status and auth info
- `GET /health` - Health check
- `GET /docs` - Interactive Swagger UI

## How It Works

The server uses the same OAuth 2.0 credentials as the CLI tool (stored in `~/.twitter_cli/tokens.json`). Both tools share the same authentication, so you only need to run `twitter-cli auth` once.

## Custom Port

```bash
python -m twitter_server 9000
```

Or with uvicorn:
```bash
uvicorn twitter_server.server:app --host 127.0.0.1 --port 8000
```
