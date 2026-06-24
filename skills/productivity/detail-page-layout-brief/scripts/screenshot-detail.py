"""
Playwright 截图脚本：HTML → 1660px @2x PNG
用法: python3 screenshot-detail.py /path/to/detail.html [output.png]
输出: 1660px 宽 PNG，符合船加网详情图上传标准
"""

from playwright.sync_api import sync_playwright
import sys, os
from PIL import Image

html_path = sys.argv[1] if len(sys.argv) > 1 else "detail.html"
output_path = sys.argv[2] if len(sys.argv) > 2 else html_path.replace('.html', '_1660px.png')

# Convert to file:// URL
if not html_path.startswith('file://'):
    html_path = 'file://' + os.path.abspath(html_path)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 830, "height": 800},
        device_scale_factor=2  # @2x 视网膜 → 1660px 输出
    )
    page.goto(html_path, wait_until="networkidle")
    
    # 动态获取完整页面高度
    full_height = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": full_height})
    
    page.screenshot(path=output_path, full_page=True)
    browser.close()

img = Image.open(output_path)
size_kb = os.path.getsize(output_path) / 1024
print(f"✅ {img.size[0]}×{img.size[1]}px  {size_kb:.0f}KB  →  {output_path}")
