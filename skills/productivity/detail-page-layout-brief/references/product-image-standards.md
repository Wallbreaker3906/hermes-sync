# 产品图生成标准（船加网 800×800 缩略图）

## 核心原则

产品图 = 干净的产品照片 + 版本标签。**不是平面设计作品，不要做任何视觉创作。**

❌ 不要做：渐变背景、场景叠加、彩色标签、装饰元素、文字排版
✅ 只做：正方形截取产品主体 + 底部深色标签条标注版本

## 规格

| 属性 | 值 |
|------|-----|
| 尺寸 | 800×800 px |
| 格式 | PNG（RGBA） |
| 背景 | 原图直接截取，不加背景 |
| 标签条 | 底部，高 88px，深色半透明 rgba(0,0,0,190) |
| 标签字体 | 阿里巴巴普惠粗体 40pt，白色 |
| 标签文字 | SKU 版本名（如「汽油版」「电动增程版」） |
| 右上角 Logo | 供应商白色反白 Logo，约 260×89px（可选） |

## 字体

- **中文标签**：阿里巴巴普惠体 Bold（`AlibabaPuHuiTi-2-85-Bold.otf`）
- 字体路径：`~/Library/Fonts/AlibabaPuHuiTi-2-85-Bold.otf`
- 备选粗体：`AlibabaPuHuiTi-2-95-ExtraBold.otf`

## 截取流程

### 1. 分析原图产品位置
不要凭感觉截。用 PIL 逐列采样像素亮度，找到产品主体的左右边界。

```python
# 在中部高度扫描亮度，找到 bright > threshold 的起始/结束 x
mid_y = img.height // 2
row = [img.getpixel((x, mid_y))[0] for x in range(img.width)]
threshold = 130
boat_start = next(x for x, v in enumerate(row) if v > threshold)
boat_end = img.width - next(x for x, v in enumerate(reversed(row)) if v > threshold) - 1
```

### 2. 生成多版截取方案
因为正方形（1440×1440）可能比产品主体窄，生成 3-5 个不同左起位置的方案：
- 产品居中：`left = boat_center - 720`
- 偏右版：`left = boat_center - 600`
- 贴右版：`left = img.width - 1440`

### 3. 让用户选择
发送所有方案（用不同文件名），等用户指定后再出最终版。**不要自己替用户决定。**

### 4. 精准定位用户选中的版本
用户可能发回截图或说「这个很好」。用像素对比找出是哪个文件：

```python
user_img = Image.open(user_path)
for cand_path in candidates:
    cand = Image.open(cand_path)
    diffs = sum(1 for x,y in grid if pixel_diff(user, cand, x, y) > 5)
    if diffs == 0:  # 精确匹配
        selected = cand_path
```

### 5. 迭代微调
用户反馈「偏左/偏右」「船不全」等，每次只调 30-60px，不要大步跳。

## Logo 图生成

### 绝对规则
**不要创作、改编、美化企业 Logo。只提取原始 Logo 文件，等比缩放放到对应尺寸画布上。**

- ❌ 不要加背景色块、不要改颜色、不要加文字（Logo 里已有的字不用再加）
- ❌ 不要做「反白」版本（除非用户明确要求）
- ✅ 原始文件 → 原色等比缩放 → 白底居中

### 规格
| 类型 | 尺寸 | 来源 |
|------|------|------|
| 品牌 Logo | 400×182 | 倍豪 LOGO 参照 |
| 供应商 Logo | 290×254 | 倍豪 LOGO 参照 |

### 提取方法
1. 从官网 HTML 搜索 `<img src>` 或 CSS `background-image` 中含 `logo` 的 URL
2. 下载到 `/tmp/` 
3. 确认尺寸（通常 200-300px 宽）
4. 验证 Logo 内含文字（中文公司名 + 英文名），不含字的只是图标不是完整 Logo

## 标签文案

标签只说版本，不写产品名、不写卖点、不写口号。

| 产品 | 标签 |
|------|------|
| 沧巡汽油版 | `汽油版` |
| 沧巡电动增程版 | `电动增程版` |

## 常见错误

- ⚠️ **想得太复杂**：产品图不是海报/详情页/宣传卡。用户原话——「你不要把产品图想得太复杂了，可以去船加网上看看其他产品的产品图」
- ⚠️ **标签用鲜艳颜色**：用户要的是「显眼」不是「鲜艳」。深色半透明条 + 大白字就够显眼了，不要用品牌绿/金/蓝等色块
- ⚠️ **编造 Logo**：用户原话——「你怎么自己编造企业的LOGO标识？欧卡的LOGO有固定版本的，只要提取他们的LOGO即可，不用自己创作改编」
- ⚠️ **Logo 反白**：不要主动做反白 Logo，除非用户明确要求（如产品图右上角需要白色版）
