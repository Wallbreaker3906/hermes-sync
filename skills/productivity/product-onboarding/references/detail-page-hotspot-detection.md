# 详情图热区检测与 HTML 代码生成

设计师交付整张详情长图（PNG）后，需要为图中的可点击区域生成 `<map><area>` HTML 代码。

---

## 热区类型

### 类型一：显式标注热区
图中明确有「点击查看XXX」等引导文字的区域 → 直接取该文字的边界框坐标。

### 类型二：隐性橙色文字热区（核心规则）
部分详情图使用**统一指令 + 橙色文字**模式：

> 在图中有一段统一说明「点击下方橙色字样查看相关产品」

在该说明下方的有限区域内，**所有橙色型号文字**都是可点击热区——每个上面不再单独标注"点击查看"。

**识别方法：**

1. 先在图中扫描「点击下方橙色字样」「点击查看」等统一指令文本
2. 确定指令下方的有效范围
3. 在有效范围内扫描**橙色像素群**（RGB：R>170, G 60-190, B<140）
4. 用连通域算法（BFS/DFS）将相邻橙色像素聚合成块
5. 过滤噪声：宽度<8px 或高度<8px 的块丢弃
6. 每个有效橙色块 = 一个 `<area>` 热区

**Python 示例（Pillow）：**

```python
from PIL import Image
from collections import deque

img = Image.open("detail_page.png")
w, h = img.size

# 定义橙色范围
def is_orange(pixel):
    r, g, b = pixel[0], pixel[1], pixel[2]
    return r > 170 and 60 < g < 190 and b < 140

# 在指定 Y 范围内扫描连通域
def find_orange_clusters(img, y_start, y_end):
    visited = set()
    clusters = []
    for y in range(y_start, y_end):
        for x in range(img.width):
            if is_orange(img.getpixel((x, y))) and (x, y) not in visited:
                # BFS 找连通域
                q = deque([(x, y)])
                visited.add((x, y))
                min_x, max_x, min_y, max_y = x, x, y, y
                while q:
                    cx, cy = q.popleft()
                    min_x, max_x = min(min_x, cx), max(max_x, cx)
                    min_y, max_y = min(min_y, cy), max(max_y, cy)
                    for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                        nx, ny = cx+dx, cy+dy
                        if (0 <= nx < img.width and 0 <= ny < img.height
                            and (nx, ny) not in visited
                            and is_orange(img.getpixel((nx, ny)))):
                            visited.add((nx, ny))
                            q.append((nx, ny))
                clusters.append((min_x, min_y, max_x, max_y))
    return clusters
```

### 类型三：标准导航按钮
详情图底部的品牌/分类跳转按钮 → 按设计规范取固定区域坐标。

---

## 热区链接目标

| 热区内容 | 链接目标 |
|----------|---------|
| 橙色型号文字 | `https://www.boatplus.cn/product/product_detail-{产品ID}.html` |
| 「查看同品牌更多产品」 | `https://www.boatplus.cn/product/product_retrieval.html?cat={分类ID}&brand={品牌ID}` |
| 品牌 Logo/名称 | `https://www.boatplus.cn/product/product_retrieval.html?brand={品牌ID}` |

**品牌 ID 和分类 ID 需从 boatplus.cn 已有页面提取**，不可编造。

---

## 输出格式

```html
<img src="https://www.boatplus.cn/statics/attachment/ueditor/{日期}/{编号}/{图片名}.jpeg" 
     usemap="#detailmap"/>
<map name="detailmap">
  <!-- 显式热区 -->
  <area shape="rect" coords="x1,y1,x2,y2" 
        href="https://www.boatplus.cn/product/product_retrieval.html?cat=159_169_195&brand=701"
        target="_blank" alt="查看倍豪全回转推进器"/>
  
  <!-- 橙色文字热区（隐性） -->
  <area shape="rect" coords="459,4323,546,4336"
        href="https://www.boatplus.cn/product/product_detail-71896.html"
        target="_blank" alt="相关产品"/>
  <area shape="rect" coords="1221,4018,1308,4334"
        href="https://www.boatplus.cn/product/product_detail-XXXXX.html"
        target="_blank" alt="相关产品"/>
</map>
```

**注意：**
- 坐标格式：`coords="x1,y1,x2,y2"`（左上角x, 左上角y, 右下角x, 右下角y）
- 热区坐标需根据实际图片像素精确确定，不可估算
- `target="_blank"` 让链接在新标签页打开
- 同页面多个热区链接到不同目标时，需确认每个热区对应的产品 ID
