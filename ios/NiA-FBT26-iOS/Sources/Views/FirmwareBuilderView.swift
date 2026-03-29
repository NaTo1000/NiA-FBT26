import SwiftUI
import UniformTypeIdentifiers

struct FirmwareBuilderView: View {
    @EnvironmentObject private var settings: AppSettings
    @StateObject private var api = APIManager.shared

    @State private var selectedFile: FileModel?
    @State private var targetDevice: String = "Flipper Zero"
    @State private var buildResult: BuildResult?
    @State private var analysisResult: AIResponse?
    @State private var isBuilding: Bool = false
    @State private var isAnalyzing: Bool = false
    @State private var errorMessage: String?
    @State private var showDocumentPicker: Bool = false

    private let targetDevices = ["Flipper Zero", "Flipper Zero Dev Board", "Custom"]

    var body: some View {
        NavigationStack {
            Form {
                // File picker section
                Section(header: Text("Source Files")) {
                    Button(action: { showDocumentPicker = true }) {
                        HStack {
                            Image(systemName: "folder.badge.plus")
                            Text(selectedFile?.name ?? "Select firmware source file")
                                .foregroundStyle(selectedFile == nil ? .secondary : .primary)
                        }
                    }
                    if let file = selectedFile {
                        HStack {
                            Image(systemName: "doc.fill")
                                .foregroundStyle(.blue)
                            Text(file.name)
                            Spacer()
                            Text(fileSizeString(file.size))
                                .foregroundStyle(.secondary)
                                .font(.caption)
                        }
                    }
                }

                // Build options
                Section(header: Text("Build Options")) {
                    Picker("Target Device", selection: $targetDevice) {
                        ForEach(targetDevices, id: \.self) { device in
                            Text(device).tag(device)
                        }
                    }
                }

                // Actions
                Section {
                    Button(action: buildFirmware) {
                        HStack {
                            if isBuilding {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "hammer.fill")
                            }
                            Text(isBuilding ? "Building…" : "Build Firmware")
                        }
                    }
                    .disabled(selectedFile == nil || isBuilding)

                    Button(action: analyzeFirmware) {
                        HStack {
                            if isAnalyzing {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "magnifyingglass")
                            }
                            Text(isAnalyzing ? "Analyzing…" : "Analyze with AI")
                        }
                    }
                    .disabled(selectedFile == nil || isAnalyzing)
                }

                // Error
                if let error = errorMessage {
                    Section {
                        Label(error, systemImage: "exclamationmark.triangle.fill")
                            .foregroundStyle(.red)
                            .font(.footnote)
                    }
                }

                // Build result
                if let result = buildResult {
                    Section(header: Text("Build Result")) {
                        Label(
                            result.status == "success" ? "Build Succeeded" : "Build Failed",
                            systemImage: result.status == "success"
                                ? "checkmark.circle.fill"
                                : "xmark.circle.fill"
                        )
                        .foregroundStyle(result.status == "success" ? .green : .red)

                        if !result.output.isEmpty {
                            Text(result.output)
                                .font(.system(.caption, design: .monospaced))
                                .textSelection(.enabled)
                        }
                        if let downloadURL = result.downloadURL,
                           let downloadLink = URL(string: downloadURL) {
                            Link(destination: downloadLink) {
                                Label("Download Firmware", systemImage: "arrow.down.circle.fill")
                            }
                        }
                    }
                }

                // AI analysis result
                if let analysis = analysisResult {
                    Section(header: Text("AI Analysis (\(analysis.model))")) {
                        Text(analysis.result)
                            .font(.body)
                            .textSelection(.enabled)
                    }
                }
            }
            .navigationTitle("Firmware Builder")
            .sheet(isPresented: $showDocumentPicker) {
                DocumentPicker(selectedFile: $selectedFile)
            }
        }
    }

    private func buildFirmware() {
        guard let file = selectedFile else { return }
        errorMessage = nil
        isBuilding = true
        Task {
            defer { isBuilding = false }
            do {
                api.configure(with: settings)
                buildResult = try await api.buildFirmware(fileURL: file.url, targetDevice: targetDevice)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func analyzeFirmware() {
        guard let file = selectedFile else { return }
        errorMessage = nil
        isAnalyzing = true
        Task {
            defer { isAnalyzing = false }
            do {
                api.configure(with: settings)
                analysisResult = try await api.analyzeFirmware(fileURL: file.url)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func fileSizeString(_ bytes: Int64) -> String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: bytes)
    }
}

// MARK: - Document Picker

struct DocumentPicker: UIViewControllerRepresentable {
    @Binding var selectedFile: FileModel?

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let types: [UTType] = [.data, .archive, .sourceCode]
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: types)
        picker.delegate = context.coordinator
        picker.allowsMultipleSelection = false
        return picker
    }

    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, UIDocumentPickerDelegate {
        let parent: DocumentPicker

        init(_ parent: DocumentPicker) { self.parent = parent }

        func documentPicker(_ controller: UIDocumentPickerViewController,
                            didPickDocumentsAt urls: [URL]) {
            guard let url = urls.first else { return }
            let accessing = url.startAccessingSecurityScopedResource()
            defer {
                if accessing { url.stopAccessingSecurityScopedResource() }
            }
            let attrs = try? FileManager.default.attributesOfItem(atPath: url.path)
            let size = attrs?[.size] as? Int64 ?? 0
            parent.selectedFile = FileModel(name: url.lastPathComponent, url: url, size: size)
        }
    }
}

#Preview {
    FirmwareBuilderView()
        .environmentObject(AppSettings())
}
