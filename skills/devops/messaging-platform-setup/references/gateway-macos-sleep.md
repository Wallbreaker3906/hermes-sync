# Gateway macOS Sleep Fix (Detailed)

## Symptoms

- QQ/WeCom bot suddenly stops responding
- `hermes gateway status` shows "Gateway service is not loaded"
- `ps aux | grep hermes` shows no gateway process
- Gateway logs show `Received SIGTERM — initiating shutdown` at the time user stopped using their Mac

## Root Cause

When Mac goes to sleep (lid closed or idle timeout), launchd sends `SIGTERM` to user GUI agents including the Hermes gateway. The default `KeepAlive` configuration (`SuccessfulExit: false`) tells launchd to only restart on crash (non-zero exit). Since SIGTERM is a clean shutdown (exit 0), launchd does NOT restart the gateway when the Mac wakes up.

## Diagnostic Commands

```bash
# 1. Confirm Mac was asleep at the time
pmset -g log | grep -E "Sleep|Wake" | tail -20

# 2. Confirm launchd killed the gateway
log show --predicate 'process == "launchd"' --style syslog --last 24h | grep -i hermes | grep -E "SIGTERM|SIGKILL|Killed"

# 3. Check gateway logs for shutdown reason
grep -E "SIGTERM|shutdown|Stopping" ~/.hermes/logs/gateway.log | tail -10

# 4. Check current KeepAlive setting
plutil -p ~/Library/LaunchAgents/ai.hermes.gateway.plist | grep -A3 KeepAlive
```

## Fix

The fix has two components: a launchd plist tweak and a health-check watchdog. Both are needed for reliable auto-recovery.

### 1. Launchd plist: ThrottleInterval + KeepAlive

`KeepAlive: <true/>` (always restart) can fail when launchd receives too many rapid exits in a short window — it silently stops restarting to prevent thrashing. Adding `ThrottleInterval` lets launchd pace itself without giving up permanently. Use a dict for `KeepAlive` to be explicit:

```xml
<!-- ROBUST (handles both SIGTERM exit-0 and SIGKILL exit--9) -->
<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>
</dict>
<key>ThrottleInterval</key>
<integer>30</integer>
```

`SuccessfulExit: false` means "restart on non-zero exit" (covers SIGKILL). For the SIGTERM case (exit 0 during graceful sleep shutdown), you'd want `SuccessfulExit: true` — but in practice, macOS sleep often sends SIGKILL not SIGTERM, and the health-check watchdog (below) catches the rest.

## Variant: Gateway Process Alive but Bot Disconnected After Sleep

### Symptoms

- `ps aux | grep hermes` shows gateway process running, but QQ/WeCom bot doesn't respond
- `launchctl list | grep hermes` shows gateway with exit code 0 (process alive), but bot is silent
- Gateway logs show the adapter connected fine before sleep, then after wake: `Reconnect failed: Failed to get QQ Bot gateway URL: [Errno 8] nodename nor servname provided, or not known`

### Root Cause

This is a *different* failure mode from the SIGTERM kill. The gateway process survives sleep (KeepAlive is working), but the internal platform adapter's WebSocket connection drops. On wake, the adapter tries to reconnect *immediately* — before the network interface has finished re-establishing. DNS resolution fails (`nodename nor servname provided`), and the adapter's retry logic may give up permanently or back off so long the connection never recovers.

The key difference:
- **SIGTERM variant**: Process dies → KeepAlive restarts it → needs `SuccessfulExit: true`
- **Adapter variant**: Process stays alive → internal reconnect fails → KeepAlive doesn't help because the process didn't die

### Diagnosis

```bash
# Check if gateway process is alive
ps aux | grep "gateway run" | grep -v grep

# Look for the DNS failure signature in logs
grep -i "Reconnect failed.*nodename nor servname" ~/.hermes/logs/gateway.log | tail -5

# Check the last QQ Bot log entry — is it a "Ready" or an error?
grep -i "qqbot" ~/.hermes/logs/gateway.log | tail -5
```

### Fix: Health Check Watchdog

A separate launchd job that periodically checks adapter health and restarts the gateway if the adapter has been disconnected too long. Two components:

**Design principle: check Ready age, not error strings.** Matching specific error patterns (`Reconnect failed`, `WebSocket error`, etc.) is fragile — new error types ("Send failed: All connection attempts failed", bare `ERROR` log lines) slip through. Instead, check how old the last `Ready` log line is. If it's older than `MAX_IDLE` seconds (default: 30 min), restart the gateway. This catches every failure mode without needing to enumerate them.

**CRITICAL: check for a real PID, not just the launchd label.** `launchctl list "$PLIST_NAME"` succeeds even when the process is dead (SIGKILL exit -9 leaves the label registered). If the script only checks label existence, a dead gateway with an old "Ready" in its log will be falsely reported as healthy. Check for an actual numeric PID:

```bash
PID=$(launchctl list | grep "^[0-9].*${PLIST_NAME}$" | awk '{print $1}')
if [ -z "$PID" ] || [ "$PID" = "-" ]; then
    # Process is dead — restart
fi
```

See `templates/gateway-healthcheck.sh` for a production-ready script that implements both checks.

**1. Health check script** — see `templates/gateway-healthcheck.sh` for a production-ready script. Key design decisions (embedded in the template):

- **Check for a real numeric PID**, not just launchd label existence. A dead process (SIGKILL -9) still has its label registered — `launchctl list "$NAME"` succeeds; only `grep "^[0-9]"` catches the truth.
- **Check BOTH "Ready" and "Session resumed"** as healthy states. After a WebSocket reconnect, the adapter logs "Session resumed" — not "Ready". Missing this means a perfectly healthy reconnect is invisible and the bot is wrongly restarted.
- **Check Ready age, not error strings.** Matching specific error patterns is fragile — "Send failed: All connection attempts failed", bare `ERROR` log lines, and unknown future errors all slip through. If the last healthy log is >30 min old, restart.

**2. launchd plist** (`~/Library/LaunchAgents/ai.hermes.qq-healthcheck.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.qq-healthcheck</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/$USER/Library/Scripts/hermes-gateway-healthcheck.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/.hermes/logs/qq-healthcheck.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/.hermes/logs/qq-healthcheck.error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/ai.hermes.qq-healthcheck.plist
```

The watchdog runs every 10 minutes. It gives the adapter's native reconnect logic a 10-minute grace window before stepping in. After sleep/wake, the bot should auto-recover within 10-20 minutes max.

**Multi-profile setup:** If you have multiple QQ Bots running via profiles (see `references/qqbot-multi-instance.md`), each profile's gateway needs its own health check:
- Point `LOG_FILE` at the profile's log: `~/.hermes/profiles/<name>/logs/gateway.log`
- Use the profile's plist label for restart: `launchctl stop ai.hermes.gateway-<profilename>`
- Create a separate launchd plist for each health check

### Special case: "paused after N consecutive failures"

QQ Bot adapter has a safety valve: after 10 consecutive reconnect failures, it **pauses** itself to avoid hammering the API. The log will show:

```
qqbot paused after 10 consecutive failures (QQ startup failed: ...)
```

When paused, the adapter stops all retry attempts and sits idle. The health check watchdog above covers this (it detects `paused after|startup failed` patterns and restarts the gateway). To recover manually:

```bash
hermes gateway restart
```

Or from within a Hermes session (if you have an alternate platform like CLI or WeCom):

```
/platform resume qqbot
```

**Adapt for WeCom**: change `grep "qqbot"` to `grep "wecom"` in the health check script.

**Quick Restart If Already Down**

```bash
hermes gateway start
```

## Not a Connection Issue? Check Provider Balance

API credit exhaustion looks identical to bot disconnection: WebSocket stays alive but every LLM call fails silently. Before spending time debugging WebSocket issues, check your provider balance. See `references/api-balance-monitor.md` for automated monitoring via cron.
