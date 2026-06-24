import Vision
import CoreImage
import Foundation

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let img = CIImage(contentsOf: url) else {
    print("ERROR: cannot load image")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "en"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(ciImage: img, options: [:])
try handler.perform([request])

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
