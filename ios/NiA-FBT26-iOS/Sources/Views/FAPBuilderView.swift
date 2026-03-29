import SwiftUI

struct FAPBuilderView: View {
    @EnvironmentObject private var settings: AppSettings
    @StateObject private var api = APIManager.shared

    @State private var codeInput: String = ""
    @State private var generatedCode: String = ""
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                // Code Input
                GroupBox(label: Label("Source Code / Description", systemImage: "doc.text")) {
                    TextEditor(text: $codeInput)
                        .frame(minHeight: 160)
                        .font(.system(.body, design: .monospaced))
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(Color.secondary.opacity(0.3), lineWidth: 1)
                        )
                }

                // Generate button
                Button(action: generateCode) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .tint(.white)
                    } else {
                        Label("Generate FAP Code", systemImage: "wand.and.stars")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(codeInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isLoading)

                // Error banner
                if let error = errorMessage {
                    Label(error, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                        .font(.footnote)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                // Generated code preview
                if !generatedCode.isEmpty {
                    GroupBox(label: Label("Generated Code", systemImage: "checkmark.seal.fill")) {
                        ScrollView {
                            Text(generatedCode)
                                .font(.system(.body, design: .monospaced))
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .textSelection(.enabled)
                        }
                        .frame(maxHeight: 260)
                    }
                    .transition(.move(edge: .bottom).combined(with: .opacity))

                    Button(action: copyCode) {
                        Label("Copy to Clipboard", systemImage: "doc.on.doc")
                    }
                    .buttonStyle(.bordered)
                }

                Spacer()
            }
            .padding()
            .navigationTitle("FAP Builder")
            .animation(.easeInOut, value: generatedCode)
        }
    }

    private func generateCode() {
        errorMessage = nil
        isLoading = true
        Task {
            defer { isLoading = false }
            do {
                api.configure(with: settings)
                let response = try await api.generateFAPCode(code: codeInput)
                generatedCode = response.result
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func copyCode() {
        UIPasteboard.general.string = generatedCode
    }
}

#Preview {
    FAPBuilderView()
        .environmentObject(AppSettings())
}
