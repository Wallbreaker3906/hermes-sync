# 品牌视觉提取方法

## 从 PDF 宣传册提取主色

```python
import fitz
from collections import Counter

doc = fitz.open("供应商宣传册.pdf")
# 重点采样前 6 页的 header 区域（上半部分）
for i in range(min(6, doc.page_count)):
    page = doc[i]
    pix = page.get_pixmap(dpi=50)
    img_data = pix.samples
    w, h = pix.width, pix.height
    colors = []
    step = max(1, min(w, h) // 20)
    for y in range(0, min(h//4, h), step):
        for x in range(0, w, step):
            pos = (y * w + x) * pix.n
            r, g, b = img_data[pos], img_data[pos+1], img_data[pos+2]
            colors.append((r, g, b))
    top = Counter(colors).most_common(5)
    for (r,g,b), n in top:
        print(f"  #{r:02x}{g:02x}{b:02x}: {n}次")
```

主色通常出现在第 2-3 页的大面积底色中，辅助色出现在第 1 页的 header 区。

## 从官网 CSS 提取配色

```bash
curl -sL "https://www.xxx.cn" -o /tmp/home.html
```

然后用正则提取 `color/background/border` 中的 `#hex` 值，统计频率。但注意 Element UI / Bootstrap 等框架色会混入（如 `#409eff`），需与 PDF 品牌色交叉验证。

## Logo 获取

通常官网 Logo 路径包含 `logo` 关键词：
```bash
# 搜 img src
grep -o 'src="[^"]*logo[^"]*"' /tmp/home.html
# 也搜 CSS background-image
grep -o 'url([^)]*logo[^)]*)' /tmp/home.html
```

下载后用 `file:///tmp/xxx.webp` 直接嵌入 HTML。

## 实际案例：欧卡智舶

| 来源 | 提取值 |
|------|--------|
| PDF 第2页大面积底色 | `#13907a` 青绿（品牌主色） |
| PDF 第1页 header | `#213e56` 深蓝灰（辅色） |
| PDF 第6页背景 | `#ecf7f5` 极浅青绿（底色） |
| 官网字体 | PingFang SC, Microsoft YaHei, Alibaba |
