import Vision
import AppKit
import Foundation

/// OCR a standalone image (PNG/JPG/etc.) using macOS Vision framework.
/// Unlike the PDF variant, this operates on a single image file directly.
///
/// Compile: swiftc ocr_image.swift -o ocr_image
/// Usage:   ./ocr_image <image_path>
///
/// Supports Chinese + English recognition. No external dependencies needed
/// (uses built-in macOS frameworks only).

let args = CommandLine.arguments
guard args.count >= 2 else {
    print("Usage: ocr_image <image_path>")
    exit(1)
}

let imagePath = args[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERROR: Cannot load image \(imagePath)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "en"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
    guard let observations = request.results else {
        print("No text found")
        exit(0)
    }
    for obs in observations {
        if let top = obs.topCandidates(1).first {
            print(top.string)
        }
    }
} catch {
    print("ERROR: \(error.localizedDescription)")
    exit(1)
}
