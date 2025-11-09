# Twitter CLI - Usage Examples

This document provides practical examples of how to use the Twitter CLI.

## Example 1: Initial Setup and Authentication

```bash
# First time setup
twitter-cli auth

# You will see:
# Enter your Client ID: [paste your Client ID from developer.x.com]
# Enter your Client Secret: [paste your Client Secret]
# Saving credentials...
# Generating PKCE challenge...
#
# Opening browser for authentication...
# If browser doesn't open, visit: https://x.com/i/oauth2/authorize?...
#
# Waiting for authorization callback...
# Exchanging authorization code for tokens...
# Retrieving user information...
#
# ✓ Successfully authenticated as @yourhandle
# Access token expires at: 2025-11-15 20:33:45
```

## Example 2: Post a Simple Tweet

```bash
twitter-cli tweet "Hello from my Twitter CLI! This is automated."

# Output:
# Posting tweet...
# ✓ Tweet posted: https://x.com/yourhandle/status/1234567890
```

## Example 3: Post a Tweet with Dynamic Content

```bash
# Using command substitution
twitter-cli tweet "Current time: $(date)"

# Or with variables
message="Automated tweet posted at $(date '+%Y-%m-%d %H:%M:%S')"
twitter-cli tweet "$message"
```

## Example 4: Check Authentication Status

```bash
twitter-cli status

# Output:
# ✓ Authenticated as @yourhandle
# Access token expires: 2025-11-15 20:33:45
# Refresh token: valid
# Scopes: tweet.read tweet.write users.read offline.access
```

## Example 5: Logout

```bash
twitter-cli logout

# Output:
# Are you sure you want to logout? [y/N]: y
# ✓ Logged out successfully
# Run 'twitter-cli auth' to authenticate again
```

## Example 6: Use in a Bash Script

```bash
#!/bin/bash

# Monitor system and tweet status updates
check_system() {
    load=$(uptime | awk -F'load average:' '{print $2}')
    memory=$(free -h | grep Mem | awk '{print $3 "/" $2}')

    message="System Status Update
CPU Load: $load
Memory: $memory"

    twitter-cli tweet "$message"
}

# Run every hour
while true; do
    check_system
    sleep 3600
done
```

## Example 7: Use in a Python Script

```python
import subprocess
import json
from datetime import datetime

def post_tweet(text):
    """Post a tweet using the CLI"""
    result = subprocess.run(
        ["twitter-cli", "tweet", text],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return {"success": True, "output": result.stdout}
    else:
        return {"success": False, "error": result.stderr}

# Example usage
status = post_tweet("Automated tweet from Python!")
if status["success"]:
    print("Tweet posted successfully!")
    print(status["output"])
else:
    print("Error:", status["error"])
```

## Example 8: Tweet Collection Data

```bash
#!/bin/bash

# Collect some data
data=$(curl -s https://api.example.com/stats)
count=$(echo "$data" | jq '.count')
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Post update
twitter-cli tweet "Data collection complete! Processed $count items at $timestamp"
```

## Example 9: Conditional Tweet

```bash
#!/bin/bash

# Only tweet if condition is met
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

if (( $(echo "$cpu_usage > 80" | bc -l) )); then
    twitter-cli tweet "⚠️ High CPU usage detected: ${cpu_usage}%"
fi
```

## Example 10: Daily Status Report

```bash
#!/bin/bash
# Save as daily_report.sh

# Get various metrics
uptime_hours=$(uptime -p | sed 's/up //' | sed 's/, .*//')
timestamp=$(date '+%A, %B %d, %Y at %I:%M %p')

# Create message
message="Daily Status Report - $timestamp
System uptime: $uptime_hours
All systems operational"

# Post tweet
twitter-cli tweet "$message"
```

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Tweet on Deploy
on:
  push:
    branches: [main]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install twitter-cli
        run: uv pip install --user twitter-cli

      - name: Post deployment tweet
        env:
          TWITTER_CLIENT_ID: ${{ secrets.TWITTER_CLIENT_ID }}
          TWITTER_CLIENT_SECRET: ${{ secrets.TWITTER_CLIENT_SECRET }}
        run: |
          # Note: Tokens must be pre-configured locally
          twitter-cli tweet "New deployment to production! Commit: ${{ github.sha }}"
```

### Cron Job (System Scheduler)

```bash
# Add to crontab: crontab -e

# Tweet every 6 hours
0 */6 * * * /usr/local/bin/twitter-cli tweet "Scheduled status update at $(date)"

# Tweet daily at 9 AM
0 9 * * * /usr/local/bin/twitter-cli tweet "Good morning! Today's updates are live."
```

### Systemd Service

```ini
# /etc/systemd/system/twitter-monitor.service

[Unit]
Description=Twitter CLI Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/twitter-cli
ExecStart=/home/your_username/.local/bin/twitter-cli tweet "Service started"
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

## Error Handling in Scripts

```bash
#!/bin/bash
set -e

# Function to post tweet with error handling
tweet_with_retry() {
    local message="$1"
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if twitter-cli tweet "$message"; then
            echo "Tweet posted successfully"
            return 0
        else
            echo "Attempt $attempt failed. Retrying..."
            sleep $((attempt * 5))
            ((attempt++))
        fi
    done

    echo "Failed to post tweet after $max_attempts attempts" >&2
    return 1
}

# Usage
tweet_with_retry "Test message with retry logic"
```

## Notes

- All examples assume the CLI is properly installed and authenticated
- For scripting, ensure tokens don't expire during long-running processes
- Token refresh happens automatically but requires refresh_token scope
- Never commit your Client ID or Client Secret to version control
- Use environment variables or secret management for production deployments
