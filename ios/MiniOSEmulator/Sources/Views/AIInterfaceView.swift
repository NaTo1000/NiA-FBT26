import SwiftUI
import Combine

/// Represents a single message in the jessicAi conversation.
struct AIMessage: Identifiable {
    enum Role { case user, assistant }
    let id = UUID()
    let role: Role
    let content: String
    let timestamp: Date
}

/// SwiftUI view providing a chat-style interface for jessicAi mudusa,
/// the AI security assistant integrated into the MiniOS emulator.
struct AIInterfaceView: View {

    @StateObject private var core = EmulatorCore()
    @State private var messages: [AIMessage] = [
        AIMessage(
            role: .assistant,
            content: "Hello! I'm jessicAi mudusa — your on-device security AI. I'm running inside MiniOS. Ask me anything about your network, tools, or current threats.",
            timestamp: Date()
        )
    ]
    @State private var inputText: String = ""
    @State private var isThinking: Bool = false
    @FocusState private var inputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            aiHeader
            Divider().overlay(Color.green.opacity(0.4))
            messageList
            Divider().overlay(Color.green.opacity(0.4))
            inputBar
        }
        .background(Color.black.ignoresSafeArea())
        .navigationTitle("jessicAi mudusa")
        .navigationBarTitleDisplayMode(.inline)
        .preferredColorScheme(.dark)
    }

    // MARK: - Header

    private var aiHeader: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(Color.green.opacity(0.2)).frame(width: 44, height: 44)
                Image(systemName: "brain.head.profile")
                    .font(.title2)
                    .foregroundColor(.green)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("jessicAi mudusa")
                    .font(.headline)
                    .foregroundColor(.white)
                HStack(spacing: 4) {
                    Circle().fill(Color.green).frame(width: 6, height: 6)
                    Text("Running in MiniOS")
                        .font(.caption)
                        .foregroundColor(.green)
                }
            }
            Spacer()
            Button(action: clearConversation) {
                Image(systemName: "trash")
                    .foregroundColor(.gray)
            }
        }
        .padding()
        .background(Color(white: 0.08))
    }

    // MARK: - Message List

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(messages) { message in
                        messageBubble(message)
                            .id(message.id)
                    }
                    if isThinking {
                        thinkingIndicator
                    }
                }
                .padding()
            }
            .onChange(of: messages.count) { _ in
                withAnimation {
                    proxy.scrollTo(messages.last?.id, anchor: .bottom)
                }
            }
            .onChange(of: isThinking) { _ in
                withAnimation {
                    proxy.scrollTo(messages.last?.id, anchor: .bottom)
                }
            }
        }
    }

    private func messageBubble(_ message: AIMessage) -> some View {
        HStack(alignment: .top, spacing: 8) {
            if message.role == .assistant {
                Image(systemName: "brain.head.profile")
                    .font(.caption)
                    .foregroundColor(.green)
                    .padding(.top, 4)
            } else {
                Spacer()
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(10)
                    .background(
                        message.role == .user
                            ? Color.green.opacity(0.25)
                            : Color(white: 0.12)
                    )
                    .foregroundColor(.white)
                    .font(.system(size: 14))
                    .cornerRadius(12)

                Text(message.timestamp, style: .time)
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
            }

            if message.role == .user {
                Image(systemName: "person.circle.fill")
                    .font(.caption)
                    .foregroundColor(.blue)
                    .padding(.top, 4)
            } else {
                Spacer()
            }
        }
    }

    private var thinkingIndicator: some View {
        HStack(spacing: 6) {
            ForEach(0..<3) { i in
                Circle()
                    .fill(Color.green)
                    .frame(width: 6, height: 6)
                    .opacity(0.6)
                    .animation(
                        .easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.2),
                        value: isThinking
                    )
            }
        }
        .padding(.leading, 28)
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        HStack(spacing: 8) {
            TextField("Ask jessicAi mudusa…", text: $inputText, axis: .vertical)
                .lineLimit(1...4)
                .textFieldStyle(.plain)
                .font(.system(size: 14))
                .foregroundColor(.white)
                .accentColor(.green)
                .focused($inputFocused)
                .padding(10)
                .background(Color(white: 0.12))
                .cornerRadius(20)
                .onSubmit { sendMessage() }

            Button(action: sendMessage) {
                Image(systemName: isThinking ? "stop.circle.fill" : "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundColor(inputText.isEmpty && !isThinking ? .gray : .green)
            }
            .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty && !isThinking)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(white: 0.08))
    }

    // MARK: - Actions

    private func sendMessage() {
        if isThinking {
            isThinking = false
            return
        }
        let text = inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        let userMsg = AIMessage(role: .user, content: text, timestamp: Date())
        messages.append(userMsg)
        inputText = ""
        isThinking = true

        // Forward the query to MiniOS AI via the emulator console.
        core.sendCommand("jessicai query \"\(text)\"")

        // Simulate the AI response (real impl reads from MiniOS stdout).
        Task {
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            let reply = generateContextualReply(for: text)
            let aiMsg = AIMessage(role: .assistant, content: reply, timestamp: Date())
            messages.append(aiMsg)
            isThinking = false
        }
    }

    private func clearConversation() {
        messages = messages.prefix(1).map { $0 }
    }

    /// Returns a contextual placeholder response.
    /// In production this is replaced by the actual jessicAi mudusa inference output.
    private func generateContextualReply(for query: String) -> String {
        let lower = query.lowercased()
        if lower.contains("scan") || lower.contains("nmap") {
            return "I can run an Nmap scan for you. Open the Tools tab, select Nmap, enter your target, and press Run. Make sure you have written authorisation before scanning any network."
        } else if lower.contains("password") || lower.contains("hash") {
            return "Password analysis is available via Hashcat inside MiniOS. Use it only against hashes you own or have explicit permission to test."
        } else if lower.contains("flipper") {
            return "The Flipper Zero bridge is ready. Use the Tools tab → Flipper Zero Bridge to connect to the emulated device."
        } else if lower.contains("hello") || lower.contains("hi") {
            return "Hi! I'm ready to assist with your authorised cybersecurity assessments. What would you like to analyse today?"
        } else {
            return "Received your query. I'm processing it inside MiniOS — this response is a local stub; full AI inference runs when MiniOS is booted."
        }
    }
}

// MARK: - Preview

#if DEBUG
struct AIInterfaceView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView { AIInterfaceView() }
    }
}
#endif
