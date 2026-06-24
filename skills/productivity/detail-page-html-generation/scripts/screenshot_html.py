"""
Playwright 截图脚本 — 将 HTML 渲染为 1660px @2x PNG。
用法: python3 screenshot_html.py <input.html> [output.png]
"""
import sys
from playwright.sync_api import sync_playwright

html_path = sys.argv[1] if len(sys.argv) > 1 else "file:///tmp/detail_page.html"
output_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/detail_1660px.png"

if not html_path.startswith("file://"):
    html_path = "file://" + html_path

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 830, "height": 800},
        device_scale_factor=2
    )
    page.goto(html_path, wait_until="networkidle")
    full_height = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": full_height})
    page.screenshot(path=output_path, full_page=True)
    browser.close()

import os
from PIL import Image
size = os.path.getsize(output_path)
img = Image.open(output_path)
print(f"DONE {img.size[0]}x{img.size[1]}px {size/1024:.0f}KB")
