# API Balance Monitor (DeepSeek)

Prevent silent bot outages from exhausted provider credits. The bot stays connected (WebSocket alive) but every API call fails — indistinguishable from a dead bot.

## Pattern

Use a **cron job with `no_agent=true`** that runs a balance-check script every 6 hours. When the script produces output (balance below threshold), Hermes delivers it to the target platform. When balance is healthy, the script is silent (no delivery).

## Script

Place in `~/.hermes/scripts/deepseek-balance-check.sh`:

```bash
#!/bin/bash
# DeepSeek balance check — alerts when below threshold
# Cron: no_agent=true, script only. Output on low balance, silent otherwise.

API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env 2>/dev/null | cut -d= -f2 | tr -d ' ')
THRESHOLD=5  # CNY

if [ -z "$API_KEY" ]; then exit 0; fi

RESP=$(curl -s --max-time 10 https://api.deepseek.com/user/balance \
    -H "Authorization: Bearer $API_KEY" 2>/dev/null)

BALANCE=$(echo "$RESP" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(float(d['balance_infos'][0]['total_balance']))" 2>/dev/null)

if [ -z "$BALANCE" ]; then exit 0; fi

LOW=$(echo "$BALANCE < $THRESHOLD" | bc -l 2>/dev/null)
if [ "$LOW" = "1" ]; then
    echo "DeepSeek balance low: ${BALANCE} CNY (threshold: ${THRESHOLD} CNY). Recharge at https://platform.deepseek.com."
fi
```

Make executable: `chmod +x ~/.hermes/scripts/deepseek-balance-check.sh`

## Cron Job

```bash
hermes cron create "every 6h" \
    --name "DeepSeek Balance Monitor" \
    --no-agent \
    --script deepseek-balance-check.sh \
    --deliver origin,qqbot
```

Key settings:
- `no_agent=true`: script IS the job — no LLM involved, zero token cost
- `schedule: every 6h`: frequent enough to catch exhaustion within a workday
- `deliver: origin,qqbot`: alert goes to both CLI origin and QQ Bot
- Script is **silent on healthy balance** — only non-empty stdout triggers delivery

## Test

Run the script manually to verify:
```bash
bash ~/.hermes/scripts/deepseek-balance-check.sh
# No output = balance healthy (wired correctly, no false alert)
```

## Adapt for other providers

Same pattern works for any provider with a balance/usage API. Adjust:
1. API endpoint and auth header
2. JSON path to extract balance
3. Threshold currency/units
