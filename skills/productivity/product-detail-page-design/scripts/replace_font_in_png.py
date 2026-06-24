#!/usr/bin/env python3
"""
Replace fonts in a PNG image: OCR-extract all text regions, erase old text
with background color sampling, then re-render with Alibaba PuHuiTi.

Use when: HTML source is lost but old PNG exists, and only font needs changing.

Prerequisites:
  - macOS with Swift (for Apple Vision OCR)
  - Python 3 with PIL/Pillow
  - Alibaba PuHuiTi fonts installed in ~/Library/Fonts/

Usage:
  1. Run Swift OCR to extract text regions:
     swift ocr_extract.swift > /tmp/regions.json
  2. Run this script:
     python3 replace_font_in_png.py <old.png> <output.png> <regions.json>
"""

import json, sys, os
from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = os.path.expanduser("~/Library/Fonts/AlibabaPuHuiTi-2-55-Regular.otf")
FONT_BOLD = os.path.expanduser("~/Library/Fonts/AlibabaPuHuiTi-2-85-Bold.otf")


def replace_font(old_path, out_path, regions_path):
    with open(regions_path) as f:
        regions = json.loads(f.read())

    img = Image.open(old_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    iw, ih = img.size
    print(f"Image: {iw}x{ih}, {len(regions)} text regions")

    if not os.path.exists(FONT_REGULAR):
        print(f"ERROR: Font not found at {FONT_REGULAR}")
        sys.exit(1)

    processed = 0
    for r in regions:
        x, y, w, h = r["x"], r["y"], r["w"], r["h"]
        text = r["t"].strip()
        if w < 5 or h < 5 or not text:
            continue

        pad = 4
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(iw, x + w + pad), min(ih, y + h + pad)

        # 1. Sample original text color (darkest pixel = text)
        text_samples = []
        for py in range(y, min(y + h, ih), 2):
            for px in range(x, min(x + w, iw), 2):
                text_samples.append(img.getpixel((px, py)))
        if not text_samples:
            continue
        text_samples.sort(key=lambda c: c[0] + c[1] + c[2])
        text_color = text_samples[0]

        # 2. Sample border background
        border_colors = []
        for px in range(x1, x2, 3):
            if y1 > 0:
                border_colors.append(img.getpixel((px, y1 - 1)))
            if y2 < ih:
                border_colors.append(img.getpixel((px, y2)))
        for py in range(y1, y2, 3):
            if x1 > 0:
                border_colors.append(img.getpixel((x1 - 1, py)))
            if x2 < iw:
                border_colors.append(img.getpixel((x2, py)))
        if border_colors:
            bg = (
                sum(c[0] for c in border_colors) // len(border_colors),
                sum(c[1] for c in border_colors) // len(border_colors),
                sum(c[2] for c in border_colors) // len(border_colors),
                255,
            )
        else:
            bg = (text_samples[-1][0], text_samples[-1][1], text_samples[-1][2], 255)

        # 3. Erase old text
        draw.rectangle([(x1, y1), (x2, y2)], fill=bg)

        # 4. Pick font
        use_bold = h > 16 and os.path.exists(FONT_BOLD)
        font_file = FONT_BOLD if use_bold else FONT_REGULAR
        font_size = max(8, min(int(h * 0.82), 64))
        try:
            font = ImageFont.truetype(font_file, font_size)
        except Exception:
            continue

        # 5. Measure & center
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (w - tw) // 2
        ty = y + (h - th) // 2 - bbox[1]

        # 6. Draw
        tc = (text_color[0], text_color[1], text_color[2], 255)
        draw.text((tx, ty), text, fill=tc, font=font)
        processed += 1

    img = img.convert("RGB")
    img.save(out_path)
    print(f"Replaced {processed} text regions -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 replace_font_in_png.py <old.png> <output.png> <regions.json>")
        sys.exit(1)
    replace_font(sys.argv[1], sys.argv[2], sys.argv[3])
