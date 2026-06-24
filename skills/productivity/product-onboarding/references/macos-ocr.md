# macOS Image OCR (Swift + Vision)

Use when you need to extract Chinese/English text from images on macOS without installing external tools (Tesseract, Homebrew, etc.).

## Setup (one-time)

```bash
cat > /tmp/ocr.swift <<'EOF'
import Vision
import AppKit
import Foundation
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
let cgImg = img.cgImage(forProposedRect: nil, context: nil, hints: nil)!
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "en"]
try VNImageRequestHandler(cgImage: cgImg).perform([req])
for obs in (req.results ?? []) {
    if let top = obs.topCandidates(1).first { print(top.string) }
}
EOF
swiftc -o /tmp/ocr /tmp/ocr.swift
```

**First compilation is slow (30-60s)** — the Swift compiler needs to process the Vision/AppKit frameworks. After compilation, the binary at `/tmp/ocr` runs in ~2 seconds.

**Caveat**: `/tmp/` is cleared on system reboot. If the binary is missing, recompile with the commands above.

## Usage

```bash
# ⚠️ ALWAYS resize first — large images cause Vision to timeout (30s+)
sips -Z 1024 input.png --out /tmp/ocr_input.png

# Run OCR (binary at /tmp/ocr, ~2s runtime)
/tmp/ocr /tmp/ocr_input.png
```

**Why resize**: The Swift Vision framework's performance scales with image dimensions. A full-resolution screenshot or scanned page can take 30+ seconds and hit command timeouts. Resizing to 1024px on the long edge via `sips` (built into macOS, no install needed) reduces runtime to 1-2 seconds with negligible accuracy loss.

## When to Use

- Image-based PDF pages where pymupdf `get_text()` returns garbled output
- Screenshots containing product specs, tables, or diagrams
- Any image where Chinese text needs extraction and no external OCR tool is installed

## Pitfalls

- Vision framework OCR quality is good but not perfect — Chinese characters with similar shapes may be misrecognized
- Background noise or decorative fonts reduce accuracy
- For tabular data, the output is line-by-line; column alignment must be reconstructed manually
- The Swift compiler needs full disk access (no sandbox restrictions)
