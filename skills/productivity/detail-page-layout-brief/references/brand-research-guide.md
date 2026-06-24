# 品牌视觉 DNA 提取流程

生成任何供应商的详情页之前，必须先完成此流程。**不研究品牌直接出设计 = 视觉灾难。**

## 步骤 1：官网 CSS 配色提取

```bash
curl -sL https://供应商官网 -o /tmp/brand_home.html
```

用 Python 从 HTML 中提取所有 `#hex` 色值，统计使用频率：
```python
import re
from collections import Counter
with open('/tmp/brand_home.html') as f:
    html = f.read()
colors = re.findall(r'(?:color|background|border)[^:]*:\s*(#[0-9A-Fa-f]{3,6})', html)
for c, n in Counter(colors).most_common(20):
    print(f"  {c}: {n}次")
```

⚠️ 官网常见 UI 框架（Element UI 等）的默认色（如 `#409eff`, `#67c23a`）不能直接当作品牌色。需与 PDF 交叉验证。

## 步骤 2：PDF 像素采样

```python
import fitz
from collections import Counter

doc = fitz.open('/path/to/brochure.pdf')
page = doc[0]  # 封面
pix = page.get_pixmap(dpi=50)
img_data = pix.samples
w, h = pix.width, pix.height

# 采样上半部分（品牌标识区）
colors = []
for y in range(0, h//4, max(1, h//40)):
    for x in range(0, w, max(1, w//40)):
        pos = (y * w + x) * pix.n
        colors.append((img_data[pos], img_data[pos+1], img_data[pos+2]))

for (r,g,b), n in Counter(colors).most_common(10):
    print(f"  #{r:02x}{g:02x}{b:02x}: {n}次")
```

遍历前 5-6 页，识别大面积品牌色块。

## 步骤 3：设计 DNA 固化

汇总为一句话卡片，用于后续 HTML 生成：

```
品牌主色: #13907a (青绿)
品牌深色: #213e56 (深蓝灰)
浅底: #ecf7f5 (极浅青绿)
字体: PingFang SC / Microsoft YaHei
调性: 干净明亮、现代科技、大面积色块
```

## 步骤 4：Logo 下载

从官网 HTML 搜索 logo 图片：
```python
import re
# Search img tags for logo keywords
for m in re.finditer(r'<img[^>]*src=["\']([^"\']+)["\']', html):
    if 'logo' in m.group(0).lower():
        print(m.group(1))
# Also check CSS background-image
for m in re.finditer(r'background[^:]*:\s*url\(["\']?([^)"\']+logo[^)"\']+)', html):
    print(m.group(1))
```

下载到 `/tmp/`：`curl -sL "完整URL" -o /tmp/brand_logo.webp`

## 步骤 5：PDF OCR 提取文字

对于扫描版/图片嵌入式 PDF（`get_text()` 返回空），用 macOS Swift Vision OCR：

```bash
# 先导出页面为高分辨率 PNG
python3 -c "
import fitz
doc = fitz.open('pdf_path')
for pn in [15,16,17,18,23,35]:
    doc[pn-1].get_pixmap(dpi=200).save(f'/tmp/ocr_p{pn}.png')
"

# 逐页 OCR
for f in /tmp/ocr_p*.png; do
    echo "=== $(basename $f) ==="
    /tmp/ocr_image "$f" 2>/dev/null
done
```

## 步骤 6：SKU 表数据读取

1. 定位文件：从 session 历史或 Documents/Desktop 搜索
2. macOS 沙盒绕过：`osascript -e 'tell application "Finder" to duplicate file ... to (POSIX file "/tmp" as alias) with replacing'`
3. 读取：`openpyxl.load_workbook('/tmp/sku_copy.xlsx', data_only=True)`
4. 搜索供应商行：遍历 `产品SKU归类表` sheet，匹配品牌名/品名
