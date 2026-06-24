---
name: product-image-generation
description: >-
  Generate product images (800×800) and LOGO images for boatplus.cn product listings.
  Triggers: 产品图, LOGO图, 生成产品图, 产品图片.
---

# Product Image & LOGO Generation

Generate clean, minimal product images and LOGO images for boatplus.cn listings. The golden rule: **simple is better**. Boatplus product images are straightforward product photos — not designed marketing cards.

## Workflow

1. Get the product's main photo (high-res, preferably the "clean" version from detail page work)
2. Understand the SKU variants and their distinguishing labels
3. Generate product images with square crop + label bar
4. Generate LOGO images from the official logo file
5. Save with clear SKU-linked filenames in a permanent location

---

## Product Images (800×800)

### Crop strategy

The goal is a square crop of the boat/product, centered, with the full product visible. The crop process requires user iteration — do NOT try to auto-detect and send without review.

1. Start by analyzing the image to find the product's approximate bounds (sample pixel brightness across columns)
2. Generate 3-5 crop variants at different x-offsets and send ALL for user selection
3. Let the user pick the best, then fine-tune (nudge left/right in ~30px increments)
4. Only finalize when the user confirms

### Label bar

- Height: 88px, at the bottom of the 800×800 image
- Color: semi-transparent black `rgba(0, 0, 0, 180-190)`
- Text: SKU version label (e.g., "汽油版", "电动增程版")
- Font: **Alibaba PuHuiTi 85-Bold** (`AlibabaPuHuiTi-2-85-Bold.otf`), 40pt, white
- Centered horizontally within the bar

### Logo watermark

- White/reversed version of the company logo, top-right corner
- Size: ~260px wide (generous, visible)
- Margin: ~24px from right and top edges

### Sending for review

Always send the images and let the user confirm. The crop position is subjective — don't assume.

---

## LOGO Images

### Two formats (match reference)

| Type | Size | Treatment |
|------|------|-----------|
| 品牌LOGO | 400×182 | Fill width with slight margin (12px each side) |
| 供应商LOGO | 290×254 | Full logo visible, slight margin (12px each side) |

### Critical rules

- **NEVER create or modify a company's logo.** Only use the official logo file provided by the user or extracted from official sources (PDF, website).
- Trim whitespace from the source logo before resizing (`numpy` + alpha channel mask)
- Use original logo colors on white background for standalone LOGO images
- Product images use the REVERSED/WHITE version of the logo (for visibility on dark boat backgrounds)

### Source priority

1. User-provided official logo file (best)
2. Extracted from company PDF (page 1-2, small images ~200-900px)
3. Website header logo (may be reversed/white-text version)

---

## Pitfalls

1. **Over-designing**: Do NOT add gradients, scene overlays, decorative badges, multiple text layers, or "design elements". The user explicitly rejected this. Boatplus product images are clean product photos.
2. **Logo fabrication**: Never add company name text alongside the icon to "complete" a logo. Only use the official logo as-is.
3. **Wrong logo colors**: Product images use white/reversed logo. Standalone LOGO images use the original color logo. Don't mix them up.
4. **Label confusion**: The user said "不够鲜艳" (not vibrant enough) but meant "不够显眼" (not prominent enough). Make labels BIG and bold, not colorful.
5. **Skipping user review**: Always get crop position confirmed. Never assume the first crop is correct.
6. **Sandbox issues**: Work files from ~/Documents/ may be blocked. Use `~/.hermes/shared/` for project files that need sandbox bypass.

---

## File Naming & Storage

### Naming pattern

```
欧卡_SKU-01_沧巡_产品图_汽油版.png
欧卡_SKU-02_沧巡_产品图_电动增程版.png
欧卡_品牌LOGO.png
欧卡_供应商LOGO.png
```

Include: company prefix, SKU number, product name, image type, variant label.

### Storage

Save to `~/Documents/[企业名]_[产品名]_图片/` and also mirror to `~/.hermes/shared/` for sandbox access. See `references/sandbox-bypass.md` for details.
