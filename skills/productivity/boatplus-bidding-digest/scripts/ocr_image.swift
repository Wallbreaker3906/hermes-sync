import Vision
import AppKit
import Foundation

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
