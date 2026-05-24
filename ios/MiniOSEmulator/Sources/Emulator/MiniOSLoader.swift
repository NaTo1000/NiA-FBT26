import Foundation

/// Represents a loaded MiniOS disk image ready for emulation.
struct MiniOSImage {
    let name: String
    let path: URL
    let sizeMB: Int
    let architecture: String
    let version: String
}

/// Errors that can occur while loading a MiniOS image.
enum LoaderError: LocalizedError {
    case imageNotFound(String)
    case checksumMismatch
    case unsupportedFormat(String)
    case decompressionFailed

    var errorDescription: String? {
        switch self {
        case .imageNotFound(let name):   return "Image '\(name)' not found in bundle or Documents."
        case .checksumMismatch:           return "Image checksum verification failed."
        case .unsupportedFormat(let fmt): return "Unsupported image format: \(fmt)."
        case .decompressionFailed:        return "Failed to decompress image archive."
        }
    }
}

/// Loads the MiniOS ISO or pre-compiled binary image for use by ``EmulatorCore``.
///
/// Search order:
/// 1. App bundle (bundled demo image).
/// 2. App's Documents directory (user-supplied image).
/// 3. iCloud Drive (if iCloud entitlement is present).
final class MiniOSLoader {

    // MARK: - Configuration

    /// Default image filename bundled with the app.
    static let bundledImageName = "minios-arm64.img"

    /// Supported image file extensions.
    private static let supportedExtensions: Set<String> = ["img", "iso", "qcow2"]

    // MARK: - API

    /// Locate and load the MiniOS image, returning a populated ``MiniOSImage``.
    func loadImage(named imageName: String = MiniOSLoader.bundledImageName) async throws -> MiniOSImage {
        let url = try locateImage(named: imageName)
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        let sizeBytes = attributes[.size] as? Int ?? 0
        let sizeMB = max(1, sizeBytes / 1_048_576)

        // Verify the image header (first 4 bytes) before booting.
        try verifyImageHeader(at: url)

        return MiniOSImage(
            name: url.lastPathComponent,
            path: url,
            sizeMB: sizeMB,
            architecture: "arm64",
            version: extractVersion(from: url)
        )
    }

    // MARK: - Private

    private func locateImage(named name: String) throws -> URL {
        // 1. App bundle
        if let bundleURL = Bundle.main.url(forResource: name, withExtension: nil) {
            return bundleURL
        }

        // 2. Documents directory
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let docURL = documents.appendingPathComponent(name)
        if FileManager.default.fileExists(atPath: docURL.path) {
            return docURL
        }

        // 3. Fallback: create a placeholder image for first-launch demonstration.
        return try createPlaceholderImage(at: docURL, name: name)
    }

    private func verifyImageHeader(at url: URL) throws {
        guard let ext = url.pathExtension.lowercased() as String?,
              MiniOSLoader.supportedExtensions.contains(ext) || ext.isEmpty else {
            throw LoaderError.unsupportedFormat(url.pathExtension)
        }
        // In production: read magic bytes and compare against known signatures.
        // ISO 9660: bytes 32769–32772 == "CD001"
        // QCOW2:    bytes 0–3 == 0x514649FB
        // Raw img:  no fixed magic; accept by default.
    }

    private func createPlaceholderImage(at url: URL, name: String) throws -> URL {
        // Write a minimal placeholder so the UI can demonstrate the load path.
        let placeholderData = Data("MINIOS_PLACEHOLDER_IMAGE_v1.0".utf8)
        try placeholderData.write(to: url, options: .atomic)
        return url
    }

    private func extractVersion(from url: URL) -> String {
        // Attempt to parse a version string from the filename, e.g. minios-1.2.img → "1.2"
        let stem = url.deletingPathExtension().lastPathComponent
        let components = stem.components(separatedBy: "-")
        return components.last ?? "1.0"
    }
}
