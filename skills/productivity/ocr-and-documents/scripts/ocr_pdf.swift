import Foundation
import PDFKit
import Vision
import AppKit

// Usage: swiftc ocr_pdf.swift -o ocr_pdf && ./ocr_pdf <pdf_path> <page1> <page2> ...
// Default: reads /tmp/input.pdf, pages 18 and 19

let pdfPath = CommandLine.arguments.count > 1 
    ? CommandLine.arguments[1] 
    : "/private/tmp/倍豪船舶企业宣传册2024.pdf"

let pageNums: [Int]
if CommandLine.arguments.count > 2 {
    pageNums = CommandLine.arguments.dropFirst(2).compactMap { Int($0) }
} else {
    pageNums = [18, 19]
}

guard let pdfDoc = PDFDocument(url: URL(fileURLWithPath: pdfPath)) else {
    print("Failed to open PDF: \(pdfPath)")
    exit(1)
}

let scale: CGFloat = 2.5

for pn in pageNums {
    guard let page = pdfDoc.page(at: pn - 1) else {
        print("Page \(pn) not found")
        continue
    }
    
    let pageRect = page.bounds(for: .mediaBox)
    let imgSize = CGSize(width: pageRect.width * scale, height: pageRect.height * scale)
    
    let img = NSImage(size: imgSize)
    img.lockFocus()
    if let ctx = NSGraphicsContext.current?.cgContext {
        ctx.setFillColor(NSColor.white.cgColor)
        ctx.fill(CGRect(origin: .zero, size: imgSize))
        ctx.scaleBy(x: scale, y: scale)
        page.draw(with: .mediaBox, to: ctx)
    }
    img.unlockFocus()
    
    guard let tiff = img.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let pngData = bitmap.representation(using: .png, properties: [:]),
          let cgImage = bitmap.cgImage else {
        print("Failed to convert page \(pn)")
        continue
    }
    
    let outPath = "/tmp/bh_p\(pn).png"
    try! pngData.write(to: URL(fileURLWithPath: outPath))
    
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en"]
    
    let handler = VNImageRequestHandler(cgImage: cgImage)
    try! handler.perform([request])
    
    print("\n===== PAGE \(pn) =====")
    if let observations = request.results {
        for obs in observations {
            if let text = obs.topCandidates(1).first?.string {
                print(text)
            }
        }
    } else {
        print("(no text found)")
    }
}
