from playwright.sync_api import sync_playwright
import sys, os
from PIL import Image

# Usage: python3 screenshot_detail.py input.html output.png
html_path = sys.argv[1] if len(sys.argv) > 1 else "detail.html"
output_path = sys.argv[2] if len(sys.argv) > 2 else "detail_1660px.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 830, "height": 800},
        device_scale_factor=2  # Renders @2x → 1660px output for boatplus.cn
    )
    page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle")
    full_height = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 830, "height": full_height})
    page.screenshot(path=output_path, full_page=True)
    browser.close()

img = Image.open(output_path)
size_kb = os.path.getsize(output_path) / 1024
print(f"✅ {img.size[0]}×{img.size[1]}px, {size_kb:.0f}KB → {output_path}")
