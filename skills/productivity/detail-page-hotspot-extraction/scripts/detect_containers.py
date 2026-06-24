"""
Container boundary detection for boatplus.cn detail page images.

Usage:
  1. Run OCR first (scripts/ocr_detail_image.swift) to get text positions
  2. Edit the HOTSPOTS list below with text pixel coordinates
  3. Run: python3 scripts/detect_containers.py <image_path>
  4. Output: HTML coords for each hotspot

Method:
  - For each hotspot: sample banner color above/below text (avoiding white text pixels)
  - Determine container type: full-width banner vs local button/block
  - Full-width: scan banner color to page edges
  - Local: walk from outside toward text, detect where color deviates from base
"""

from PIL import Image
import sys

def dist(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2])

def scan_to_edge(start_x, y, dx, base_color, max_steps, sensitivity=12):
    """Walk from start in direction dx, return where base_color ENDS."""
    cx = start_x
    dev_run = 0
    last_clean = cx
    for _ in range(max_steps):
        cx += dx
        if cx < 0 or cx >= 9999: break
        if dist(img.getpixel((cx, y)), base_color) > sensitivity:
            dev_run += 1
            if dev_run >= 3:
                return last_clean
        else:
            dev_run = 0
            last_clean = cx
    return last_clean

def find_fullwidth_bounds(y, base_color):
    """Find left/right edges of a full-width colored banner."""
    left = 0
    for x in range(0, img.width):
        if dist(img.getpixel((x, y)), base_color) < 15:
            left = x; break
    right = img.width - 1
    for x in range(img.width - 1, 0, -1):
        if dist(img.getpixel((x, y)), base_color) < 15:
            right = x; break
    return left, right

def find_vertical_bounds(mid_x, text_top, text_bottom, base_color):
    """Find top/bottom of colored container around text."""
    top = text_top
    for y in range(text_top, 0, -1):
        if dist(img.getpixel((mid_x, y)), base_color) < 10:
            top = y
        else:
            break
    bottom = text_bottom
    for y in range(text_bottom, img.height):
        if dist(img.getpixel((mid_x, y)), base_color) > 15:
            bottom = y - 1
            break
    return top, bottom


# ============================================================
# EDIT THIS LIST: (label, text_x1, text_x2, text_y1, text_y2)
# ============================================================
HOTSPOTS = [
    # Example from NGT-1 image:
    # ("点击了解 NMEA 2000网络", 242, 567, 54, 90),
    # ("点击此处查看 更多网关设备", 958, 1597, 4590, 4647),
]

# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 detect_containers.py <image_path>")
        sys.exit(1)
    
    img = Image.open(sys.argv[1])
    W, H = img.size
    
    for label, tx1, tx2, ty1, ty2 in HOTSPOTS:
        mid_x = (tx1 + tx2) // 2
        mid_y = (ty1 + ty2) // 2
        
        # Sample container color from above text (avoid white text)
        banner_color = img.getpixel((mid_x, max(0, ty1 - 10)))
        
        # Determine container type
        # Check if color spans full width
        left_check, right_check = find_fullwidth_bounds(mid_y, banner_color)
        is_fullwidth = (left_check < 60 or right_check > W - 60)
        
        if is_fullwidth:
            left, right = left_check, right_check
        else:
            # Local container: walk from outside toward text
            left = scan_to_edge(tx1 - 30, mid_y, -1, banner_color, 500)
            right = scan_to_edge(tx2 + 30, mid_y, 1, banner_color, 500)
        
        top, bottom = find_vertical_bounds(mid_x, ty1, ty2, banner_color)
        
        # HTML coords (÷2)
        hx1, hy1 = left // 2, top // 2
        hx2, hy2 = right // 2, bottom // 2
        
        print(f"  {label}")
        print(f"    像素: ({left},{top})→({right},{bottom})")
        print(f'    HTML: coords="{hx1},{hy1},{hx2},{hy2}"')
