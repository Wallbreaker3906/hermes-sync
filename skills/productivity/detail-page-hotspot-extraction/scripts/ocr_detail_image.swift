import Vision
import CoreImage
import Foundation

guard CommandLine.arguments.count >= 2 else {
    print("Usage: ocr_detail_image <image_path>")
    exit(1)
}

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let img = CIImage(contentsOf: url) else {
    print("ERROR: cannot load image at \(path)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "en"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(ciImage: img, options: [:])
do {
    try handler.perform([request])
} catch {
    print("ERROR: \(error)")
    exit(1)
}

guard let observations = request.results else {
    print("NO RESULTS")
    exit(0)
}

for obs in observations {
    guard let topCandidate = obs.topCandidates(1).first else { continue }
    let text = topCandidate.string
    let bb = obs.boundingBox
    let conf = topCandidate.confidence
    
    print("TEXT: \(text)")
    print("BBOX: \(bb.origin.x),\(bb.origin.y),\(bb.size.width),\(bb.size.height)")
    print("CONF: \(conf)")
    print("---")
}
