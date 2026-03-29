import XCTest
@testable import NiAFBT26iOS

// MARK: - AppSettings Tests

final class AppSettingsTests: XCTestCase {
    func testDefaultServerURL() {
        let settings = AppSettings()
        XCTAssertFalse(settings.serverURL.isEmpty, "Server URL should not be empty by default")
    }

    func testDefaultServerPort() {
        let settings = AppSettings()
        XCTAssertEqual(settings.serverPort, 7000, "Default port should be 7000")
    }

    func testOrchestratorBaseURL() {
        let settings = AppSettings()
        settings.serverURL = "http://192.168.1.10"
        settings.serverPort = 7000
        XCTAssertEqual(settings.orchestratorBaseURL, "http://192.168.1.10:7000")
    }

    func testBluetoothEnabledByDefault() {
        let settings = AppSettings()
        XCTAssertTrue(settings.bluetoothEnabled, "Bluetooth should be enabled by default")
    }
}

// MARK: - Keychain Tests

final class KeychainHelperTests: XCTestCase {
    private let testKey = "unit_test_api_key_\(UUID().uuidString)"

    override func tearDown() {
        super.tearDown()
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: testKey
        ]
        SecItemDelete(query as CFDictionary)
    }
    func testSaveAndRead() {
        KeychainHelper.save(key: testKey, value: "test_value_123")
        let value = KeychainHelper.read(key: testKey)
        XCTAssertEqual(value, "test_value_123")
    }

    func testOverwrite() {
        KeychainHelper.save(key: testKey, value: "first_value")
        KeychainHelper.save(key: testKey, value: "second_value")
        let value = KeychainHelper.read(key: testKey)
        XCTAssertEqual(value, "second_value")
    }

    func testReadMissingKey() {
        let value = KeychainHelper.read(key: "nonexistent_key_\(UUID().uuidString)")
        XCTAssertNil(value)
    }
}

// MARK: - AppError Tests

final class AppErrorTests: XCTestCase {
    func testNetworkUnavailableMessage() {
        let error = AppError.networkUnavailable
        XCTAssertNotNil(error.errorDescription)
        XCTAssertTrue(error.errorDescription!.lowercased().contains("network"))
    }

    func testServerErrorMessage() {
        let error = AppError.serverError("Internal Server Error")
        XCTAssertTrue(error.errorDescription!.contains("Internal Server Error"))
    }

    func testDecodingFailedMessage() {
        let error = AppError.decodingFailed("keyNotFound")
        XCTAssertTrue(error.errorDescription!.contains("keyNotFound"))
    }

    func testInvalidURLMessage() {
        let error = AppError.invalidURL
        XCTAssertNotNil(error.errorDescription)
    }
}

// MARK: - AIResponse Model Tests

final class AIResponseModelTests: XCTestCase {
    func testInitDefaults() {
        let response = AIResponse(model: "code_generation", result: "print('hello')")
        XCTAssertFalse(response.id.uuidString.isEmpty)
        XCTAssertEqual(response.model, "code_generation")
        XCTAssertEqual(response.result, "print('hello')")
    }

    func testJSONRoundTrip() throws {
        let original = AIResponse(model: "firmware_analysis", result: "No issues found.")
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(original)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decoded = try decoder.decode(AIResponse.self, from: data)
        XCTAssertEqual(decoded.id, original.id)
        XCTAssertEqual(decoded.model, original.model)
        XCTAssertEqual(decoded.result, original.result)
    }
}

// MARK: - BuildResult Model Tests

final class BuildResultModelTests: XCTestCase {
    func testSuccessResult() {
        let result = BuildResult(status: "success", output: "Build OK", downloadURL: "http://localhost:7000/downloads/fw.bin")
        XCTAssertEqual(result.status, "success")
        XCTAssertNotNil(result.downloadURL)
    }

    func testFailureResult() {
        let result = BuildResult(status: "error", output: "Compilation failed: undefined reference")
        XCTAssertEqual(result.status, "error")
        XCTAssertNil(result.downloadURL)
    }

    func testJSONRoundTrip() throws {
        let original = BuildResult(status: "success", output: "OK", downloadURL: "http://example.com/fw")
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(BuildResult.self, from: data)
        XCTAssertEqual(decoded.status, original.status)
        XCTAssertEqual(decoded.downloadURL, original.downloadURL)
    }
}

// MARK: - TaskRequest Tests

final class TaskRequestTests: XCTestCase {
    func testEncoding() throws {
        let req = TaskRequest(task: "Generate FAP", model: "code_generation", parameters: ["lang": "C"])
        let data = try JSONEncoder().encode(req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(json?["task"] as? String, "Generate FAP")
        XCTAssertEqual(json?["model"] as? String, "code_generation")
        let params = json?["parameters"] as? [String: String]
        XCTAssertEqual(params?["lang"], "C")
    }

    func testEncodingWithNilModel() throws {
        let req = TaskRequest(task: "some task", model: nil, parameters: nil)
        let data = try JSONEncoder().encode(req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertNotNil(json?["task"])
    }
}
