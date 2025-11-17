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

Server listens on `0.0.0.0:8000` - accessible from any machine on your network

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

## Network Access

**From other machines on the network:**

First, find your server machine's IP address:
```bash
# On the server machine
ipconfig getifaddr en0  # macOS
# or
hostname -I            # Linux
```

Then from any other machine:
```bash
curl -X POST http://<SERVER_IP>:8000/tweet \
  -H "Content-Type: application/json" \
  -d '{"text": "Posted from another machine!"}'
```

Example (if server IP is 192.168.1.50):
```bash
curl -X POST http://192.168.1.50:8000/tweet \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from my RAG system!"}'
```

## Restrict to Localhost Only

To disable network access and only allow connections from the same machine:
```bash
python -m twitter_server --localhost
```

## Custom Port

```bash
# Network accessible (default)
python -m twitter_server 9000

# Localhost only with custom port
python -m twitter_server --localhost 9000
```

Or with uvicorn:
```bash
# Network accessible
uvicorn twitter_server.server:app --host 0.0.0.0 --port 8000

# Localhost only
uvicorn twitter_server.server:app --host 127.0.0.1 --port 8000
```
