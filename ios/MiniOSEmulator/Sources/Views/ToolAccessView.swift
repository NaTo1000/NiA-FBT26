import SwiftUI

/// A security tool available in MiniOS's ethical toolkit.
struct EthicalTool: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let command: String
    let icon: String
    var requiresTarget: Bool = true
}

/// SwiftUI view that provides a user-friendly interface to MiniOS's
/// built-in ethical cybersecurity toolkit (Nmap, Wireshark, etc.).
/// All tools are intended for authorized security testing only.
struct ToolAccessView: View {

    @StateObject private var core = EmulatorCore()
    @State private var selectedTool: EthicalTool? = nil
    @State private var targetInput: String = ""
    @State private var outputLog: String = ""
    @State private var isRunning: Bool = false

    private let tools: [EthicalTool] = [
        EthicalTool(
            name: "Nmap",
            description: "Network discovery and security auditing.",
            command: "nmap",
            icon: "network"
        ),
        EthicalTool(
            name: "Wireshark (tshark)",
            description: "Network protocol analyser (CLI mode).",
            command: "tshark -i eth0 -c 50",
            icon: "antenna.radiowaves.left.and.right",
            requiresTarget: false
        ),
        EthicalTool(
            name: "Ncat",
            description: "Versatile networking utility.",
            command: "ncat",
            icon: "cable.connector"
        ),
        EthicalTool(
            name: "OpenSSL",
            description: "TLS/SSL diagnostics and certificate inspection.",
            command: "openssl s_client -connect",
            icon: "lock.shield"
        ),
        EthicalTool(
            name: "Masscan",
            description: "High-speed TCP port scanner.",
            command: "masscan -p1-1024",
            icon: "magnifyingglass"
        ),
        EthicalTool(
            name: "Nikto",
            description: "Web server vulnerability scanner.",
            command: "nikto -h",
            icon: "globe"
        ),
        EthicalTool(
            name: "Aircrack-ng",
            description: "Wi-Fi security assessment suite.",
            command: "aircrack-ng",
            icon: "wifi"
        ),
        EthicalTool(
            name: "Flipper Zero Bridge",
            description: "Connect to the emulated Flipper Zero for signal testing.",
            command: "flipper-bridge --connect",
            icon: "flipphone",
            requiresTarget: false
        ),
    ]

    var body: some View {
        VStack(spacing: 0) {
            toolList
            if let tool = selectedTool {
                Divider()
                toolDetailPanel(for: tool)
            }
        }
        .navigationTitle("Ethical Toolkit")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color.black.ignoresSafeArea())
        .preferredColorScheme(.dark)
    }

    // MARK: - Tool List

    private var toolList: some View {
        List(tools) { tool in
            Button(action: { selectedTool = tool; outputLog = ""; targetInput = "" }) {
                HStack(spacing: 12) {
                    Image(systemName: tool.icon)
                        .font(.title3)
                        .foregroundColor(.green)
                        .frame(width: 28)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(tool.name)
                            .foregroundColor(.white)
                            .font(.body.weight(.semibold))
                        Text(tool.description)
                            .foregroundColor(.gray)
                            .font(.caption)
                    }

                    Spacer()

                    if selectedTool?.id == tool.id {
                        Image(systemName: "chevron.down")
                            .foregroundColor(.green)
                            .font(.caption)
                    }
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .listRowBackground(Color(white: 0.1))
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
    }

    // MARK: - Tool Detail Panel

    private func toolDetailPanel(for tool: EthicalTool) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(tool.name)
                .font(.headline)
                .foregroundColor(.white)

            if tool.requiresTarget {
                HStack {
                    TextField("Target (IP / hostname)", text: $targetInput)
                        .textFieldStyle(.roundedBorder)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                        .font(.system(.body, design: .monospaced))
                }
            }

            Button(action: { runTool(tool) }) {
                Label(isRunning ? "Running…" : "Run \(tool.name)", systemImage: "play.fill")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
            }
            .buttonStyle(.borderedProminent)
            .tint(.green)
            .disabled(isRunning || (tool.requiresTarget && targetInput.trimmingCharacters(in: .whitespaces).isEmpty))

            if !outputLog.isEmpty {
                ScrollView {
                    Text(outputLog)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(.green)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(6)
                }
                .frame(maxHeight: 160)
                .background(Color(white: 0.05))
                .cornerRadius(6)
            }
        }
        .padding()
        .background(Color(white: 0.08))
    }

    // MARK: - Actions

    private func runTool(_ tool: EthicalTool) {
        let target = targetInput.trimmingCharacters(in: .whitespaces)
        let fullCommand = tool.requiresTarget ? "\(tool.command) \(target)" : tool.command
        isRunning = true
        outputLog = "$ \(fullCommand)\n[Sending to MiniOS guest…]\n"
        core.sendCommand(fullCommand)

        // Simulate async output retrieval (real impl reads from virtio-console)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            outputLog += "[Output would appear here when MiniOS guest responds.]\n"
            isRunning = false
        }
    }
}

// MARK: - Preview

#if DEBUG
struct ToolAccessView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView { ToolAccessView() }
    }
}
#endif
