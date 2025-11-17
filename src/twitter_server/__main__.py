"""Run the Twitter OAuth2.0 server as a module"""

import sys
from .server import run_server

if __name__ == "__main__":
    # Parse command line arguments for host and port
    host = "127.0.0.1"
    port = 8000

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            host = sys.argv[1]
            if len(sys.argv) > 2:
                port = int(sys.argv[2])

    print(f"Starting Twitter OAuth2.0 Server on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Root endpoint: http://{host}:{port}/")
    print("Press Ctrl+C to stop the server\n")

    try:
        run_server(host=host, port=port)
    except KeyboardInterrupt:
        print("\nServer stopped.")
