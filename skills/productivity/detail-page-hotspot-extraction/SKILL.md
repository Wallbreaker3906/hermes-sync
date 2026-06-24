---
name: detail-page-hotspot-extraction
description: |
  从船加网(boatplus.cn)产品详情图(1660px @2x)中提取热区坐标，
  生成 <img> + <map> + <area> 富文本代码。
  支持显式热区("点击查看"/"了解")和隐式热区(统一指令+颜色/特征标记)。
version: 1.0.0
---

# 详情页热区提取

## 核心规则

1. **图片尺寸**: 原图 1660px 宽(@2x视网膜图)，网页容器 830px。
2. **坐标换算**: 所有像素坐标 ÷2 = HTML `<area>` 坐标。
3. **两类热区**:
   - **显式**: 文字含「点击查看」「了解」「查看详情」等 → 直接取容器坐标
   - **隐式**: 统一下指令「点击下方××字样查看相关产品」→ 在指令下方扫描符合特征的元素

## 完整流程

### 步骤1: OCR 识别全图文字

使用 macOS Vision 框架:

```python
import Vision
request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "en"]
request.recognitionLevel = .accurate
```

获取所有文字及其归一化坐标(原点左下，0-1)。

### 步骤2: 提取显式热区

搜索关键词: `点击查看` `点击了解` `了解` `点击此处` `查看更多` `MORE` `CLICK`

对每个匹配:
1. 转换归一化坐标为像素坐标
2. 确定容器类型(小按钮 vs 全宽横幅)
3. 提取容器边界

### 步骤3: 提取隐式热区

搜索统一指令: `点击下方.*字样查看`
1. 读懂指令中描述的特征(颜色/粗体/下划线等)
2. 在指令下方有效范围内扫描该特征
3. 每个匹配 = 一个热区

### 步骤4: 容器边界检测(关键!)

**判断容器类型**:
- 在文字上方/下方 5-10px 处取样背景色
- 向左/右扫描: 如果该颜色延伸到页面边缘(X<50 或 X>1610) → **全宽横幅**
- 否则 → **局部按钮/色块**

**全宽横幅**:
```python
# 从文字外侧取样横幅底色(避开白色文字像素)
banner_color = img.getpixel((mid_x, ty1 - 10))  # 文字上方10px
# 向两端扫描到边界
for x in range(0, W): 
    if matches(img.getpixel((x, y)), banner_color): left = x; break
for x in range(W-1, 0, -1):
    if matches(img.getpixel((x, y)), banner_color): right = x; break
```

**局部容器**:
```python
# 从远处向文字方向推进，检测颜色偏离持续 3+ px
base_color = img.getpixel((far_x, mid_y))  # 容器外50px+
for x in range(far_x, text_x, direction):
    if color_diff > 10:
        dev_run += 1
        if dev_run >= 3: boundary = last_clean; break
    else:
        dev_run = 0; last_clean = x
```

### 步骤5: 生成代码

```html
<img src="图片URL" border="0" usemap="#map_name" style="width:830px;" />
<map name="map_name">
  <area shape="rect" coords="x1,y1,x2,y2" href="链接" target="_blank" />
</map>
```

## 脚本工具

| 脚本 | 用途 |
|------|------|
| `scripts/ocr_detail_image.swift` | macOS Vision OCR，识别详情图中所有文字及归一化坐标 |
| `scripts/detect_containers.py` | 容器边界检测，支持全宽横幅和局部按钮两种模式 |

**OCR 编译与运行**:
```bash
swiftc ~/.hermes/skills/productivity/detail-page-hotspot-extraction/scripts/ocr_detail_image.swift -o /tmp/ocr_detail
/tmp/ocr_detail /path/to/detail.png > ocr_result.txt
```

**容器检测**：编辑脚本中 hotspots 列表 → 填入 OCR 获得的文字像素坐标和外侧取样点 → 运行即得 HTML 坐标。

## 参考资料

- `references/actisense-patterns.md` — 两张 Actisense 详情页（NGT-1 vs PRO-NDC-1E）的完整对比分析，含热区坐标、链接类型和检测教训

## 链接推断规则

当无法直接获取 URL 时，根据提示文字推断：

| 提示文字特征 | URL 类型 | 模式 |
|-------------|---------|------|
| 具体产品名/功能名 | 产品详情页 | `product_detail-XXXXX.html` |
| "更多XX设备""全部XX" | 分类列表 | `product_retrieval.html?cat=XXX&brand=YYY` |
| 系列名/品类名 | 关键词搜索 | `product_retrieval_list.html?keyword=系列名&brand=YYY` |

品牌 ID 可从同品牌其他产品页的 `brand=` 参数获得。

## 常见陷阱

- ❌ 从文字中心向外扩展 → 白色文字在白色底上会停在文字边缘
- ❌ 取样背景色时取到文字像素 → 判断容器类型失败
- ❌ 把全宽横幅当小按钮 → 坐标范围太小
- ❌ 被容器内部装饰细线(<5px)中断扫描 → 需容忍短暂偏离(8px规则)
- ❌ **只取"查看全部"按钮而忽略整个系列展示区** → 系列标题+产品卡片区往往是**一整块热区**(可高达1000px)
- ✅ 在文字上方/下方 5-15px 取样，避开文字区域
- ✅ 先判断全宽 vs 局部，再选对应检测策略
- ✅ 当检测到"系列产品"相关文字时，检查下方是否有产品卡片区域需要合并为一个大热区
- ✅ 先判断全宽 vs 局部(横幅色是否延伸到 X<50 或 X>1610)，再选对应策略
- ✅ 全宽横幅: 直接扫描横幅底色到页面边缘，不走"从文字向外扩展"逻辑
- ✅ 规格表/Features对比表/配件表中的型号名称是普通文字，不是热区 — 不要强行给表格文字加链接
