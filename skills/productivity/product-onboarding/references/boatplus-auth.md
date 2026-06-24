# boatplus.cn 认证与访问控制

船加网（boatplus.cn）对信息资讯页面（`/information/`）实施了访问控制，需要登录后才能访问。

## 登录入口

- **页面**: `https://www.boatplus.cn/login.html`
- **API**: `POST /api/shop/member/login.do`
- **方法**: `Content-Type: application/x-www-form-urlencoded`

## 表单字段

| 字段 | 说明 |
|------|------|
| `username` | 用户名 |
| `password` | 密码 |
| `validcode` | 图形验证码 |

## 验证码

- **图片地址**: `/validcode.do?vtype=memberlogin`
- **类型**: 图形验证码（字母数字混合）
- **必须填写**，否则登录失败

## 403 防护 (openresty WAF)

`/information/` 路径下的页面（如招中标列表、详情页）和 `/api/` 路径（包括登录 API）返回 **403 Forbidden**，由 openresty 网关拦截。该 WAF 对 HTTP 客户端有选择性：

```
HTTP/2 403
Server: openresty/1.31.1.1
```

| 客户端 | 结果 | 说明 |
|--------|:--:|------|
| `curl` (默认 UA) | ✅ 200 | **唯一可靠的命令行工具** |
| Python `requests` | ❌ 403 | 即使带完整浏览器 headers、cookie 也会被拦截 |
| Python `urllib` | ❌ 403 | 同上 |

**规则：访问 boatplus.cn 的所有 HTTP 请求（含登录 API）必须用 `curl`，不要用 Python requests/urllib。** 原因可能是 openresty 基于 TLS 指纹（JA3）或 HTTP/2 特征进行过滤——curl 的原生 TLS 实现不被检测。

首页（`/`）和其他公开页面正常返回 200。JSESSIONID cookie 不足以访问 `/information/` 路径——需要完整的登录会话（登录后服务器端写入的 session 状态）。

## 登录流程

```
1. GET / → 获取 JSESSIONID cookie
2. GET /validcode.do?vtype=memberlogin → 获取验证码图片（需人工识别）
3. POST /api/shop/member/login.do
   Body: username=xxx&password=xxx&validcode=xxx
4. 成功后 → 可访问 /information/ 路径
```

## 已验证的登录响应

成功时服务器返回 JSON：
```json
{"result": 1, "message": "登录成功"}
```

失败时的响应（如验证码错误）：
```json
{"result": 0, "message": "验证码错误"}
```

## 自动化难点

~~图形验证码需要人工识别，无法完全自动化。~~ **经验证可用 OCR 自动识别**：

### 自动识别方案（推荐）

用 Swift Vision OCR 工具（详见 `references/macos-ocr.md`）识别验证码：

```bash
# 1. 下载验证码（用 session cookie）
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s \
  "https://www.boatplus.cn/validcode.do?vtype=memberlogin" \
  -o /tmp/captcha.png

# 2. OCR 识别（需先编译 /tmp/ocr，首次 ~60s）
/tmp/ocr /tmp/captcha.png

# 3. 使用识别结果登录
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s \
  -X POST "https://www.boatplus.cn/api/shop/member/login.do" \
  --data-urlencode "username=USER" \
  --data-urlencode "password=PASS" \
  --data-urlencode "validcode=OCR_RESULT"
```

**验证码识别率**：Swift Vision 对船加网的字母数字混合验证码（160×80px JPEG）识别率约 80-90%。单字符偶尔误识别（如 `C`↔`c`、`y`↔`v`），失败时刷新验证码重试即可。

### 备用方案

1. 下载验证码图片 → 发送给用户 → 用户输入后完成登录
2. 用户从浏览器导出已登录的 Cookie（跳过验证码步骤）
3. 用户手动登录后保持 session

## 资讯详情页 URL 格式

⚠️ **招标公告和招标公告共用同一个详情页模板**，仅靠标题前缀区分：

- 列表页: `/information/information_zhaobiaoList.html?type=2`
- 详情页: `/information/information_zhaobiaoDetail.html?id={id}`
  - 标题含「《招标公告》」→ 招标
  - 标题含「《中标公告》」→ 中标

**不是**两个不同的 URL 模式（不存在 `information_zhongbiaoDetail.html`）。列表页 HTML 中每条资讯的 `<h4>` 标签内包含《招标公告》或《中标公告》前缀，用于区分类型。
