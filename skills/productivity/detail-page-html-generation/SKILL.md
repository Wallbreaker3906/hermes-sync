---
name: detail-page-html-generation
description: >-
  用 HTML/CSS 直接生成船加网产品详情页，Playwright 截图出 1660px PNG，
  替代人工排版环节。输入：供应商 PDF + SKU 数据 + 品牌视觉分析。
  触发词：「生成详情页 HTML」「HTML 出图」「自动排版详情页」「不用设计师出图」。
  ⚠️ 前置：必须先完成品牌视觉 DNA 提取（官网+PDF 配色/Logo），不能凭猜测配色。
---

# 详情页 HTML 自动生成 + Playwright 截图

## 概述

这套流程替代「任务书 → 设计师 PS 排版 → 出图」中的人工排版环节，
用 HTML/CSS + Playwright 直接生成 1660px 的船加网详情长图。

适用于：产品数据完整（已有 SKU + PDF 宣传册）、品牌视觉可提取的供应商。

## 前置准备（一次性）

### 安装 Playwright
```bash
pip3 install playwright
python3 -m playwright install chromium
```

Playwright 二进制路径通常在 `~/Library/Python/3.9/bin/`，记入 PATH 或在脚本中用完整路径。

### 验证截图
```bash
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={'width':830,'height':600}, device_scale_factor=2)
    page.goto('file:///tmp/test.html', wait_until='networkidle')
    page.screenshot(path='/tmp/test.png', full_page=True)
    b.close()
print('OK')
"
```

## 工具脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| 品牌色提取 | `scripts/extract_brand_colors.py` | 从 PDF 自动采样品牌主色 |
| Playwright 截图 | `scripts/screenshot_html.py` | HTML 渲染为 1660px @2x PNG |

## 完整工作流（5 步）

### 第 0 步：品牌视觉 DNA 提取（最关键的步骤）

**不要在提取品牌色之前写任何 CSS。** 凭猜测配色 = 视觉灾难。

#### 从 PDF 宣传册提取品牌色
```python
import fitz
from collections import Counter

doc = fitz.open("供应商宣传册.pdf")
# 遍历前几页，采样 header 区域像素
for page_num in range(min(6, doc.page_count)):
    pix = doc[page_num].get_pixmap(dpi=50)
    # 采样页面上半部分（品牌色通常在 header）
    img_data = pix.samples
    w, h = pix.width, pix.height
    colors = Counter()
    step = max(1, min(w, h) // 20)
    for y in range(0, min(h//3, h), step):
        for x in range(0, w, step):
            pos = (y * w + x) * pix.n
            r, g, b = img_data[pos:pos+3]
            colors[(r, g, b)] += 1
    # 输出前 5 高频色
```

#### 从官网 CSS 提取辅助色
```python
import re, requests
html = requests.get("https://供应商官网").text
colors = set()
for m in re.finditer(r'(?:color|background)[^:]*:\s*(#[0-9A-Fa-f]{3,6})', html):
    colors.add(m.group(1).lower())
```

#### 提取 Logo
官网 HTML 中搜索 logo 图片：
```python
for m in re.finditer(r'background(?:-image)?\s*:\s*url\(["\']?([^)"\']+logo[^)"\']*)', html):
    logo_url = m.group(1)
```

常见命名：`/image/logo.webp`、`/image/logo-dark.svg`。

#### 输出品牌 DNA 清单
| 要素 | 值 | 来源 |
|------|-----|------|
| 品牌主色 | `#XXXXXX` | PDF 第 N 页大面积色块 |
| 品牌深色 | `#XXXXXX` | PDF 封面/header |
| 品牌浅底 | `#XXXXXX` | PDF 内页背景 |
| Logo 文件 | 路径 | 官网下载 |
| 字体风格 | 阿里普惠体（Alibaba PuHuiTi），开源免费商用 |
| 字体授权 | 见 `product-detail-page-design` 字体章节 | macOS 截图 → PingFang SC（免费商用） |

### 第 1 步：提取产品图片

从 PDF 宣传册中定位产品相关页面，导出为 PNG：
```python
doc = fitz.open("供应商宣传册.pdf")
for page_num in [16, 25, 26, 28]:  # 产品图所在页
    pix = doc[page_num - 1].get_pixmap(dpi=150)
    pix.save(f"/tmp/brand_images/page{page_num}.png")
```

产品图片用于嵌入 HTML 的 hero 区、特性展示区。如果 PDF 是扫描版且文字嵌入图片中无法提取，产品规格需要从 SKU Excel 或用户提供。

### 第 2 步：收集完整内容

- **产品规格**：从 SKU Excel 提取参数（型号、尺寸、动力、航速等）
- **产品优势/特性**：从 PDF + 官网提取
- **企业介绍**：从 PDF 企业介绍页 + 官网「关于我们」提取（资质、规模、行业地位）
- **应用场景**：从 PDF 案例页提取

### 第 3 步：编写 HTML

**CSS 变量必须从品牌 DNA 中取值，禁止硬编码颜色。**

```css
:root {
  --brand-primary: #13907a;    /* PDF 提取的品牌主色 */
  --brand-dark: #213e56;       /* 深色辅助色 */
  --brand-light-bg: #ecf7f5;   /* 浅底色 */
  --text-primary: #213e56;     /* 主文字色 */
  --text-secondary: #4a5c66;   /* 次级文字色 */
}
```

**板块结构**（按船加网详情图常规顺序）：
1. Hero 产品主图区（含 Logo + 品牌色背景 + 产品图 + 产品名）
2. 产品概述（文字 + 关键数据高亮卡片）
3. 技术参数表
4. 核心特性（网格卡片）
5. 企业介绍（资质/规模/行业地位）
6. 应用场景
7. 跳转链接区

**设计原则**：
- Logo 必须在 hero 区可见
- 产品实物图必须出现（从 PDF 截取）
- 品牌色大面积色块而非纯黑/纯白
- 留白适度，信息层级分明
- 白底为主、品牌色块点缀，不要全暗黑背景

### 第 4 步：Playwright 截图

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 830, "height": 800},
        device_scale_factor=2  # @2x → 1660px 输出
    )
    page.goto("file:///tmp/detail_page.html", wait_until="networkidle")
    full_height = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": full_height})
    page.screenshot(path="/tmp/detail_1660px.png", full_page=True)
    browser.close()
```

输出规格：1660px 宽 × 自动高度，PNG 格式。

### 第 5 步：热区提取（接 `detail-page-hotspot-extraction`）

生成 PNG 后，继续用现有热区提取技能处理。

## 链接规则

**链接必须基于真实 SKU 数据，禁止编造。**
- 产品详情页：`product_detail-XXXXX.html`（需确认实际产品 ID）
- 分类检索：`product_retrieval.html?cat=XXX_XXX_XXX_&brand=YYY`
- 品牌页：`product_retrieval.html?brand=YYY`
- 关键词搜索：`product_retrieval_list.html?keyword=关键词&brand=YYY`

如果产品尚未在船加网上线，跳转链接先留 `#`，标注「待产品上线后更新」。

## Pitfalls

- ⚠️ **品牌色不是猜的**：必须先完成第 0 步的 PDF+官网颜色提取，再写 CSS。凭感觉选色 = 品牌灾难。
- ⚠️ **Logo 不能缺**：详情页必须有供应商 Logo，从官网下载。
- ⚠️ **产品图片不能缺**：详情页没有产品实物图 = 毫无意义，从 PDF 截取关键页。
- ⚠️ **链接不能编**：必须查 SKU 数据确认产品 ID 和分类代码后才填链接，否则先留空。
- ⚠️ **内容要全面**：不只是产品参数，还要有企业介绍、应用场景——详情页是供应商的综合展示窗。
- ⚠️ **设计感不只是颜色**：排版节奏、留白、信息层级、图片使用——都需要考虑。如果审美判断力不足，请用户审核后再定稿。
- ⚠️ **同供应商多产品**：如果该供应商已有其他产品的 HTML 生成过，新产品的企业介绍、跳转链接可以复用，只需替换产品相关内容。
- ⚠️ Playwright 截图脚本不要放在 execute_code 中（沙盒无 playwright 模块），写成独立 `.py` 文件用 terminal 执行。
- ⚠️ **HTML 源文件必须永久保存**：生成 HTML 后立即保存到 `~/.hermes/shared/<项目名>/html/`，禁止仅放在 `/tmp/`。丢失源文件 = 后续任何修改都要重写整个页面，用户已为此付出过两次代价。
- 🔴 **HTML 源文件必须永久保存！** 截图完成后，HTML 文件存到 `~/.hermes/shared/供应商名_产品名/html/` 目录。严禁只放在 `/tmp/`。`/tmp/` 重启即清空，丢失后需完整重建——对复杂详情页（6 轮迭代以上）这意味着数小时重复劳动。这是硬规则。
- 🔴 **字体必须用阿里普惠体**：`font-family: 'Alibaba PuHuiTi', 'AlibabaPuHuiTi', 'Alibaba PuHuiTi 2.0', sans-serif`。阿里普惠体为阿里巴巴开源（SIL OFL），永久免费商用，无任何授权风险。禁止使用 PingFang SC、Microsoft YaHei 或 `-apple-system` 字体栈。详见 product-detail-page-design 技能的 references/font-policy.md。
- ⚠️ **HTML 源文件必须永久保存**：生成后存到图片目录的 `html/` 子目录，不能只放 `/tmp/` 截图完就清理。文件名：`detail_{品牌}_{SKU}.html`。
- ⚠️ **新电脑需重装 Playwright**：`python3 -m playwright install chromium`
