"""FastAPI server for posting tweets via HTTP requests"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add parent directory to path to import twitter_cli modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from twitter_cli import token_manager, api, media_manager


app = FastAPI(
    title="Twitter OAuth2.0 Server",
    description="HTTP server for posting tweets using OAuth 2.0",
    version="0.1.0",
)


class TweetRequest(BaseModel):
    """Request model for posting a text tweet"""
    text: str


class TweetWithMediaRequest(BaseModel):
    """Request model for posting a tweet with media"""
    text: str
    media_paths: List[str]


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/status")
def status():
    """Get server status and authentication info"""
    if not token_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    tokens = token_manager.load_tokens()
    config = token_manager.load_config()

    if not tokens or not config:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        access_token = token_manager.get_valid_access_token()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token error: {str(e)}")

    try:
        from twitter_cli import oauth
        user_info = oauth.get_user_info(access_token)
        username = user_info.get("username", "unknown")
    except Exception as e:
        username = "unknown"

    expiration = token_manager.get_token_expiration_time()

    return {
        "authenticated": True,
        "username": username,
        "token_expires_at": expiration.isoformat() if expiration else None,
        "scopes": tokens.get("scope", "").split() if tokens.get("scope") else [],
    }


@app.post("/tweet")
def post_tweet(request: TweetRequest):
    """Post a text-only tweet"""
    if not token_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated. Run 'twitter-cli auth' first.")

    try:
        access_token = token_manager.get_valid_access_token()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

    try:
        result = api.post_tweet(request.text, access_token)
        return {
            "success": True,
            "tweet_id": result.get("id"),
            "text": request.text,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to post tweet: {str(e)}")


@app.post("/tweet-media")
def post_tweet_with_media(request: TweetWithMediaRequest):
    """Post a tweet with media (images or videos)"""
    if not token_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated. Run 'twitter-cli auth' first.")

    # Check if media credentials are available
    if not media_manager.has_media_credentials():
        raise HTTPException(
            status_code=400,
            detail="Media credentials not configured. Run 'twitter-cli auth-media' first."
        )

    try:
        # Validate media paths exist
        for path in request.media_paths:
            if not os.path.exists(path):
                raise HTTPException(status_code=400, detail=f"Media file not found: {path}")

        # Use OAuth 1.0a media posting (via tweepy)
        result = media_manager.post_tweet_with_media(request.text, request.media_paths)

        return {
            "success": True,
            "tweet_id": result.get("id"),
            "text": request.text,
            "media_count": len(request.media_paths),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to post tweet with media: {str(e)}")


@app.get("/")
def root():
    """Root endpoint with API documentation"""
    return {
        "name": "Twitter OAuth2.0 Server",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "GET /health": "Health check",
            "GET /status": "Get authentication status and user info",
            "POST /tweet": "Post a text-only tweet",
            "POST /tweet-media": "Post a tweet with media",
        }
    }


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
