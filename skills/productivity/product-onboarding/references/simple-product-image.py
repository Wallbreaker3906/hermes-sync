"""
模板：船加网产品图生成（800×800，极简风格）

使用方法：修改顶部 CONFIG，然后运行。
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np

# =========== CONFIG ===========
PRODUCT_IMAGE_PATH = "/path/to/product_hero.png"  # 产品主图
LOGO_PATH = "/tmp/orca_logo.webp"                 # 反白版 LOGO（白字+彩标，给深色底用）
OUTPUT_PATH = "/tmp/product_output.png"
LABEL = "汽油版"  # 或 "电动增程版"
FONT_PATH = "/Users/tinatang/Library/Fonts/AlibabaPuHuiTi-2-85-Bold.otf"
SIZE = 800
LABEL_H = 88          # 标签条高度
LABEL_FONT_SIZE = 40  # 标签字号
LOGO_W = 220          # 右上角 LOGO 宽度
LOGO_MARGIN = 24      # LOGO 距边缘距离
# =============================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", size)

def make_white_logo(logo, size):
    """将 LOGO 转为白色版（用于产品图右上角）"""
    logo = logo.resize(size, Image.LANCZOS)
    lw, lh = logo.size
    white = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    for x in range(lw):
        for y in range(lh):
            r, g, b, a = logo.getpixel((x, y))
            if a > 30:
                white.putpixel((x, y), (255, 255, 255, a))
    return white

# 加载素材
hero = Image.open(PRODUCT_IMAGE_PATH).convert("RGBA")
logo = Image.open(LOGO_PATH).convert("RGBA")
white_logo = make_white_logo(logo, (LOGO_W, int(LOGO_W * logo.size[1] / logo.size[0])))

# 1. 定位船体
arr = np.array(hero)
mid = hero.size[1] // 2
row = arr[mid, :, 0]
threshold = 130
boat = np.where(row > threshold)[0]
if len(boat) > 0:
    boat_start, boat_end = boat[0], boat[-1]
    boat_center = (boat_start + boat_end) // 2
else:
    boat_center = hero.size[0] // 2

# 2. 裁切正方形
sq = hero.size[1]  # 取高度为正方形边长
left = max(0, boat_center - sq // 2)
if left + sq > hero.size[0]:
    left = hero.size[0] - sq
cropped = hero.crop((left, 0, left + sq, hero.size[1]))
cropped = cropped.resize((SIZE, SIZE), Image.LANCZOS)

draw = ImageDraw.Draw(cropped)

# 3. 右上角白色 LOGO
lx = SIZE - white_logo.size[0] - LOGO_MARGIN
ly = LOGO_MARGIN
cropped.paste(white_logo, (lx, ly), white_logo)

# 4. 底部标签（半透明黑底 + 白字）
bar = Image.new("RGBA", (SIZE, LABEL_H), (0, 0, 0, 180))
cropped.paste(bar, (0, SIZE - LABEL_H), bar)

font = get_font(LABEL_FONT_SIZE)
bbox = draw.textbbox((0, 0), LABEL, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
draw.text(((SIZE - tw) // 2, SIZE - LABEL_H + (LABEL_H - th) // 2),
          LABEL, fill=(255, 255, 255), font=font)

cropped.save(OUTPUT_PATH)
print(f"✓ {OUTPUT_PATH}")
