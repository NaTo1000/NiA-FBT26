import Foundation
import Combine
import Security

// MARK: - AppSettings (ObservableObject for environment injection)

class AppSettings: ObservableObject {
    @Published var serverURL: String {
        didSet { UserDefaults.standard.set(serverURL, forKey: "server_url") }
    }
    @Published var serverPort: Int {
        didSet { UserDefaults.standard.set(serverPort, forKey: "server_port") }
    }
    @Published var bluetoothEnabled: Bool {
        didSet { UserDefaults.standard.set(bluetoothEnabled, forKey: "bluetooth_enabled") }
    }

    var huggingFaceAPIKey: String {
        get { KeychainHelper.read(key: "hf_api_key") ?? "" }
        set { KeychainHelper.save(key: "hf_api_key", value: newValue) }
    }

    var orchestratorBaseURL: String {
        "\(serverURL):\(serverPort)"
    }

    init() {
        self.serverURL = UserDefaults.standard.string(forKey: "server_url") ?? "http://localhost"
        self.serverPort = UserDefaults.standard.integer(forKey: "server_port") == 0
            ? 7000
            : UserDefaults.standard.integer(forKey: "server_port")
        self.bluetoothEnabled = UserDefaults.standard.object(forKey: "bluetooth_enabled") == nil
            ? true
            : UserDefaults.standard.bool(forKey: "bluetooth_enabled")
    }
}

// MARK: - Keychain Helper

enum KeychainHelper {
    static func save(key: String, value: String) {
        let data = Data(value.utf8)
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecValueData: data,
            kSecAttrAccessible: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    static func read(key: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}

// MARK: - APIManager

@MainActor
class APIManager: ObservableObject {
    static let shared = APIManager()

    private let session: URLSession
    private var settings: AppSettings?

    private init() {
        let config = URLSessionConfiguration.default
        // 30 s for initial request; AI model responses may take up to 120 s
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)
    }

    func configure(with settings: AppSettings) {
        self.settings = settings
    }

    // MARK: - Generic POST

    func post<T: Decodable>(endpoint: String, body: Encodable) async throws -> T {
        guard let settings = settings else { throw AppError.networkUnavailable }
        guard let url = URL(string: "\(settings.orchestratorBaseURL)/\(endpoint)") else {
            throw AppError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !settings.huggingFaceAPIKey.isEmpty {
            request.setValue("Bearer \(settings.huggingFaceAPIKey)",
                             forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AppError.networkUnavailable
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw AppError.serverError("HTTP \(httpResponse.statusCode): \(msg)")
        }
        do {
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
        } catch {
            throw AppError.decodingFailed(error.localizedDescription)
        }
    }

    // MARK: - FAP Builder

    func generateFAPCode(code: String) async throws -> AIResponse {
        let body = TaskRequest(task: code, model: "code_generation", parameters: nil)
        return try await post(endpoint: "api/fap/generate", body: body)
    }

    // MARK: - Firmware Builder

    func buildFirmware(fileURL: URL, targetDevice: String) async throws -> BuildResult {
        let body = TaskRequest(
            task: fileURL.lastPathComponent,
            model: "build_diagnostics",
            parameters: ["target": targetDevice]
        )
        return try await post(endpoint: "api/firmware/build", body: body)
    }

    func analyzeFirmware(fileURL: URL) async throws -> AIResponse {
        let body = TaskRequest(
            task: fileURL.lastPathComponent,
            model: "firmware_analysis",
            parameters: nil
        )
        return try await post(endpoint: "api/firmware/analyze", body: body)
    }

    // MARK: - AI Research

    func runResearchConference(topic: String, models: [String]) async throws -> [AIResponse] {
        struct ConferenceRequest: Encodable {
            let topic: String
            let models: [String]
        }
        let body = ConferenceRequest(topic: topic, models: models)
        return try await post(endpoint: "api/research/conference", body: body)
    }

    func queryModel(model: String, prompt: String) async throws -> AIResponse {
        let body = TaskRequest(task: prompt, model: model, parameters: nil)
        return try await post(endpoint: "api/ai/query", body: body)
    }
}
