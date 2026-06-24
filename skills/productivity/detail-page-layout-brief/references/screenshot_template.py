from playwright.sync_api import sync_playwright
import os, sys

# Usage: python3 screenshot_template.py <html_path> [output_path]
html_path = sys.argv[1] if len(sys.argv) > 1 else "file:///tmp/detail_page.html"
output_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/detail_page_1660px.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 830, "height": 800},
        device_scale_factor=2  # @2x 视网膜 → 输出 1660px 宽
    )
    page.goto(html_path, wait_until="networkidle")
    full_height = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": full_height})
    page.screenshot(path=output_path, full_page=True)
    browser.close()

size = os.path.getsize(output_path)
from PIL import Image
img = Image.open(output_path)
print(f"OK {img.size[0]}x{img.size[1]}px {size/1024:.0f}KB")
