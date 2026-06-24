# Swift PDFKit + Vision OCR (macOS)

Reliable OCR for scanned/image-based Chinese PDFs on macOS. Use when pymupdf times out, textutil fails ("Text encoding Unicode isn't applicable"), or the PDF contains only embedded images without text layers.

## Why This Works

- **PDFKit** renders any PDF page as CGImage — handles scanned docs, complex fonts, and encrypted PDFs that pymupdf chokes on
- **Vision** (VNRecognizeTextRequest) performs on-device OCR with `recognitionLanguages: ["zh-Hans", "en"]` — no network, no models to download
- Both frameworks are built into macOS — zero install, just compile once (~60s first time, seconds afterward)

## Usage

Compile once:
```bash
swiftc /path/to/ocr.swift -o /tmp/ocr
```

Run (extracts + OCRs specific pages):
```bash
/tmp/ocr
```

Outputs PNG images and OCR'd text for each target page.

## Key Source Code Pattern

```swift
import PDFKit
import Vision

// Render PDF page to NSImage via PDFPage.draw(with:to:)
let page = pdfDoc.page(at: pageIndex)
let img = NSImage(size: ...)
img.lockFocus()
page.draw(with: .mediaBox, to: ctx)
img.unlockFocus()

// OCR with Vision
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]
let handler = VNImageRequestHandler(cgImage: cgImage)
try handler.perform([request])
```

## TCC Sandbox Bypass

When macOS TCC blocks direct file access to Desktop/Documents:
- Copy to `/tmp` via Finder: `osascript -e 'tell app "Finder" to duplicate src to folder "/tmp"'`
- Verify with `stat` (works when `ls` is blocked)
- Search with `mdfind` (Spotlight) when `find` is blocked
