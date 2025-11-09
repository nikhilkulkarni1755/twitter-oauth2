"""OAuth 2.0 PKCE flow implementation for Twitter/X"""

import hashlib
import secrets
import base64
import urllib.parse
import webbrowser
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Tuple
import requests


def generate_pkce_pair() -> Tuple[str, str]:
    """
    Generate code_verifier and code_challenge for PKCE.

    - code_verifier: 43-128 random URL-safe chars
    - code_challenge: base64url(sha256(code_verifier))
    - code_challenge_method: S256

    Returns: (code_verifier, code_challenge)
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
    code_verifier = code_verifier.rstrip("=")  # Remove padding

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8")
    code_challenge = code_challenge.rstrip("=")  # Remove padding

    return code_verifier, code_challenge


def generate_state() -> str:
    """Generate random state for CSRF protection"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")


def build_auth_url(
    client_id: str, redirect_uri: str, code_challenge: str, state: str
) -> str:
    """
    Build OAuth 2.0 authorization URL.

    Base: https://x.com/i/oauth2/authorize
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    return f"https://x.com/i/oauth2/authorize?{urllib.parse.urlencode(params)}"


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback"""

    authorization_code = None
    error_message = None

    def do_GET(self):
        """Handle GET request to /callback"""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        query_params = urllib.parse.parse_qs(parsed_path.query)

        # Check for errors from X
        if "error" in query_params:
            error = query_params["error"][0]
            error_desc = query_params.get("error_description", ["Unknown error"])[0]
            CallbackHandler.error_message = f"{error}: {error_desc}"

            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Authorization Failed</h1>
            <p><strong>{error}</strong></p>
            <p>{error_desc}</p>
            <p>You can close this window and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return

        # Get authorization code
        if "code" not in query_params:
            CallbackHandler.error_message = "No authorization code received"

            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Error</h1><p>No authorization code received</p></body></html>"
            )
            return

        code = query_params["code"][0]
        state = query_params.get("state", [None])[0]

        # Verify state (CSRF protection)
        if state != getattr(self.server, "expected_state", None):
            CallbackHandler.error_message = "State mismatch - CSRF attack detected"

            self.send_response(403)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Error</h1><p>State mismatch - authentication failed</p></body></html>"
            )
            return

        CallbackHandler.authorization_code = code

        # Send success response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>Success!</h1>
        <p>You have successfully authenticated with Twitter.</p>
        <p>You can close this window and return to your terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_callback_server(expected_state: str) -> str:
    """
    Start HTTP server on localhost:8085 to capture OAuth callback.

    Returns: authorization_code (string) or raises exception
    """
    server_address = ("localhost", 8085)
    server = HTTPServer(server_address, CallbackHandler)
    server.expected_state = expected_state

    # Run server in background thread
    server_thread = Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Wait for callback (with timeout)
    server_thread.join(timeout=300)  # 5 minute timeout

    if CallbackHandler.error_message:
        raise RuntimeError(f"OAuth error: {CallbackHandler.error_message}")

    if CallbackHandler.authorization_code is None:
        raise RuntimeError("Authorization callback timeout or failed")

    return CallbackHandler.authorization_code


def exchange_code_for_tokens(
    code: str,
    code_verifier: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """
    Exchange authorization code for access/refresh tokens.

    POST https://api.x.com/2/oauth2/token
    """
    auth = (client_id, client_secret)

    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    try:
        response = requests.post(
            "https://api.x.com/2/oauth2/token",
            auth=auth,
            data=data,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to exchange code for tokens: {e}")

    try:
        return response.json()
    except ValueError as e:
        raise RuntimeError(f"Invalid token response: {e}")


def get_user_info(access_token: str) -> dict:
    """Get authenticated user info from X API"""
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(
            "https://api.x.com/2/users/me",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get user info: {e}")

    try:
        data = response.json()
        return data.get("data", {})
    except ValueError as e:
        raise RuntimeError(f"Invalid user response: {e}")
