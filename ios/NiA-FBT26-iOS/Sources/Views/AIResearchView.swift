import SwiftUI

struct AIResearchView: View {
    @EnvironmentObject private var settings: AppSettings
    @StateObject private var api = APIManager.shared

    @State private var topic: String = ""
    @State private var selectedModels: Set<String> = ["code_generation", "firmware_analysis"]
    @State private var responses: [AIResponse] = []
    @State private var isConferencing: Bool = false
    @State private var errorMessage: String?

    private let availableModels: [(id: String, label: String, icon: String)] = [
        ("code_generation",   "Code Generation (DeepSeek)",   "chevron.left.forwardslash.chevron.right"),
        ("code_review",       "Code Review (CodeLlama)",       "checkmark.seal"),
        ("nl_to_cli",         "NL→CLI (Llama 70B)",            "terminal"),
        ("docs_generator",    "Docs Generator (Mistral)",      "doc.text"),
        ("signal_classifier", "Signal Classifier (ONNX)",      "waveform.path.ecg"),
        ("firmware_analysis", "Firmware Analysis (StarCoder2)","cpu"),
        ("github_ranker",     "GitHub Ranker (BGE)",           "star"),
        ("log_analyzer",      "Log Analyzer (Phi-3)",          "list.bullet.rectangle"),
        ("build_diagnostics", "Build Diagnostics (DeepSeek)",  "hammer"),
        ("protocol_parser",   "Protocol Parser (Llama 8B)",    "antenna.radiowaves.left.and.right"),
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Form {
                    // Topic input
                    Section(header: Text("Research Topic")) {
                        TextField("e.g. Sub-GHz replay attack detection", text: $topic)
                            .autocorrectionDisabled()
                    }

                    // Model selection
                    Section(header: Text("Select Models (\(selectedModels.count) selected)")) {
                        ForEach(availableModels, id: \.id) { model in
                            Toggle(isOn: Binding(
                                get: { selectedModels.contains(model.id) },
                                set: { isOn in
                                    if isOn { selectedModels.insert(model.id) }
                                    else { selectedModels.remove(model.id) }
                                }
                            )) {
                                Label(model.label, systemImage: model.icon)
                                    .font(.subheadline)
                            }
                        }
                    }

                    // Conference button
                    Section {
                        Button(action: runConference) {
                            HStack {
                                Spacer()
                                if isConferencing {
                                    ProgressView()
                                        .progressViewStyle(.circular)
                                    Text("Conferencing…")
                                        .padding(.leading, 8)
                                } else {
                                    Label("Start Conference", systemImage: "brain.head.profile")
                                        .fontWeight(.semibold)
                                }
                                Spacer()
                            }
                        }
                        .disabled(topic.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                                  || selectedModels.isEmpty
                                  || isConferencing)
                    }
                }
                .frame(maxHeight: responses.isEmpty ? .infinity : 340)

                // Error
                if let error = errorMessage {
                    Label(error, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                        .font(.footnote)
                        .padding(.horizontal)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                // Results
                if !responses.isEmpty {
                    Divider()
                    Text("Conference Results")
                        .font(.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding([.horizontal, .top])

                    List(responses) { response in
                        ResponseCard(response: response)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("AI Research")
            .animation(.easeInOut, value: responses.count)
        }
    }

    private func runConference() {
        errorMessage = nil
        responses = []
        isConferencing = true
        Task {
            defer { isConferencing = false }
            do {
                api.configure(with: settings)
                responses = try await api.runResearchConference(
                    topic: topic,
                    models: Array(selectedModels)
                )
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

// MARK: - Response Card

struct ResponseCard: View {
    let response: AIResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain")
                    .foregroundStyle(.purple)
                Text(response.model)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Spacer()
                Text(response.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            Text(response.result)
                .font(.body)
                .textSelection(.enabled)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    AIResearchView()
        .environmentObject(AppSettings())
}
