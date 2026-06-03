#!/usr/bin/env swift
import Foundation
import Vision

struct OCRRecord: Codable {
    let path: String
    let text: String
    let lines: [String]
}

func jsonLine(_ record: OCRRecord) -> String {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    if let data = try? encoder.encode(record), let text = String(data: data, encoding: .utf8) {
        return text
    }
    return "{\"path\":\"\(record.path)\",\"text\":\"\",\"lines\":[]}"
}

let paths = CommandLine.arguments.dropFirst()
if paths.isEmpty {
    fputs("Usage: ocr_images_vision.swift <image> [image ...]\n", stderr)
    exit(2)
}

for path in paths {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    let preferredLanguages = ["zh-Hans", "zh-Hant", "en-US"]
    if let supported = try? request.supportedRecognitionLanguages() {
        let selected = preferredLanguages.filter { supported.contains($0) }
        if !selected.isEmpty {
            request.recognitionLanguages = selected
        }
    }

    let url = URL(fileURLWithPath: String(path))
    let handler = VNImageRequestHandler(url: url, options: [:])
    do {
        try handler.perform([request])
        let lines = (request.results ?? [])
            .compactMap { $0.topCandidates(1).first?.string.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        print(jsonLine(OCRRecord(path: String(path), text: lines.joined(separator: "\n"), lines: lines)))
    } catch {
        print(jsonLine(OCRRecord(path: String(path), text: "", lines: [])))
    }
}
