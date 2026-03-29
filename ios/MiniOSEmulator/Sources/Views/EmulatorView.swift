import SwiftUI
import Combine

/// Root view that hosts the MiniOS emulator with a virtual screen,
/// an on-screen keyboard, and status indicators.
struct EmulatorView: View {

    @StateObject private var core = EmulatorCore()
    @State private var commandInput: String = ""
    @State private var showKeyboard: Bool = false
    @FocusState private var inputFocused: Bool

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                statusBar
                Divider()
                virtualScreen
                Divider()
                consoleInputBar
            }
            .navigationTitle("MiniOS Emulator")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { toolbarItems }
            .background(Color.black)
        }
        .navigationViewStyle(.stack)
        .preferredColorScheme(.dark)
    }

    // MARK: - Status Bar

    private var statusBar: some View {
        HStack(spacing: 16) {
            statusIndicator
            Spacer()
            metricsBadge(label: "CPU", value: String(format: "%.0f%%", core.cpuUsage))
            metricsBadge(label: "RAM", value: "\(core.memoryUsageMB) MB")
        }
        .padding(.horizontal)
        .padding(.vertical, 6)
        .background(Color(white: 0.1))
    }

    private var statusIndicator: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(stateColor)
                .frame(width: 8, height: 8)
            Text(stateLabel)
                .font(.caption.weight(.semibold))
                .foregroundColor(.white)
        }
    }

    private func metricsBadge(label: String, value: String) -> some View {
        VStack(spacing: 1) {
            Text(label)
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(.gray)
            Text(value)
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundColor(.green)
        }
    }

    // MARK: - Virtual Screen

    private var virtualScreen: some View {
        ScrollViewReader { proxy in
            ScrollView {
                Text(core.consoleOutput.isEmpty ? "Waiting for MiniOS…" : core.consoleOutput)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(.green)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
                    .id("bottom")
            }
            .onChange(of: core.consoleOutput) { _ in
                withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
            }
        }
        .background(Color.black)
    }

    // MARK: - Console Input

    private var consoleInputBar: some View {
        HStack(spacing: 8) {
            Text("$")
                .font(.system(size: 14, design: .monospaced))
                .foregroundColor(.green)

            TextField("Enter command…", text: $commandInput)
                .font(.system(size: 14, design: .monospaced))
                .foregroundColor(.white)
                .accentColor(.green)
                .focused($inputFocused)
                .onSubmit { submitCommand() }
                .submitLabel(.go)

            Button(action: submitCommand) {
                Image(systemName: "arrow.up.circle.fill")
                    .foregroundColor(.green)
                    .font(.title3)
            }
            .disabled(commandInput.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(white: 0.08))
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarItems: some ToolbarContent {
        ToolbarItemGroup(placement: .navigationBarLeading) {
            NavigationLink(destination: ToolAccessView()) {
                Label("Tools", systemImage: "wrench.and.screwdriver")
            }
        }
        ToolbarItemGroup(placement: .navigationBarTrailing) {
            NavigationLink(destination: AIInterfaceView()) {
                Label("AI", systemImage: "brain")
            }
            bootButton
        }
    }

    private var bootButton: some View {
        Button(action: handleBootTap) {
            switch core.state {
            case .idle, .stopped, .error:
                Label("Boot", systemImage: "power")
            case .loading:
                ProgressView().tint(.white)
            case .running:
                Label("Stop", systemImage: "stop.circle")
            case .paused:
                Label("Resume", systemImage: "play.circle")
            }
        }
        .tint(.green)
    }

    // MARK: - Helpers

    private var stateColor: Color {
        switch core.state {
        case .running:        return .green
        case .paused:         return .yellow
        case .loading:        return .blue
        case .error:          return .red
        case .idle, .stopped: return .gray
        }
    }

    private var stateLabel: String {
        switch core.state {
        case .idle:           return "Idle"
        case .loading:        return "Loading…"
        case .running:        return "Running"
        case .paused:         return "Paused"
        case .stopped:        return "Stopped"
        case .error(let msg): return "Error: \(msg)"
        }
    }

    private func submitCommand() {
        let cmd = commandInput.trimmingCharacters(in: .whitespaces)
        guard !cmd.isEmpty else { return }
        core.sendCommand(cmd)
        commandInput = ""
    }

    private func handleBootTap() {
        switch core.state {
        case .idle, .stopped, .error:
            Task { await core.boot() }
        case .running:
            core.stop()
        case .paused:
            core.resume()
        case .loading:
            break
        }
    }
}

// MARK: - Preview

#if DEBUG
struct EmulatorView_Previews: PreviewProvider {
    static var previews: some View {
        EmulatorView()
    }
}
#endif
