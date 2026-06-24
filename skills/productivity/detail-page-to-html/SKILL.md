---
name: detail-page-to-html
description: >-
  从船加网(boatplus.cn)产品详情图提取热区坐标，生成 HTML 代码。
  设计师出完详情长图后，用此技能分析图片、找到可点击热区、输出 <img>+<map>+<area> 完整代码。
  触发词：用户发来详情页 PNG 图片，说「生成代码」「提取热区」「详情图转HTML」等。
  前置技能：detail-page-layout-brief（出任务书） → detail-page-auto-generation（HTML自动排版截图出图，替代设计师手工） → 本技能提取热区转代码。
---

# 详情图热区提取 → HTML 代码生成

## 触发条件
用户发来船加网产品详情页长图（PNG），要求提取热区坐标或生成 HTML 代码。

**注意**：如果详情页是用 `detail-page-layout-brief` 方案B（HTML 自动生成 + 截图）出的图，热区已作为 `<a>` 标签内嵌在源 HTML 中，无需走本技能的 OCR 流程——直接从源 HTML 提取链接即可。本技能仅用于设计师手工排版的图片。

## 核心规则

### 坐标换算（最重要）
详情图原图宽 **1660px**（@2x 视网膜图），但网页容器宽 **830px**。
**所有从原图检测到的坐标，X 和 Y 都必须除以 2**，才是 HTML `<area>` 中使用的坐标。

### 两遍扫描法

#### 第一遍：显式热区
用 OCR 扫描全图，匹配指示词：
- 「点击查看」「点击了解」「点击此处查看」「了解」 等

找到的文本区域直接取包围盒 → 坐标 ÷2 → 热区。

#### 第二遍：隐式热区
扫描全图，寻找**统一指令说明**，如：
- 「点击下方橙色字样查看相关产品」
- 「点击下方蓝色字样……」

处理步骤：
1. 从指令中提取**特征描述**（颜色、加粗、下划线等）
2. 确定指令下方的**有效范围**
3. 用像素分析扫描该范围内符合特征的元素
4. 每个符合特征的元素 → 坐标 ÷2 → 热区
5. 隐式热区不需要每个都标注「点击查看」

**注意：背景大面积色带 ≠ 文字热区。** 需用像素连续性分析区分文字（孤立像素簇）和背景（连续大面积）。

## 工作流程

### Step 1: 获取图片基本信息
```bash
sips -g pixelWidth -g pixelHeight image.png
```
确认是 1660px 宽（标准 @2x 图）。

### Step 2: 区域结构分析
用 PIL 按 100px 步长扫描，输出区域色彩分布（WHITE / DARK / MIXED / REDDISH / BLUE），判断图片的板块结构：
- 顶部横幅 → 产品概览 → 参数表格 → 特性说明 → 底部链接区

### Step 3: OCR 文字提取
使用 macOS Swift Vision 框架（内置，无需安装依赖）。Swift 代码模板见 `references/swift-vision-ocr.swift`。

用法：
```bash
# 编译（首次~60s）
swiftc ~/.hermes/skills/productivity/detail-page-to-html/references/swift-vision-ocr.swift -o /tmp/ocr_image
# 运行
/tmp/ocr_image /path/to/image.png
```

Vision 返回归一化坐标（0-1，原点左下角）：
- `X_pixel = normalized_x × 1660`
- `Y_pixel = (1 - normalized_y - normalized_h) × 图片高度`

### Step 4: 扫描显式热区
从 OCR 结果中 grep 匹配关键词：`点击|查看|了解|此处|MORE|CLICK`

### Step 5: 扫描隐式热区
从 OCR 结果中 grep 匹配指令关键词：`下方|字样|橙色|红色|蓝色|加粗|点击`

如果有指令，进行像素分析（PIL）在指令下方区域扫描符合特征的元素。使用连通组件检测找到文本块，过滤掉大面积背景。

### Step 6: 容器边界检测（关键步骤）

**OCR 返回的是文字本身的紧凑边界，但热区应该是包含文字的视觉容器（按钮/色块/横幅区）。**

容器通常表现为：文字周围有一个与背景底色不同的区域，边缘可能有渐变阴影。

**检测方法：从外向内推进**

```python
def find_container_edge(start_x, y, dx, base_color, max_steps, sensitivity=10):
    """从 start_x 向文字方向走，找到颜色开始持续偏离 base_color 的起点。
    这就是容器边缘（渐变开始处）。"""
    cx = start_x
    dev_run = 0  # 连续偏离的像素数
    last_clean = cx
    
    for _ in range(max_steps):
        cx += dx
        p = img.getpixel((cx, y))
        diff = abs(p[0]-base_color[0]) + abs(p[1]-base_color[1]) + abs(p[2]-base_color[2])
        if diff > sensitivity:
            dev_run += 1
            if dev_run >= 3:  # 持续偏离 3px 以上 = 找到容器边缘
                return last_clean
        else:
            dev_run = 0
            last_clean = cx
    return last_clean
```

**流程：**
1. 在文字区域外侧远处（约 50-100px）取样**页面/横幅底色** `base_color`
2. 从外侧向文字方向逐像素推进
3. 当颜色**持续偏离**底色超过 `sensitivity`（默认 12）达到 3px 以上 → 标记为容器边缘
4. 四个方向（左、右、上、下）各执行一次
5. `sensitivity=10~15` 可捕获渐变阴影，太小会停在内部装饰线，太大会漏掉边界

**为什么不是从文字向外扩展？**
因为容器内部是文字（白色），从文字中心向外第一步就是白→容器色的大跳变，无法区分容器边界和内部装饰。从外向内推进才能精确捕获渐变起始点。

### Step 7: 坐标转换
所有检测到的像素坐标 ÷2（原因：@2x 视网膜图 → 830px 容器）：

```python
x1_html = x1_img // 2
y1_html = y1_img // 2
x2_html = x2_img // 2
y2_html = y2_img // 2
```

### Step 8: 输出 HTML
```html
<img src="图片URL" usemap="#hotspots" style="width:830px;" />
<map name="hotspots">
  <area shape="rect" coords="x1,y1,x2,y2" href="链接URL" target="_blank" alt="说明" />
  ...
</map>
```

链接 URL 中的 `cat` 和 `brand` 参数需用户确认后填入，不可臆造。

## Pitfalls

- ⚠️ **坐标 ÷2 不可忘**：最容易出错的环节。所有检测到的像素坐标必须除以 2。
- ⚠️ **文字边界 ≠ 热区边界**：OCR 给的是文字的紧凑包围盒，但热区应该覆盖包含文字的视觉容器（按钮/色块/横幅）。必须用「从外向内推进」法找到容器渐变边缘。容器通常比文字边界宽 10-40px，高 10-30px。
- ⚠️ **从外向内，不从内向外**：从文字中心向外扩展会遇到文字白色 → 容器色的跳变，无法区分容器边缘和内部装饰。正确做法是取样外侧底色，向文字方向推进，找持续偏离点。
- ⚠️ **容忍薄干扰**：容器内部可能有装饰细线（1-2px），用 `dev_run >= 3`（持续偏离 ≥3px）过滤，避免在内部元素处误停。
- ⚠️ **背景 ≠ 文字**：大面积橙/红/蓝色带是装饰背景，不是可点击文字。用像素连续性（孤立 vs 连续）区分。
- ⚠️ **特征不是固定颜色**：不同详情图的隐式热区特征不同——可能是橙色文字、蓝色文字、加粗文字……必须读指令文字来确定特征，不能预设。
- ⚠️ **Vision OCR 精度有限**：英文 OCR 质量好，中文有部分误识别（尤其是小号字体），必要时交叉验证。
- ⚠️ **图像 URL 路径不确定**：`https://www.boatplus.cn/statics/attachment/ueditor/YYYY/MM/DD/X/图片名.png` 中的日期路径需用户提供。
- ⚠️ **TCC 沙盒**：Swift 编译产物放 `/tmp/`，图片也先用 `osascript Finder duplicate` 到 `/tmp/` 避免权限问题。
- ⚠️ **execute_code 的 read_file 带行号前缀**：`read_file()` 返回 `"   123|content"` 格式的内容，不能用它读取后直接 write_file 写回——行号前缀会污染文件。用 Python 原生 `open().read()` 读取干净内容。
