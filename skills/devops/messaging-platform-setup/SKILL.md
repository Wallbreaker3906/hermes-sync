---
name: messaging-platform-setup
description: "Set up Hermes Agent on messaging platforms (QQ, WeCom, Telegram, Discord, etc.) — platform selection, credential acquisition, configuration, and troubleshooting."
version: 1.2.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [gateway, messaging, setup, wecom, qq]
---

# Messaging Platform Setup

Add Hermes Agent to messaging platforms so users can interact with it via chat apps (QQ, WeCom, Telegram, etc.).

## Quick Reference: Platform Comparison

| Platform | Adapter | Connection | Public URL Needed | Latency | Status |
|----------|---------|------------|-------------------|---------|--------|
| QQ | `qqbot` (Official API v2) | WebSocket | ❌ No | Seconds | ✅ Works on home Mac |
| WeCom AI Bot | `wecom` (AI Bot) | WebSocket | ❌ No | Seconds | ⚠️ 灰度，部分账号无此功能 |
| WeCom 自建应用 | `wecom_callback` (Self-built) | HTTP Callback | ✅ Yes | 3-30 min | Requires ngrok/cloud |
| Telegram | `telegram` | Webhook | ✅ Yes (or polling) | Seconds | — |
| Discord | `discord` | WebSocket | ❌ No | Seconds | — |

## General Setup Pattern

For ALL platforms, the pattern is:
1. Create a bot/app on the platform's developer portal
2. Get credentials (Bot ID / Token / Secret / App ID)
3. Add credentials to `~/.hermes/.env` or `config.yaml`
4. Hermes gateway auto-connects on restart

```bash
# After adding credentials, restart gateway:
hermes gateway restart
# Or for launchd (macOS):
launchctl stop ai.hermes.gateway && launchctl start ai.hermes.gateway
```

## Platform-Specific Guides

### QQ Bot (Official API v2)

**Prerequisites:** QQ Open Platform account at https://q.qq.com

1. Create bot app → Get **App ID** and **Client Secret**
2. Bot name and avatar are managed on QQ Open Platform (NOT in Hermes)
3. Config in `config.yaml`:
```yaml
platforms:
  qq:
    enabled: true
    extra:
      app_id: "your-app-id"
      client_secret: "your-secret"
```
4. Hermes connects via `wss://api.sgroup.qq.com/websocket`

**Pitfall:** The QQ adapter name in `platform_toolsets` is `qqbot` (not `qq`).

**Multi-instance QQ Bot:** To run multiple QQ Bots simultaneously, use **Hermes profiles** — each bot gets its own independent profile with its own gateway process. This is necessary because the gateway's platform system uses a `Platform` enum keyed by type (one adapter instance per platform type), so you cannot configure multiple `qqbot` entries in a single `config.yaml`.

**Setup recipe:**

1. Create a profile for the second bot:
```bash
hermes profile create qqbot2 --clone
```

2. Edit the profile's `.env` to replace `QQ_APP_ID` and `QQ_CLIENT_SECRET` with the second bot's credentials. Also set `QQ_ALLOW_ALL_USERS=true` if desired.

3. Create a separate launchd plist for the second gateway. The key difference from the default plist: set `HERMES_HOME` to the profile directory:
```xml
<key>EnvironmentVariables</key>
<dict>
    ...
    <key>HERMES_HOME</key>
    <string>/Users/$USER/.hermes/profiles/qqbot2</string>
</dict>
```
The plist label should be unique (e.g. `ai.hermes.gateway-qqbot2`), and log paths should point into the profile's `logs/` directory.

4. Each profile's gateway needs its own health check watchdog (see `references/gateway-macos-sleep.md`), pointing at the profile's log file and using the profile's plist label for restart.

See `references/qqbot-multi-instance.md` for a complete step-by-step walkthrough with all file paths and exact commands.

**Recovering from "paused after 10 failures":** When the QQ Bot adapter fails to reconnect repeatedly (e.g., after Mac sleep/wake), it pauses itself to avoid API abuse. Run `hermes gateway restart` to recover, or `/platform resume qqbot` from any Hermes session.

### WeCom (企业微信)

**Two modes — choose carefully:**

#### Mode A: AI Bot (WebSocket) — PREFERRED
- Real-time, no public URL needed
- Direct URL: `https://work.weixin.qq.com/wework_admin/frame#/app/createBot`
- ⚠️ **Not available to all WeCom accounts** (灰度功能)
- If the above URL redirects to homepage, your account doesn't have it
- ❌ **Does NOT support 客户联系 (customer contact with WeChat users)** — the AI Bot type cannot be added to the customer contact scenario. If you need the bot to talk to external WeChat customers, you must use Mode B (自建应用) instead.

#### Mode B: Self-Built App (Callback) — FALLBACK
- Path: 应用管理 → 创建应用 → 自建应用
- Needs: Corp ID, Agent ID, Secret, Token, EncodingAESKey
- **REQUIRES public URL** — home Mac behind NAT won't work
- Options for public URL: ngrok tunnel, cloud server, frp
- **Response delay: 3-30 minutes** (not real-time chat)
- See `references/wecom-self-built.md` for full setup

**Full setup details:** See `references/wecom-self-built.md` for credential locations, ngrok setup, and config templates.

#### Mode A Troubleshooting: errcode 853000

The WebSocket `aibot_subscribe` command returns `errcode=853000` ("invalid bot_id or secret"). This has **two distinct root causes** — diagnose in order:

**Cause 1 (MOST COMMON): Stale Secret after enabling 长连接**

If the user can see the 长连接 (long connection) toggle in their admin console and has enabled it, the Secret that was generated *before* enabling 长连接 is now invalid. The fix is simple:
1. Go to the AI Bot settings page in the WeCom admin console
2. Click the "重新生成" (Regenerate) button next to the Secret
3. Copy the NEW Secret (it will be a different length than the old one — e.g. 43 chars vs 42)
4. Update BOTH `.env` and `config.yaml` (the adapter reads from `config.yaml` first, then `.env`)
5. Run `hermes gateway restart`

**DO NOT assume 853000 always means grayscale restriction.** If the user confirms they can see the 长连接 toggle, try Secret regeneration FIRST before diagnosing as a grayscale issue.

**Cause 2: Corp not in grayscale allowlist**

If the user does NOT see the 长连接 option at all, or Secret regeneration doesn't fix it, then the corp is not whitelisted for the AI Bot WebSocket feature — even if the admin console shows the bot page and allows credential creation.

**Diagnostic flow (in order):**
1. Ask: "Can you see the 长连接 toggle in your AI Bot settings?"
   - YES → Ask them to regenerate the Secret and try again (Cause 1)
   - NO, or regeneration still fails → Proceed to Cause 2 checks below
2. Verify credentials are correctly copied (Bot ID starts with `aib`; Secret is 42-50 chars)
3. Verify both `.env` and `config.yaml` have identical values (no truncation, no hidden chars — verify with `grep WECOM ~/.hermes/.env | od -c`)
4. Check if the error persists across gateway restarts
5. The WeCom developer doc for the AI Bot WebSocket endpoint shows `gray_info.conf_file` in its metadata, confirming per-corp gating

**What to tell the user (Cause 2):** "The credentials are valid, but your enterprise (corp) hasn't been whitelisted for the AI Bot WebSocket feature yet. This is a server-side gate — nothing you configure locally will bypass it. Wait for the feature to roll out to your corp, or fall back to QQ."

**Resolution:** 
- Cause 1: Regenerate Secret → update both `.env` and `config.yaml` → `hermes gateway restart`
- Cause 2: Wait for WeCom to enable the feature for the corp, or fall back to QQ Bot (same real-time experience)

**Decision flow:**
```
Need customer contact (客户联系 / WeChat customers)?
  → YES: Mode A (AI Bot) does NOT support this — must use Mode B (自建应用) with ngrok/cloud
  → NO: Continue below

Can access AI Bot page?
  → YES: Can see 长连接 toggle?
    → YES: Does WebSocket connect (no 853000)?
      → YES: Mode A works — done
      → NO (errcode 853000): Try Cause 1 first — REGENERATE THE SECRET
        → FIXED: Done
        → STILL FAILS: Proceed to Cause 2 — corp not whitelisted
    → NO: Corp not whitelisted for WebSocket. Choose:
      → Wait for rollout, or use QQ Bot
      → Mode B with ngrok (3-30 min delay)
  → NO: Consider if 3-30min delay is acceptable
    → YES: Use Mode B with ngrok/cloud
    → NO: Abandon WeCom, use QQ instead
```

### Telegram
1. Create bot via @BotFather → get token
2. Set `TELEGRAM_BOT_TOKEN` in `.env`
3. Needs public webhook URL or polling

### macOS: Gateway Goes Down After Sleep

Two distinct failure modes after Mac sleep — diagnose which one you're hitting:

**Mode 1 — Gateway process killed:** macOS sends SIGKILL during sleep (exit -9). Launchd's `KeepAlive` tries to restart, but without `ThrottleInterval`, it may give up permanently after too many rapid restarts. **Fix:** Add `ThrottleInterval: 30` to the plist, plus set `KeepAlive` as a dict with `SuccessfulExit: false` (explicit non-zero-exit restart). Full details in `references/gateway-macos-sleep.md`.

**Mode 2 — Gateway alive but adapter disconnected:** The gateway process survives sleep, but the platform adapter's WebSocket reconnection fails because the network isn't ready yet (DNS: "nodename nor servname provided"). The adapter gives up and never retries. KeepAlive can't help because the process didn't die. **Fix:** Health check watchdog — a separate launchd job that checks adapter health every 10 minutes and restarts the gateway if disconnected too long.

**Two critical implementation lessons (hard-won):**

1. **Check Ready age, not error strings.** Matching specific error patterns is fragile — "Send failed: All connection attempts failed" and bare `ERROR` log lines slip through. Instead, check how old the last `Ready` log line is. If >30 minutes since last successful connection, restart. This catches every failure mode.

2. **Check for a real PID, not the launchd label.** `launchctl list "$NAME"` succeeds even when the process is dead (SIGKILL -9 leaves the label registered). If the script only checks the label, a dead gateway with a stale "Ready" in its log is falsely reported as healthy. Parse for an actual numeric PID: `launchctl list | grep "^[0-9].*PLIST$" | awk '{print $1}'`.

Full script + plist in `references/gateway-macos-sleep.md`. Ready-to-copy templates: `templates/gateway-healthcheck.sh` and `templates/gateway-healthcheck.plist`.

**Quick restart if already down:**
```bash
hermes gateway start
```

**⚠️ Before debugging WebSocket: check provider balance first.** API exhaustion looks identical to disconnection. See `references/api-balance-monitor.md` for automated balance alerts.

## WeCom Pairing (First-Time Authorization)

When a new user messages the WeCom bot for the first time, Hermes generates a pairing code and sends it to the user. The operator must approve the code before the user can chat.

### Normal flow
```bash
hermes pairing list                          # See pending codes
hermes pairing approve wecom <CODE>         # Approve
```

### Pairing approval fails silently

Sometimes `hermes pairing approve` returns "Code not found or expired" even though `hermes pairing list` shows the code. This appears to be a hash mismatch bug in the pairing store.

**Workaround — manually approve the user:**
```bash
cat ~/.hermes/pairing/wecom-pending.json    # Find user_id

# Create/update approved list:
python3 -c "
import json, time
uid = 'UserID_from_pending'
with open('$HERMES_HOME/pairing/wecom-approved.json','w') as f:
    json.dump({uid:{'user_id':uid,'user_name':uid,'approved_at':time.time()}},f,indent=2)
"
# Clear pending:
echo '{}' > ~/.hermes/pairing/wecom-pending.json
```

The gateway picks up the approved user on the next message — no restart needed.

## Common Pitfalls

1. **Gateway gone after Mac sleep:** Two modes — (a) process SIGKILL'd during sleep: add `ThrottleInterval: 30` to the plist so launchd doesn't give up after repeated restarts; (b) process alive but adapter disconnected: install the health check watchdog. Both fixes are needed for reliable auto-recovery. Full guide in `references/gateway-macos-sleep.md`.
2. **Gateway restart needed:** Platform changes only take effect after gateway restart
3. **Platform name mismatch:** Config uses `qq` for platforms section but `qqbot` for toolsets
4. **Home network limitation:** Self-built app / webhook modes need public URLs — home Mac needs ngrok or cloud deployment
5. **Credential storage:** Secrets go in `.env`, not `config.yaml`
6. **Duplicate credentials in .env:** When switching between WeCom modes (self-built app → AI Bot) or re-entering credentials, old `WECOM_BOT_ID` / `WECOM_SECRET` lines may remain. Check with `grep WECOM ~/.hermes/.env` — if you see multiple pairs, remove the stale ones. The adapter reads env vars line-by-line; duplicate keys can cause the wrong value to be used. Verify no hidden chars with `grep WECOM ~/.hermes/.env | od -c`.
7. **WeCom Secret expires after enabling 长连接:** The Secret generated before enabling the long connection toggle becomes INVALID. Even though the admin console still shows the old Secret, the WebSocket gateway will return errcode 853000 until the user clicks "重新生成" (Regenerate) and gets a new Secret. The new Secret will be a different length (e.g. 43 instead of 42 characters). Always update both `.env` AND `config.yaml` with the new Secret, then `hermes gateway restart`.
8. **AI Bot does not support customer contact (客户联系):** The WeCom AI Bot (Mode A) cannot be added to the 客户联系 scenario for replying to external WeChat customers. The admin console has no "可调用接口的应用" list for AI Bots. If you need customer contact functionality, use Mode B (自建应用) instead — but be aware that Mode B requires a public URL and has 3-30 minute response delay.
9. **QQ Bot pauses after repeated reconnect failures:** After Mac sleep/wake, network may not be ready when the adapter tries to reconnect. After 10 consecutive failures, the adapter pauses itself (log: "paused after 10 consecutive failures"). It stays paused until gateway restart. Fix: `hermes gateway restart` or `/platform resume qqbot`. The health check watchdog (`templates/gateway-healthcheck.sh`) covers this — it detects "paused after|startup failed" patterns in addition to the usual error strings.
10. **Health check misses "Session resumed":** After a WebSocket reconnect, QQ Bot logs "Session resumed" — NOT "Ready". If the health check searches only for `grep "Ready"`, a bot that reconnected via session resume looks identical to a dead bot — every check falsely reports OK while messages go unanswered. **Always grep for `Ready|Session resumed` together.** The template at `templates/gateway-healthcheck.sh` has this fix baked in.
11. **Health check script silently truncated:** The health check script can get truncated on disk (e.g., write_file or patch producing only 15 lines with just the PID check, losing all Ready-age logic). A truncated script will report every check as "OK" while the bot is actually dead — there is no visible error, just silent failure. After deploying any health check script: (a) verify line count with `wc -l`, (b) run it manually with `bash ~/Library/Scripts/hermes-qq-healthcheck.sh` and confirm it produces sensible output matching the current bot state, (c) keep a backup of the known-good script for quick recovery.
13. **QQ Bot can't search the web (\"访问不了外部网络\"):** The `platform_toolsets` entry for `qqbot` typically only includes `hermes-qqbot`, which lacks the `web` toolset. When a QQ user asks for information requiring internet access, the bot correctly reports it can't access the network — this is a toolset configuration issue, not a network problem. **Fix:** Add `web` to the qqbot platform_toolsets entry in `config.yaml` (and any profile copies), then restart the gateway. After restart, the bot gains `web_search` and `web_extract` tools.\n\n12. **API balance exhaustion masquerades as disconnection:** When the LLM provider runs out of credit, the bot stays connected but every API call fails — it looks exactly like a dead bot. Before debugging WebSocket issues, check provider balance: `curl -s https://api.deepseek.com/user/balance -H "Authorization: Bearer $DEEPSEEK_API_KEY"`. Set up a cron-based balance monitor (script with `no_agent=true`, schedule `every 6h`, deliver to `origin,qqbot`) that alerts when balance drops below a threshold. See `references/api-balance-monitor.md` for the full pattern.

## Verification

```bash
# Check gateway status
hermes gateway status

# Check if gateway process is alive
ps aux | grep -i hermes | grep -v grep

# Check launchd registration
launchctl list | grep hermes

# Check platform connection logs
grep -i "platform_name" ~/.hermes/logs/gateway.log | tail -10

# Check all connected platforms
grep "✓.*connected" ~/.hermes/logs/gateway.log

# Check for SIGTERM / unexpected shutdowns
grep -E "SIGTERM|shutdown|Stopping" ~/.hermes/logs/gateway.log | tail -10
```
