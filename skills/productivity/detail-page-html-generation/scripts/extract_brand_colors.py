"""
从供应商 PDF 宣传册提取品牌色系。
用法: python3 extract_brand_colors.py <pdf_path>
输出: 品牌主色、深色辅助色、浅底色（hex 值）
"""
import fitz
import sys
from collections import Counter

pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)

print(f"PDF: {pdf_path} ({doc.page_count} 页)")
print()

for page_num in range(min(8, doc.page_count)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=50)
    img_data = pix.samples
    w, h = pix.width, pix.height
    
    # 采样页面上半部（品牌色通常在 header/hero 区）
    colors = Counter()
    step = max(1, min(w, h) // 25)
    for y in range(0, min(h//3, h), step):
        for x in range(0, w, step):
            pos = (y * w + x) * pix.n
            r, g, b = img_data[pos], img_data[pos+1], img_data[pos+2]
            # 过滤极值（纯白/纯黑通常是背景/文字）
            if (r, g, b) in [(255,255,255), (0,0,0)]:
                continue
            colors[(r, g, b)] += 1
    
    top_colors = colors.most_common(5)
    print(f"--- 第{page_num+1}页 ---")
    for (r, g, b), count in top_colors:
        hex_c = f"#{r:02x}{g:02x}{b:02x}"
        bar = "█" * min(count, 40)
        print(f"  {hex_c}  rgb({r},{g},{b})  {bar}")
    
    # 同时输出文字（用于定位品牌相关内容）
    text = page.get_text().strip()[:200]
    if text:
        print(f"  文字: {text[:120]}...")
    print()

doc.close()
