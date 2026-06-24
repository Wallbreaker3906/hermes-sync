# 直接在 PNG 上替换字体（OCR + PIL 方案）

## 适用场景

只有旧版 PNG 图片、没有 HTML 源文件，需要把字体从 A 换成 B，但**版式、图片、色块全部保持原样**。

## 原理

1. 用 macOS Swift Vision OCR 提取所有文字区域（坐标 + 内容）
2. 用 PIL 逐个擦除旧文字（采样周边背景色填充）
3. 用 PIL 在新字体渲染相同文字，放到相同位置

## 脚本模板

### 第一步：OCR 提取文字区域（Swift）

```swift
import Vision
import AppKit
import CoreGraphics

let imgPath = "/path/to/old.png"
guard let img = NSImage(contentsOfFile: imgPath),
      let cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(0) }

let imgW = CGFloat(cgImage.width)
let imgH = CGFloat(cgImage.height)

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "en"]
request.recognitionLevel = .accurate

try? VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])

var json = "["
for obs in request.results ?? [] {
    guard let cand = obs.topCandidates(1).first else { continue }
    let text = cand.string
    let bb = obs.boundingBox
    let x = Int(bb.origin.x * imgW)
    let y = Int((1 - bb.origin.y - bb.height) * imgH)
    let w = Int(bb.width * imgW)
    let h = Int(bb.height * imgH)
    json += "{\"x\":\(x),\"y\":\(y),\"w\":\(w),\"h\":\(h),\"t\":\"\(text)\"},"
}
json += "]"
try? json.write(toFile: "/tmp/ocr_regions.json", atomically: true, encoding: .utf8)
```

### 第二步：擦除旧文字 + 写新字体（Python）

```python
import json
from PIL import Image, ImageDraw, ImageFont

with open("/tmp/ocr_regions.json") as f:
    regions = json.loads(f.read())

img = Image.open("/path/to/old.png").convert("RGBA")
draw = ImageDraw.Draw(img)
iw, ih = img.size

font_path = os.path.expanduser("~/Library/Fonts/NewFont-Regular.otf")
bold_path = os.path.expanduser("~/Library/Fonts/NewFont-Bold.otf")

for r in regions:
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    text = r["t"].strip()
    if w < 5 or h < 5 or not text: continue

    pad = 4
    x1, y1 = max(0, x-pad), max(0, y-pad)
    x2, y2 = min(iw, x+w+pad), min(ih, y+h+pad)

    # Sample border background color
    border_colors = []
    for px in range(x1, x2, 3):
        if y1 > 0: border_colors.append(img.getpixel((px, y1-1)))
        if y2 < ih: border_colors.append(img.getpixel((px, y2)))
    for py in range(y1, y2, 3):
        if x1 > 0: border_colors.append(img.getpixel((x1-1, py)))
        if x2 < iw: border_colors.append(img.getpixel((x2, py)))
    
    bg = (255,255,255,255)
    if border_colors:
        bg = (sum(c[0] for c in border_colors)//len(border_colors),
              sum(c[1] for c in border_colors)//len(border_colors),
              sum(c[2] for c in border_colors)//len(border_colors), 255)

    # Sample text color (darkest pixel in region)
    text_samples = [img.getpixel((px, py)) for py in range(y, min(y+h, ih), 2) for px in range(x, min(x+w, iw), 2)]
    if not text_samples: continue
    text_samples.sort(key=lambda c: c[0]+c[1]+c[2])
    text_color = (text_samples[0][0], text_samples[0][1], text_samples[0][2], 255)

    # Erase
    draw.rectangle([(x1, y1), (x2, y2)], fill=bg)

    # Redraw
    use_bold = (h > 16)
    font_file = bold_path if use_bold and os.path.exists(bold_path) else font_path
    font_size = max(8, min(int(h * 0.82), 64))
    try:
        font = ImageFont.truetype(font_file, font_size)
    except:
        continue

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    tx, ty = x + (w-tw)//2, y + (h-th)//2 - bbox[1]
    draw.text((tx, ty), text, fill=text_color, font=font)

img.convert("RGB").save("/path/to/new.png")
```

## 局限性

- 渐变/纹理背景上擦除会留下可见色块（只能取平均色填充）
- 字体大小估算不精确，不同字体字距不同
- 图片中的文字（如产品图上的标签）OCR 难以识别
- 对齐依赖 OCR 坐标精度，可能有 1-2px 偏移

## 最佳实践

优先级排序：
1. 有 HTML 源文件 → 直接改 CSS font-family 重新截图
2. 只有 PNG → 尝试本方案（适合纯色背景为主的图）
3. 复杂渐变背景 → 重建 HTML 并逐版对比修正
