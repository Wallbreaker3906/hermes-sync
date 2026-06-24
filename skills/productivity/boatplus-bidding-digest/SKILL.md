---
name: boatplus-bidding-digest
description: "从船加网抓取招中标资讯，生成带二维码的Word简报推文。"
version: 1.0.0
---

# 船加网招中标简报生成

从 boatplus.cn 抓取指定日期区间的招标/中标资讯 → 生成带二维码的 Word 简报文档，供秀米排版使用。

## 前置依赖

```bash
pip install qrcode python-docx --quiet
```

## Step 0：自动计算日期区间

**默认规则**（用户说「来一份招中标简报」时自动执行）：
- **起始日** = 上一次成功生成简报的结束日期 + 1 天
- **截止日** = 下指令当天的前一天
- 示例：上次简报为 6/15-6/17，6/23 下指令 → 自动抓取 6/18-6/22

抓取后判断：
- 内容 < 5 条 → 告知用户内容偏少，询问是否扩展日期或等待
- 内容 ≥ 5 条 → 直接生成简报

用户无需每次手动指定日期范围。

## Step 1：登录船加网

账号：驾驶舱 / 1111。站点有图形验证码，需 OCR 绕过。

```bash
# 1. 拿 JSESSIONID
curl -c /tmp/bp_cookies.txt -s -o /dev/null "https://www.boatplus.cn/"

# 2. 下载验证码
curl -b /tmp/bp_cookies.txt -s -o /tmp/captcha_bp.png \
  "https://www.boatplus.cn/validcode.do?vtype=memberlogin"

# 3. OCR（Swift+Vision，首次编译约60s）
# 脚本路径：~/.hermes/skills/productivity/ocr-and-documents/scripts/ocr_image.swift
swiftc ~/.hermes/skills/productivity/ocr-and-documents/scripts/ocr_image.swift -o /tmp/ocr_image 2>/dev/null
OCR_CODE=$(/tmp/ocr_image /tmp/captcha_bp.png)

# 4. 登录
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s \
  -X POST "https://www.boatplus.cn/api/shop/member/login.do" \
  -H "Referer: https://www.boatplus.cn/login.html" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "username=驾驶舱" \
  --data-urlencode "password=1111" \
  --data-urlencode "validcode=$OCR_CODE"
```

## Step 0：自动确定日期区间（用户偏好）

**用户规则**：当用户说「来一份招中标简报」而不指定日期时，自动计算：
- **起始日** = 上一次成功生成简报的结束日期 + 1 天
- **截止日** = 下指令当天的前一天
- 内容 < 5 条时告知用户建议扩展区间；≥ 5 条直接生成。

> 最近一次简报日期记录在 session memory 中，每次生成后自动更新。

## Step 0.5：先查日期区间是否有内容

在正式开始抓取前，先用 API 快速扫描日期分布，避免在空日期区间浪费精力：

```bash
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/api/shop/news/list.do?type=2&pageNo=1&pageSize=50' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Referer: https://www.boatplus.cn/information/information_zhaobiaoList.html?type=2'
```

返回 JSON 结构：
```json
{
  "pageSize": 50,
  "totalCount": 7080,
  "currentPageNo": 1,
  "totalPageCount": 142,
  "result": [
    {
      "news_id": 14729,
      "name": "《中标公告》...",
      "homeyeartime": "2026",
      "homemonthtime": "06-22 ",
      "news_content": "<p>HTML正文</p>",
      ...
    }
  ]
}
```

用 Python 解析 `homemonthtime` 字段（格式 `"MM-DD "`，注意尾部有空格），判断目标日期区间内是否有内容。如果为空，告知用户建议调整区间。

## Step 2：API 分页抓取列表

**推荐用 API 而非 HTML 页面**——HTML 列表是 JS 动态渲染的，翻页参数无效，curl 只能抓到第一页。API 支持 `pageNo` 参数翻页。

```
GET /api/shop/news/list.do?type=2&pageNo=N&pageSize=50
```

```python
import re, json
from hermes_tools import terminal

target_dates = {'06-18', '06-19', '06-20', '06-21'}  # 不含年份
found = []

for page in range(1, 50):
    result = terminal(f"curl -b /tmp/bp_cookies.txt -s "
        f"'https://www.boatplus.cn/api/shop/news/list.do?type=2&pageNo={page}&pageSize=50' "
        f"-H 'X-Requested-With: XMLHttpRequest'", timeout=15)
    
    # 用 regex 提取字段（比 json.loads 更耐受控制字符）
    ids = re.findall(r'"news_id":(\d+)', result['output'])
    names = re.findall(r'"name":"([^"]*)"', result['output'])
    months = re.findall(r'"homemonthtime":"([^"]+)"', result['output'])
    years = re.findall(r'"homeyeartime":"([^"]+)"', result['output'])
    
    for nid, name, md, yr in zip(ids, names, months, years):
        md_clean = md.strip()
        if md_clean in target_dates and yr == '2026':
            found.append({'id': nid, 'title': name, 'date': f'{yr}-{md_clean}'})
    
    # 如果当前页最后一条日期已早于目标区间，停止翻页
    if months and months[-1].strip() < min(target_dates):
        break
```

> ⚠️ JSON 含 HTML 内容时可能有控制字符导致 `json.loads` 失败。优先用 regex 提取关键字段，或用 `json.loads(text, strict=False)`。

## Step 3：抓取文章详情

API：`POST /api/shop/news/detail.do`，参数 `id=NNN`

返回 JSON：
```json
{"result":1, "data": {"name":"标题", "news_content":"<p>HTML正文</p>"}}
```

用 curl 逐篇抓取，带 -b /tmp/bp_cookies.txt 保持登录态。

## Step 4：摘编规则

### 招标公告
保留原文结构（编号段落、采购内容、资格要求等），但**隐藏**：
- 联系电话、邮箱、地址 → 替换为 `***`
- 原文中的具体 URL → 替换为 `(详见原文)`

保留：采购计划编号/项目代码、采购品目、采购方式、备案时间、船舶规格、资格要求概述等。

### 中标公告
只保留**项目概要信息**，**不显示以下内容**：
- 中标方名称、候选人名称、供应商地址
- 投标报价、中标金额
- 评审专家名单、代理费
- 联系人、电话、邮箱、地址
- 采购人信息、招标代理信息

保留：项目编号/招标编号、采购方式、项目类型/概况描述、开标时间、公示时间/公告期限。

## Step 5：生成二维码

每个项目生成一个二维码，链接到船加网原文：

```python
import qrcode
url = f"https://www.boatplus.cn/information/information_zhaobiaoDetail.html?id={aid}"
img = qrcode.make(url, border=2, box_size=8)
img.save(f"qr_{type}_{aid}.png")
```

二维码临时存 /tmp/boatplus_qr/，后续嵌入 Word 后复制到用户可访问目录。

## Step 6：生成 Word 文档

用 python-docx 创建 .docx 文件。

**格式要求**：
- 默认字体：**宋体**（所有 Word 文档统一）
- 两页：第1页招标资讯，第2页中标资讯
- 页面标题：`📰 船加网招标资讯（M月D日-D日）` / `🏆 船加网中标资讯（M月D日-D日）`
- 每期引导语：「本期收录船舶行业XX项目N则，扫描各项目下方二维码登录船加网查看完整信息。」

**每条资讯结构**（从上到下）：
1. 二级标题：「N.《XX公告》项目名称」
2. 要点列表（bullet points）
3. 居中灰色斜体：「招标信息：请扫描下方二维码登录查看」或「中标信息：请扫描下方二维码登录查看」
4. 居中的二维码图片（宽度约 1.8 inch）

**保存路径**：`~/Documents/船加网招中标资讯_YYYYMMDD.docx`

## Step 7：二维码文件交付

QQ 私聊不支持发图片，将二维码复制到用户主目录下新建文件夹：

```bash
mkdir -p ~/船加网二维码_MMDD
cp /tmp/boatplus_qr/qr_*.png ~/船加网二维码_MMDD/
open ~/船加网二维码_MMDD/
```

## 重要提示

- 每期自动判断会话是否已有有效登录 cookie，避免重复登录
- 日期区间由用户指定，默认含起止日
- 推文最终由用户在秀米中排版装饰，本技能只出内容原稿
- OCR 验证码若识别错误，重新下载验证码重试即可

## 常见坑

- **验证码 OCR 首次经常失败。** Swift Vision 对扭曲字母识别率有限，`fncx` → 实际是 `eefn`。永远重试一次，第二次通常能过。重试时必须重新下载验证码（加时间戳参数防缓存）。
- **macOS grep 不支持 `-P`。** 所有正则提取用 Python `re` 模块，不要写 `grep -oP`。
- **JSON 含 HTML 控制字符。** `/api/shop/news/list.do` 返回的 `news_content` 字段含 `<p>` 标签等，`json.loads` 可能报 `Invalid control character`。用 `re.findall` 按字段提取，或 `json.loads(s, strict=False)`。
- **日期断档很常见。** 船加网不是每天都有内容——6月只有 4 天有发布（03日/15日/17日/22日）。碰到目标区间无内容时，告知用户并建议调整区间，不要硬做。
- **API 翻页上限。** `totalPageCount` 约 140 页，但实际可访问的约前 100 页（更早的返回空）。翻到空结果或日期越界时立即停止。
- **`homemonthtime` 尾部有空格。** 字段值是 `"06-22 "` 格式，必须 `.strip()` 后再比较。
