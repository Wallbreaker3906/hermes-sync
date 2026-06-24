# QQ Bot Multi-Instance Setup (Profile Method)

## Why profiles?

The Hermes gateway's platform system uses a `Platform` enum — one adapter instance per platform type. You cannot add multiple `qqbot` entries to a single `config.yaml`. To run multiple QQ Bots simultaneously, each needs its own Hermes profile with its own gateway process.

This also means each bot has **independent** memory, skills, and session context. They act like separate agents.

## Step-by-step: Adding a second QQ Bot

### Prerequisites

- Existing QQ Bot already running (env-vars method: `QQ_APP_ID` + `QQ_CLIENT_SECRET` in `~/.hermes/.env`)
- Second QQ Bot App ID + Client Secret from https://q.qq.com

### 1. Create the profile

```bash
hermes profile create qqbot2 --clone
```

This clones the default profile (config, .env, skills, SOUL.md) to `~/.hermes/profiles/qqbot2/`.

### 2. Update credentials

The cloned `.env` has the first bot's credentials. Replace them:

```bash
cd ~/.hermes/profiles/qqbot2

# Replace App ID
sed -i '' 's/^QQ_APP_ID=.*/QQ_APP_ID=<NEW_APP_ID>/' .env

# Replace Client Secret
sed -i '' 's/^QQ_CLIENT_SECRET=.*/QQ_CLIENT_SECRET=<NEW_SECRET>/' .env

# Optionally allow all users
sed -i '' 's/^QQ_ALLOW_ALL_USERS=.*/QQ_ALLOW_ALL_USERS=true/' .env

# Clear allowed users list (or set specific users)
sed -i '' 's/^QQ_ALLOWED_USERS=.*/QQ_ALLOWED_USERS=/' .env

# Verify
grep "QQ_" .env
```

### 3. Create launchd plist for second gateway

Create `~/Library/LaunchAgents/ai.hermes.gateway-qqbot2.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.gateway-qqbot2</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/$USER/.hermes/hermes-agent/venv/bin/python</string>
        <string>-m</string>
        <string>hermes_cli.main</string>
        <string>gateway</string>
        <string>run</string>
        <string>--replace</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/$USER/.hermes/hermes-agent</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>...same as default plist...</string>
        <key>VIRTUAL_ENV</key>
        <string>/Users/$USER/.hermes/hermes-agent/venv</string>
        <key>HERMES_HOME</key>
        <string>/Users/$USER/.hermes/profiles/qqbot2</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>ThrottleInterval</key>
    <integer>30</integer>

    <key>StandardOutPath</key>
    <string>/Users/$USER/.hermes/profiles/qqbot2/logs/gateway.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/$USER/.hermes/profiles/qqbot2/logs/gateway.error.log</string>
</dict>
</plist>
```

**Key difference from default plist:** `HERMES_HOME` points to the profile directory. This is what isolates the second bot's credentials, config, and state.

### 4. Create health check for second gateway

The health check template from `templates/gateway-healthcheck.sh` works for profiles too — just point `LOG_FILE` at the profile's log:

```bash
LOG_FILE="$HOME/.hermes/profiles/qqbot2/logs/gateway.log"
```

And restart with the profile-specific plist label:

```bash
launchctl stop ai.hermes.gateway-qqbot2
launchctl start ai.hermes.gateway-qqbot2
```

Create a companion launchd plist at `~/Library/LaunchAgents/ai.hermes.qq-healthcheck-2.plist` with `StartInterval: 600`.

### 5. Load and start

```bash
# Load second gateway plist
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway-qqbot2.plist

# Load second health check plist
launchctl load ~/Library/LaunchAgents/ai.hermes.qq-healthcheck-2.plist
```

### 6. Verify

```bash
# Both gateways should be running
launchctl list | grep hermes.gateway
# Should show:
# <pid>  0  ai.hermes.gateway
# <pid>  0  ai.hermes.gateway-qqbot2

# Check both QQ Bot connections
grep "qqbot" ~/.hermes/logs/gateway.log | tail -3
grep "qqbot" ~/.hermes/profiles/qqbot2/logs/gateway.log | tail -3
```

## Important notes

- **QQ Open IDs are app-specific.** Each QQ Bot application issues a different Open ID for the same QQ user. When configuring `QQ_ALLOWED_USERS` for a new bot, do NOT copy the Open ID from the first bot — have the user send a test message to the new bot, then extract their Open ID from the profile's gateway log: `grep "user=" ~/.hermes/profiles/qqbot2/logs/gateway.log | tail -3`.
- Each profile's gateway is a **separate process** — they have independent memory, skills, and cron jobs. If you want skills shared between bots, copy them to the profile's skills dir.
- Model provider settings are cloned from default. If you want different models per bot, edit `~/.hermes/profiles/qqbot2/config.yaml`.
- Health checks are per-gateway. Don't share a single health check script — each needs to restart its own gateway.
- The profile CLI wrapper is at `~/.local/bin/qqbot2`. Use it to:
  - `qqbot2 gateway status` — check this bot's gateway
  - `qqbot2 config edit` — edit this bot's config
  - `qqbot2 skills list` — view this bot's skills
