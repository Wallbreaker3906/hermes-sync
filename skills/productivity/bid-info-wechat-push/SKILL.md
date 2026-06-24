---
name: bid-info-wechat-push
description: 从船加网抓取招中标资讯，摘编排版成公众号推文，附带原文二维码。适用于会员权益「政府招标信息定向推送」的履约执行。
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [船加网, 招标, 中标, 公众号, 推文, 二维码, 权益履约]
    related_skills: [membership-benefits-tracking, ocr-and-documents]
---

# 船加网招中标资讯 → 公众号推文

从船加网后台抓取指定日期区间的招标/中标公告，摘编排版为两篇独立推文（招标、中标各一篇），每篇附原文二维码引导读者登录查看。

## 触发条件

- 「生成招标推文」「抓取招标信息」「招中标资讯推送」
- 用户提供日期区间 + 船加网帐号

## 前置条件

需用户提供：
- 船加网登录帐号密码（前台帐号）
- 日期区间（如 6月15日-17日）
- 招标列表页 URL：`https://www.boatplus.cn/information/information_zhaobiaoList.html?type=2`

## 步骤

### 1. 登录船加网

船加网使用 openresty WAF，Python requests 库会被 403 拦截。**必须用 curl**。

登录流程：
```bash
# 1) 获取首页设置 session cookie
curl -c /tmp/bp_cookies.txt -s -o /dev/null "https://www.boatplus.cn/" 

# 2) 下载验证码
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s -o /tmp/captcha_bp.png \
  "https://www.boatplus.cn/validcode.do?vtype=memberlogin"

# 3) OCR 识别验证码（macOS Swift+Vision，见 ocr-and-documents 技能）
# 验证码图片是 JPEG（尽管扩展名 .png），尺寸 160×80

# 4) 提交登录
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s \
  -X POST "https://www.boatplus.cn/api/shop/member/login.do" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.boatplus.cn/login.html" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Origin: https://www.boatplus.cn" \
  --data-urlencode "username=USERNAME" \
  --data-urlencode "password=PASSWORD" \
  --data-urlencode "validcode=CAPTCHA"
```

成功响应：`{"result":1,"message":"登录成功","data":null}`

### 2. 获取招标列表

列表页通过 JS 动态渲染，需登录后访问 HTML 直接解析：

```bash
curl -b /tmp/bp_cookies.txt -s -o /tmp/bp_zhaobiao.html \
  "https://www.boatplus.cn/information/information_zhaobiaoList.html?type=2"
```

HTML 结构：每篇以 `<div class="newsList-left">` 包裹，内含：
- `<a href="information_zhaobiaoDetail.html?id=NNNN">` → 文章 ID
- `<h4>` → 标题（含「招标公告」或「中标公告」前缀）
- `<span>2026-06-17</span>` → 发布日期

按日期区间和类型（招标/中标）分组筛选。

### 3. 获取每篇原文

**关键**：详情页内容为 JS 动态加载，不能解析 HTML，必须调 API：

```bash
curl -b /tmp/bp_cookies.txt -s -X POST \
  "https://www.boatplus.cn/api/shop/news/detail.do" \
  -H "User-Agent: Mozilla/5.0" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "id=14719"
```

响应 JSON 结构：
```json
{"result":1, "data": {"news_id":NN, "name":"标题", "news_content":"HTML内容"}}
```

`news_content` 是 HTML，需用 `re.sub(r'<[^>]+>', '', text)` 提取纯文本。

### 4. 摘编规则（关键）

**不要自己写一句话总结**。从原文摘录信息，但刻意隐藏最有价值的关键信息，引导读者扫码查看原文。

#### 招标公告摘编
- ✅ 保留：项目概要、采购内容、项目编号/代码、资格要求概述、开标方式
- ❌ 隐藏：联系电话、邮箱、具体投标截止日期和时间、预算金额、招标文件下载链接

#### 中标公告摘编（更严格）
- ✅ 保留：项目概要、项目编号、招标方式、开标时间、公示时间
- ❌ 隐藏：中标方名称、候选人名称和排名、中标金额、联系人、联系方式

#### 每篇结尾
```
请扫描下方二维码登录查看
```
（注意是「下方」不是「上方」）

### 5. 生成二维码

每篇生成一个二维码，链接指向船加网原文：
```
https://www.boatplus.cn/information/information_zhaobiaoDetail.html?id={article_id}
```

```python
import qrcode
img = qrcode.make(url, border=2, box_size=8)
img.save(f"qr_{type}_{id}.png")
```

二维码存到用户可访问的本地目录（注意 macOS TCC 沙盒，Desktop/Documents 写入可能被拦截，优先存 `~/` 下）。

### 6. 组装推文

两篇独立推文：
- 📰 船加网招标资讯（日期区间）
- 🏆 船加网中标资讯（日期区间）

#### 推文结构模板

```markdown
## 📰 船加网招标资讯（X月X日-X月X日）

> 本期收录船舶行业招标项目N则，详情请扫描各项目下方二维码登录船加网查看。

---

**1. 标题**

摘编摘要（不含关键数字和联系方式）

MEDIA:/path/to/qr_xxx.png
> 招标信息：请扫描下方二维码登录查看

---

**2. 标题**
...
```

中标公告将「招标」替换为「中标」，前缀 emoji 用 🏆。

#### 排版要点

- 每篇顶部一句导语：「本期收录船舶行业XX项目N则，扫描各项目下方二维码登录船加网查看完整信息。」
- 每条之间用分隔线 `---` 隔开
- 二维码用 `MEDIA:/path/to/qr_xxx.png` 格式嵌入，紧跟对应条目下方
- 每篇结尾引导语：「请扫描下方二维码登录查看」（**注意是「下方」不是「上方」**）

## 坑点

- **Python requests 被 403**：船加网 openresty WAF 拦截非 curl 请求（可能是 TLS 指纹），必须全程用 curl
- **验证码是 JPEG**：文件扩展名 `.png` 但实际是 JPEG，Vision OCR 识别正常
- **详情页无内容**：HTML 中正文区域为空，内容通过 AJAX 加载，必须调 `/api/shop/news/detail.do` POST 接口
- **「上方」vs「下方」**：提示语必须写「扫描下方二维码」，不能写「上方」
- **中标不得暴露中标方**：这是用户核心诉求——推文是引流工具，有价值的信息（谁中标、多少钱）只能扫码登录后看原文

## 参考

- `references/boatplus-api.md` — 船加网 API 端点清单
- `references/redaction-rules.md` — 摘编规则详解
