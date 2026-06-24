---
name: product-detail-page-design
description: >
  用 HTML/CSS + Playwright 截图生成船加网产品详情图（1660px @2x PNG）。
  输入：供应商 PDF 宣传册 + SKU 归类表 Excel。
  输出：每个 SKU 一张详情长图，含品牌色、Logo、产品图、场景图、参数表等。
  触发词：「生成详情图」「详情页设计」「出详情图」。
---

# 产品详情页 HTML 设计 → PNG 出图

## 触发条件
用户说「生成详情图」「出详情图」「设计详情页」等，或完成 SKU 录入后需要出图。

## 前置依赖
- Playwright + Chromium（一次性安装：`pip3 install playwright && playwright install chromium`）
- 本机 Python 环境（playwright, PIL）
- macOS Swift Vision OCR（`/tmp/ocr_image`，用于 PDF 文字识别）

## 完整工作流（8步）

### 1. 品牌视觉研究（必须先做！）
**不要凭自己的审美配色。** 每个供应商有独立的品牌视觉体系。

- **色彩提取**：从 PDF 宣传册像素采样（`fitz` + PIL），重点关注首页/封面大面积色块；官网 CSS 辅助验证
- **Logo 下载**：从官网 HTML 中找 `<img src="...logo...">`，下载到 `/tmp/`
- **字体**：使用阿里巴巴普惠体（Alibaba PuHuiTi），开源永久免费商用，无授权风险

### 2. 内容提取（三个来源并行）
| 来源 | 提取方法 | 用途 |
|------|---------|------|
| SKU Excel | openpyxl 读取 | 参数表权威数据 |
| PDF 宣传册 | fitz 导出页面→PNG→Swift OCR | 产品亮点、应用场景、性能描述 |
| 官网产品页 | curl HTML→解析图片/文字 | 场景示意图、产品轮播图 |

**⚠️ 内容验证原则：**
- 参数以 SKU 表为准（用户可能对 PDF 中某些数据做过修正）
- PDF 中的图片必须确认是当前产品，不是同品牌其他型号
- 注意发布时间——新产品不能用旧案例图
- 官网图片文件名通常就是场景名（如 `xunluo.webp`=巡逻、`jiuyuan.webp`=救援），可直接用

### 3. 图片素材准备
- 产品主图：PDF 相关页面高清截图（400dpi），用户可能需要在 PS 中去掉违规文字
- 场景图：从官网下载应用场景示意图
- Logo：PNG 或 WebP，嵌入 HTML 用 file:// 引用
- **选取原则**：选能看清的图，不要选嵌满小图和文字的复杂页面

### 4. 链接设计规则
- **只在船加网内部跳转**，不链接到外部网站（如企业官网）
- **不链接到其他品牌的页面**
- **SKU 之间互相引流**：每个版本只保留一个链接，指向同一产品的另一个 SKU
- 链接放在产品名称附近（顶部醒目位置），不放页面底部
- 产品未上传时 URL 留空，按钮样式先做好

### 5. 广告法合规
绝对禁止的极限词：首个、第一、唯一、最多、最长、最佳、最高级、全国首个……
- "首个XX产品" → "XX产品"
- "全国首个获XX认证" → "获XX认证"
- "数量最多、里程最长" → "数量领先、积累深厚"
- 注意：PDF 原图中的文字也要处理（用户 PS 修改或裁切）

### 6. 详情页内容结构（标准板块）
```
① 顶部导航：Logo + 分类标签
② 产品主图：精修产品图 + 标题 + 版本标签 + SKU互引链接
③ 关键参数横条：5-6 个核心数据
④ 产品概述：一段话概括
⑤ 产品优势：五高（通用性/集成性/扩展性/智能化/性价比）或类似
⑥ 性能优越：设计亮点描述
⑦ 技术参数表：从 SKU 表提取，可扩展导航/避障/通信/载荷
⑧ 标配/选配载荷：两栏对比
⑨ 核心亮点：PDF 中提取的特性（如多形/多能/多智/多护）
⑩ 产品展示装饰图：轮播图或细节图
⑪ 应用场景：场景图 + 每图下方功能描述
⑫ 安全可靠：安全特性描述
⑬ 企业介绍：公司简介 + 数据指标 + 联系方式
```

### 7. 视觉设计规范
- 底色：白色
- 品牌主色：从 PDF 提取（如欧卡青绿 #13907a）
- 产品特征色：少量点缀（如沧巡船体紫色 #7c5ce7），用于小标题下划线渐变、卡片左边框
- 品牌色和特征色比例约 90:10
- 场景图标签用深色渐变蒙版
- 引流按钮：深紫色底 + 白色文字 + 手指图标 + "点击查看：" 前缀
- 字体大小层级：标题 38-40px，正文 13-14px，辅助 11-12px

#### 字体选择与商用授权

**统一使用阿里巴巴普惠体（推荐）：**

```css
font-family: 'Alibaba PuHuiTi', 'AlibabaPuHuiTi', 'Alibaba PuHuiTi 2.0', sans-serif;
```

| 字体 | 来源 | 商用授权 |
|------|------|:--:|
| **Alibaba PuHuiTi（阿里普惠体）** | 阿里巴巴开源 | ✅ SIL OFL 永久免费商用 |
| PingFang SC（苹方） | macOS 系统自带 | ⚠️ macOS 系统字体，PNG 截图不涉及分发但非开源 |
| Microsoft YaHei（微软雅黑） | Windows 系统自带 | ❌ 方正的字体，商业网站展示需方正授权 |

**核心原则：** 详情图用于商业网站展示，必须使用明确免费商用的开源字体。阿里普惠体是唯一推荐选择，与产品图底部标签字体保持一致，品牌统一。

### 8. 多 SKU 处理
- **每个 SKU 一张独立详情图**，不同版本各自有不同的参数数据
- 生成汽油版 HTML → 用 Python 替换参数生成电动版 HTML
- ⚠️ 不要用 `execute_code` 中的 `read_file`+`write_file` 修改 HTML——`read_file` 返回带行号前缀（如 "  123|内容"）的内容，write_file 会原样写入导致文件污染
- 正确做法：用 `open()` 直接读文件（不带行号），Python 字符串替换后 `open().write()`

## 截图命令
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 830, "height": 800}, device_scale_factor=2)
    page.goto("file:///path/to/page.html", wait_until="networkidle")
    h = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": h})
    page.screenshot(path="output.png", full_page=True)
    browser.close()
```

## Pitfalls
- ⚠️ **品牌色不能猜**：必须先采样 PDF + 官网 CSS。深蓝不等于暗黑风，青绿不等于蓝色系
## Pitfalls
- ⚠️ **品牌色不能猜**：必须先采样 PDF + 官网 CSS。深蓝不等于暗黑风，青绿不等于蓝色系
- ⚠️ **PDF 内容≠全部是当前产品**：供应商 PDF 可能包含多款产品的内容。发布年份不对的内容不能用
- ⚠️ **execute_code 中 read_file 返回带行号前缀**：如 "  123|内容"，不能直接 write_file 回去，会污染 HTML/CSS。改用终端 `python3` 文件操作
- ⚠️ **Playwright 截图前确认 viewport**：width=830 + device_scale_factor=2 = 输出 1660px。如果输出不是 1660 宽，检查 HTML 是否有超宽元素
- ⚠️ **macOS 沙盒拦截 Documents**：用 `osascript -e 'tell application "Finder" to duplicate ...'` 绕过后再读
- ⚠️ **海况等参数以 SKU 表为准**：PDF 中可能有不同版本数据，用户录入 SKU 时已经核对过
- ⚠️ **HTML 源文件绝不能删**：每次生成详情页 HTML 必须永久保存到 `~/.hermes/shared/<项目名>/html/` 子目录，禁止仅存放在 `/tmp/` 等临时目录。用户已经因源文件丢失重新出过两次图，这是最严重的失误。
- ⚠️ **换字体 ≠ 重建版式**：如果只是换字体，优先用「直接编辑旧 PNG」方案（见 `references/font-replacement-on-png.md`），避免重写 HTML 导致版式变化。
- 🔴 **HTML 源文件必须永久保存！** 截图完成后，HTML 存到 `~/.hermes/shared/供应商_产品名/html/` 目录，不要只放 `/tmp/`。`/tmp/` 重启即清空，一旦丢失需要完整重建，极费时间。这是硬规则，不允许违反。
- 🔴 **字体必须用阿里普惠体**：`font-family: 'Alibaba PuHuiTi', 'AlibabaPuHuiTi', 'Alibaba PuHuiTi 2.0', sans-serif`。禁止使用 PingFang SC、Microsoft YaHei 或任何系统私有字体。阿里普惠体为阿里巴巴开源（SIL OFL），永久免费商用。见 references/font-policy.md。
- 🔴 **字体更换时优先用「直接 PNG 换字」技术**：如果 HTML 源文件丢失但有旧版 PNG，直接在旧版 PNG 上 OCR 提取文字位置 → 擦除旧文字 → 用 PIL + 阿里普惠体重新渲染。这比重建 HTML 更高效且版式 100% 保留。见 scripts/replace_font_in_png.py。
- ⚠️ **重新生成已有详情页时，必须对照旧版一比一还原版式**：只换字体不换版式。HTML 源文件迁移后可能丢失，旧版 PNG 就是唯一的版式参考。用 PIL 从旧版 PNG 精确采样颜色（不要凭记忆猜），有品牌规格参考文件时先加载再动工
- ⚠️ **品牌参数数据来源优先级**：用户发来的旧版 PNG > 品牌规格参考文件 > SKU Excel > PDF。旧版图片里的数据是用户最终确认过的权威版本

## 品牌规格参考文件
已收录品牌的详情页规格保存在 `references/` 目录：
- `orca-brand-spec.md` — 欧卡智舶，含版式结构、参数表、SKU差异、公司数据条
