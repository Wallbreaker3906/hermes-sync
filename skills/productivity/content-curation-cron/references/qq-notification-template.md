# QQ Notification Template for Daily Cases

This is the preferred QQ notification format for daily case updates. Place it as the **final step** in the cron job prompt.

## Template

```
☀️ 今日 Hermes 案例已更新！Day N

🏭 [行业1] — [案例标题1]
🏭 [行业2] — [案例标题2]
🏭 [行业3] — [案例标题3]

👉 https://wallbreaker3906.github.io/hermes-cases/
```

## Key Rules

- Use emoji for visual scannability (☀️, 🏭, 👉)
- Include the GitHub Pages link so the user can tap directly
- Each line is a single emoji + industry + title — keeps it short for mobile chat bubbles
- The notification step MUST use `send_message` and MUST be the last step in the cron prompt
- The cron job MUST have `messaging` in `enabled_toolsets` for `send_message` to work

## Why `send_message` is needed on top of `deliver: origin`

`deliver: origin` auto-delivers the agent's final response text. But if the agent's final response is task-oriented (e.g., "Updated with Day 3 content"), the notification format above needs an explicit `send_message` call to produce the user-facing message in the right format.
