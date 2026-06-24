"""Playwright 截图脚本 — 将 HTML 渲染为 1660px @2x PNG 详情图"""
from playwright.sync_api import sync_playwright
from PIL import Image
import os, sys

def screenshot_html(html_path: str, output_path: str) -> tuple:
    """
    打开 file:// HTML，以 830px 视口 + 2x scale 截图输出 @2x 图。
    返回 (width, height, size_kb)。
    """
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

    img = Image.open(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ {os.path.basename(output_path)}: {img.size[0]}x{img.size[1]}px, {size_kb:.0f}KB")
    return img.size[0], img.size[1], size_kb


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python playwright-screenshot.py <html_path> <output_path>")
        sys.exit(1)
    screenshot_html(sys.argv[1], sys.argv[2])
