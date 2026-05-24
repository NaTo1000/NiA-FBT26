import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var settings: AppSettings
    @State private var apiKeyInput: String = ""
    @State private var showAPIKey: Bool = false
    @State private var savedBanner: Bool = false

    var body: some View {
        NavigationStack {
            Form {
                // Server configuration
                Section(header: Text("Orchestration Server")) {
                    HStack {
                        Text("Server URL")
                        Spacer()
                        TextField("http://localhost", text: $settings.serverURL)
                            .multilineTextAlignment(.trailing)
                            .keyboardType(.URL)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                    }

                    HStack {
                        Text("Port")
                        Spacer()
                        TextField("7000", value: $settings.serverPort, format: .number)
                            .multilineTextAlignment(.trailing)
                            .keyboardType(.numberPad)
                            .frame(width: 80)
                    }

                    HStack {
                        Text("Full URL")
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(settings.orchestratorBaseURL)
                            .foregroundStyle(.secondary)
                            .font(.caption)
                    }
                }

                // HuggingFace API Key (secure storage)
                Section(
                    header: Text("HuggingFace API Key"),
                    footer: Text("Stored securely in the device Keychain. Never sent in plain text.")
                ) {
                    HStack {
                        if showAPIKey {
                            TextField("hf_...", text: $apiKeyInput)
                                .autocorrectionDisabled()
                                .textInputAutocapitalization(.never)
                        } else {
                            SecureField("hf_...", text: $apiKeyInput)
                        }
                        Button(action: { showAPIKey.toggle() }) {
                            Image(systemName: showAPIKey ? "eye.slash" : "eye")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }

                    Button("Save API Key") {
                        settings.huggingFaceAPIKey = apiKeyInput
                        savedBanner = true
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            savedBanner = false
                        }
                    }
                    .disabled(apiKeyInput.isEmpty)

                    if savedBanner {
                        Label("Saved to Keychain", systemImage: "checkmark.shield.fill")
                            .foregroundStyle(.green)
                            .font(.footnote)
                    }
                }

                // Bluetooth
                Section(header: Text("Flipper Zero Connectivity")) {
                    Toggle("Bluetooth Enabled", isOn: $settings.bluetoothEnabled)
                    Text("Uses CoreBluetooth to connect directly to Flipper Zero for firmware flashing and real-time interaction.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                // Info section
                Section(header: Text("About")) {
                    LabeledContent("App Version", value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0")
                    LabeledContent("iOS", value: UIDevice.current.systemVersion)
                    LabeledContent("Min iOS Required", value: "15.0")
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                // Load existing key from Keychain (masked)
                let stored = settings.huggingFaceAPIKey
                if !stored.isEmpty {
                    apiKeyInput = stored
                }
            }
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppSettings())
}
