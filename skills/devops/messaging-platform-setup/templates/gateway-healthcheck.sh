#!/bin/bash
# Hermes Gateway Health Check — adapter-disconnect watchdog
# Runs via launchd StartInterval; restarts gateway if platform adapter
# has been disconnected too long, OR if the gateway process is dead.
#
# Two detection methods (both needed):
#   1. PROCESS CHECK: verify a real PID exists (NOT just launchctl label)
#   2. READY-AGE CHECK: if last "Ready" log is >MAX_IDLE seconds old, restart
#
# Why not grep for error strings? Fragile. New error types (e.g. "Send failed",
# "ERROR" level lines) slip through. Checking Ready age catches everything.
#
# Usage: customize PLATFORM, PLIST_NAME, LOG_FILE, and MAX_IDLE,
#        then install with the companion launchd plist.

set -euo pipefail

LOG_FILE="${LOG_FILE:-$HOME/.hermes/logs/gateway.log}"
PLATFORM="${PLATFORM:-qqbot}"
PLIST_NAME="${PLIST_NAME:-ai.hermes.gateway}"
MAX_IDLE="${MAX_IDLE:-1800}"  # Ready older than this (seconds) = treat as disconnected

# ── 1. Process-liveness check ───────────────────────────────────────
# CRITICAL: launchctl list "label" succeeds even when the process is
# dead (exit -9, no PID). Must check for an actual numeric PID, not
# just label existence. A dead process with stale "Ready" in the log
# will pass the Ready-age check below otherwise.
PID=$(launchctl list | grep "^[0-9].*${PLIST_NAME}$" | awk '{print $1}')
if [ -z "$PID" ] || [ "$PID" = "-" ]; then
    echo "[$(date)] $PLATFORM: gateway process DEAD, restarting..."
    launchctl start "$PLIST_NAME" 2>/dev/null || \
        launchctl load ~/Library/LaunchAgents/${PLIST_NAME}.plist 2>/dev/null
    exit 0
fi
# ────────────────────────────────────────────────────────────────────

# ── 2. Connection-age check ─────────────────────────────────────────
# Find the last successful connection and check how old it is.
# Checks BOTH "Ready" (initial connect) AND "Session resumed" (reconnect
# after WebSocket drop). Missing "Session resumed" is a known pitfall —
# it looks identical to being disconnected and every health check
# falsely reports OK while the bot is actually dead.
LAST_READY=$(grep -i "$PLATFORM" "$LOG_FILE" 2>/dev/null | grep -E "Ready|Session resumed" | tail -1)

if [ -n "$LAST_READY" ]; then
    READY_TIME=$(echo "$LAST_READY" | awk '{print $1, $2}' | sed 's/,/./')
    READY_TS=$(date -j -f "%Y-%m-%d %H:%M:%S" "$READY_TIME" "+%s" 2>/dev/null || echo 0)
    NOW_TS=$(date "+%s")
    IDLE=$((NOW_TS - READY_TS))

    if [ "$IDLE" -lt "$MAX_IDLE" ]; then
        echo "[$(date)] $PLATFORM OK (Ready: ${IDLE}s ago)"
        exit 0
    fi

    echo "[$(date)] $PLATFORM: Ready stale (${IDLE}s > ${MAX_IDLE}s), restarting..."
    launchctl stop "$PLIST_NAME" 2>/dev/null
    sleep 2
    launchctl start "$PLIST_NAME" 2>/dev/null
    echo "[$(date)] $PLATFORM: gateway restarted"
    exit 0
fi
# ────────────────────────────────────────────────────────────────────

# ── 3. Fallback: no Ready line found ────────────────────────────────
LAST_LINE=$(grep -i "$PLATFORM" "$LOG_FILE" 2>/dev/null | tail -1)

if [ -z "$LAST_LINE" ]; then
    echo "[$(date)] $PLATFORM: no log entries, skipping"
    exit 0
fi

# Give the adapter's native reconnect logic a chance
if echo "$LAST_LINE" | grep -q "Reconnecting in"; then
    echo "[$(date)] $PLATFORM: reconnecting, waiting..."
    exit 0
fi

# Anything else (errors, "Send failed", "paused after", unknown) —
# if the last line is >3 min old, restart
LAST_TIME=$(echo "$LAST_LINE" | awk '{print $1, $2}' | sed 's/,/./')
LAST_TS=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_TIME" "+%s" 2>/dev/null || echo 0)
NOW_TS=$(date "+%s")
ELAPSED=$((NOW_TS - LAST_TS))

if [ "$ELAPSED" -gt 180 ]; then
    echo "[$(date)] $PLATFORM: error/idle for ${ELAPSED}s, restarting..."
    launchctl stop "$PLIST_NAME" 2>/dev/null
    sleep 2
    launchctl start "$PLIST_NAME" 2>/dev/null
    echo "[$(date)] $PLATFORM: gateway restarted"
else
    echo "[$(date)] $PLATFORM: error state ${ELAPSED}s ago, waiting..."
fi
