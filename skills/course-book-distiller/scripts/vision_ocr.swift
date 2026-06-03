#!/usr/bin/env swift
import Foundation
import Vision
import AppKit

if CommandLine.arguments.count < 2 {
    fputs("usage: vision_ocr.swift IMAGE [IMAGE...]\n", stderr)
    exit(2)
}

func recognize(path: String) throws -> [[String: Any]] {
    let url = URL(fileURLWithPath: path)
    guard let image = NSImage(contentsOf: url) else {
        throw NSError(domain: "vision_ocr", code: 1, userInfo: [NSLocalizedDescriptionKey: "cannot open image: \(path)"])
    }
    guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw NSError(domain: "vision_ocr", code: 2, userInfo: [NSLocalizedDescriptionKey: "cannot create CGImage: \(path)"])
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    if #available(macOS 13.0, *) {
        request.revision = VNRecognizeTextRequestRevision3
    }
    if #available(macOS 11.0, *) {
        let supported = try request.supportedRecognitionLanguages()
        let preferred = ["zh-Hans", "zh-Hant", "en-US"].filter { supported.contains($0) }
        if !preferred.isEmpty {
            request.recognitionLanguages = preferred
        }
    }

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try handler.perform([request])

    let observations = request.results ?? []
    return observations.compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        return [
            "text": candidate.string,
            "confidence": candidate.confidence,
            "bbox": [box.minX, box.minY, box.width, box.height]
        ]
    }
}

var output: [[String: Any]] = []
for path in CommandLine.arguments.dropFirst() {
    do {
        output.append(["path": path, "lines": try recognize(path: path)])
    } catch {
        output.append(["path": path, "error": String(describing: error)])
    }
}

let data = try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
FileHandle.standardOutput.write(data)
FileHandle.standardOutput.write("\n".data(using: .utf8)!)
