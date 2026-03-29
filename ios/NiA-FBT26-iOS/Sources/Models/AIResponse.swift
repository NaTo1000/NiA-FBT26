import Foundation

struct AIResponse: Codable, Identifiable {
    let id: UUID
    let model: String
    let result: String
    let timestamp: Date

    init(id: UUID = UUID(), model: String, result: String, timestamp: Date = Date()) {
        self.id = id
        self.model = model
        self.result = result
        self.timestamp = timestamp
    }

    enum CodingKeys: String, CodingKey {
        case id, model, result, timestamp
    }
}

struct TaskRequest: Codable {
    let task: String
    let model: String?
    let parameters: [String: String]?
}

struct BuildResult: Codable, Identifiable {
    let id: UUID
    let status: String
    let output: String
    let downloadURL: String?

    init(id: UUID = UUID(), status: String, output: String, downloadURL: String? = nil) {
        self.id = id
        self.status = status
        self.output = output
        self.downloadURL = downloadURL
    }

    enum CodingKeys: String, CodingKey {
        case id, status, output
        case downloadURL = "download_url"
    }
}

struct FileModel: Identifiable {
    let id: UUID
    let name: String
    let url: URL
    let size: Int64

    init(id: UUID = UUID(), name: String, url: URL, size: Int64 = 0) {
        self.id = id
        self.name = name
        self.url = url
        self.size = size
    }
}

enum AppError: LocalizedError {
    case networkUnavailable
    case serverError(String)
    case decodingFailed(String)
    case invalidURL

    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "Network unavailable. Check server connection."
        case .serverError(let msg):
            return "Server error: \(msg)"
        case .decodingFailed(let msg):
            return "Failed to decode response: \(msg)"
        case .invalidURL:
            return "Invalid server URL in settings."
        }
    }
}
