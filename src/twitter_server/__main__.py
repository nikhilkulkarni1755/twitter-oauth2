"""Run the Twitter OAuth2.0 server as a module"""

import sys
from .server import run_server

if __name__ == "__main__":
    # Default: bind to 0.0.0.0 so it's accessible from any machine on the network
    host = "0.0.0.0"
    port = 8000

    # Parse command line arguments
    args = sys.argv[1:]

    # Check for --localhost flag to restrict to localhost only
    if "--localhost" in args:
        host = "127.0.0.1"
        args.remove("--localhost")

    # Parse remaining arguments as [host] [port]
    if len(args) > 0:
        try:
            port = int(args[0])
        except ValueError:
            host = args[0]
            if len(args) > 1:
                port = int(args[1])

    print(f"Starting Twitter OAuth2.0 Server on {host}:{port}")
    if host == "0.0.0.0":
        print(f"  Accessible from other machines on the network")
    else:
        print(f"  Localhost only (restricted to this machine)")
    print(f"\nAPI Documentation: http://127.0.0.1:{port}/docs (if on this machine)")
    print(f"Root endpoint: http://127.0.0.1:{port}/ (if on this machine)")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        run_server(host=host, port=port)
    except KeyboardInterrupt:
        print("\nServer stopped.")
