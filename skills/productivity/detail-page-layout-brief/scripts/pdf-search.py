#!/usr/bin/env python3
"""在 PDF 中搜索产品关键词，定位每个产品出现的页码。
用法: python3 pdf-search.py <pdf_path> <keyword1> [keyword2 ...]
"""
import fitz  # PyMuPDF
import sys

if len(sys.argv) < 3:
    print("用法: python3 pdf-search.py <pdf_path> <keyword1> [keyword2 ...]")
    sys.exit(1)

pdf_path = sys.argv[1]
keywords = sys.argv[2:]

doc = fitz.open(pdf_path)
print(f"PDF: {pdf_path} ({doc.page_count} 页)\n")

for pi in range(doc.page_count):
    page = doc[pi]
    text = page.get_text()
    for kw in keywords:
        if kw in text:
            lines = text.split('\n')
            for li, line in enumerate(lines):
                if kw in line:
                    print(f"p{pi+1} [{kw}] L{li}: {line.strip()[:200]}")

doc.close()
