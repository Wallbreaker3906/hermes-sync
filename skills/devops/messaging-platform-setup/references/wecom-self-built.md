# WeCom Self-Built App (Callback Mode) Setup

> ⚠️ **Use only when AI Bot (WebSocket mode) is unavailable.**
> Self-built apps have 3-30 minute response delay and require a public URL.

## Why This Mode Exists

Some WeCom accounts don't have access to the "AI Bot" feature (灰度功能, gradually rolled out). The direct creation URL `https://work.weixin.qq.com/wework_admin/frame#/app/createBot` redirects to homepage for these accounts. Self-built apps with callback mode are the fallback.

## Required Credentials

From WeCom admin → 应用管理 → 自建应用:

| Field | Where to Find | Example |
|-------|--------------|---------|
| Corp ID | 我的企业 → 企业信息 → 底部 | `ww4c75bd5437198158` |
| Agent ID | 应用详情页顶部 | `1000002` |
| Secret | 应用详情 → Secret 区域 | `4s_XQXGK9CQ3FpmZ...` |
| Token | 接收消息 → 回调配置 | Random string (WeCom generates) |
| EncodingAESKey | 接收消息 → 回调配置 | 43-char random string (WeCom generates) |

## The Public URL Problem

The callback adapter needs WeCom to POST messages to Hermes. This requires a **publicly accessible URL**. A home Mac behind a router doesn't have one.

### Solutions

1. **ngrok tunnel** (free tier, easiest)
   ```bash
   brew install ngrok  # or download from ngrok.com
   ngrok http 8645
   # Gives you: https://xxxx.ngrok.io → localhost:8645
   # Callback URL: https://xxxx.ngrok.io/wecom/callback
   ```

2. **frp (free, self-hosted)**
   - Requires a VPS with public IP as frp server
   - More stable than ngrok free tier

3. **Cloud deployment** (best, costs money)
   - Deploy Hermes gateway on a VPS (阿里云/腾讯云 轻量服务器 ~¥50/mo)
   - No tunnel needed, always online

## Config Setup

In `~/.hermes/.env`:
```bash
WECOM_CALLBACK_CORP_ID=ww4c75bd5437198158
WECOM_CALLBACK_CORP_SECRET=4s_XQXGK9CQ3FpmZthvG88UgIxQoW3PF_hy62k_klZI
WECOM_CALLBACK_AGENT_ID=1000002
WECOM_CALLBACK_TOKEN=your-token
WECOM_CALLBACK_ENCODING_AES_KEY=your-43-char-key
WECOM_CALLBACK_HOST=0.0.0.0
WECOM_CALLBACK_PORT=8645
```

In WeCom admin → 应用 → 接收消息:
- URL: `https://your-public-url/wecom/callback`
- Token: same as `WECOM_CALLBACK_TOKEN`
- EncodingAESKey: same as `WECOM_CALLBACK_ENCODING_AES_KEY`

## Limitations vs AI Bot Mode

| Feature | AI Bot (WebSocket) | Self-Built (Callback) |
|---------|-------------------|----------------------|
| Response speed | Seconds | 3-30 minutes |
| Streaming | ✅ Yes | ❌ No |
| Typing indicator | ✅ Yes | ❌ No |
| Text input | ✅ Yes | ✅ Yes |
| Image/file input | ✅ Yes | ❌ Text only |
| Public URL needed | ❌ No | ✅ Yes |
| Group chat | ✅ Yes | ❌ Not supported |

## Verdict

If the user can't access AI Bot mode and needs real-time chat, **steer them toward QQ Bot** instead — it has WebSocket, real-time responses, and no public URL requirement. WeCom self-built app is only worthwhile when:
- The user's organization REQUIRES WeCom
- 3-30 minute delay is acceptable for their use case
- They have or can set up a public URL (ngrok/cloud)
