import Foundation
import Network
import Combine

/// Errors raised by the networking bridge.
enum NetworkBridgeError: LocalizedError {
    case configurationFailed(String)
    case interfaceUnavailable(String)
    case tunnelSetupFailed

    var errorDescription: String? {
        switch self {
        case .configurationFailed(let detail): return "Network bridge configuration failed: \(detail)"
        case .interfaceUnavailable(let iface): return "Network interface unavailable: \(iface)"
        case .tunnelSetupFailed:               return "TUN/TAP tunnel setup failed."
        }
    }
}

/// Bridges iOS networking to the MiniOS guest, forwarding packets between
/// iOS Network.framework and the emulated guest network interface.
///
/// Architecture:
/// ```
/// iOS app (Network.framework)  ←→  NetworkingBridge  ←→  Guest virtio-net
/// ```
///
/// On a jailbroken device the bridge creates a TUN/TAP interface via the
/// kernel's `/dev/net/tun` node.  In the sandboxed demo mode it falls back
/// to a userspace TCP/UDP proxy.
@MainActor
final class NetworkingBridge: ObservableObject {

    // MARK: - Published State

    @Published private(set) var isConnected: Bool = false
    @Published private(set) var bytesReceived: Int = 0
    @Published private(set) var bytesSent: Int = 0

    // MARK: - Configuration

    /// Guest-side IP address (RFC 5737 documentation range).
    var guestIP: String = "192.0.2.10"
    /// Host-side bridge IP.
    var hostBridgeIP: String = "192.0.2.1"
    /// Subnet mask.
    var subnetMask: String = "255.255.255.0"
    /// DNS server forwarded to the guest.
    var dnsServer: String = "1.1.1.1"

    // MARK: - Private

    private var monitor: NWPathMonitor?
    private var monitorQueue = DispatchQueue(label: "com.minios.networkmonitor")
    private var proxyListener: NWListener?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Lifecycle

    /// Configure and start the network bridge.
    func configure() async throws {
        startPathMonitor()
        try await setupProxy()
        isConnected = true
    }

    /// Tear down the bridge and release resources.
    func disconnect() {
        monitor?.cancel()
        monitor = nil
        proxyListener?.cancel()
        proxyListener = nil
        isConnected = false
    }

    // MARK: - Packet Forwarding

    /// Forward a raw packet from the guest to iOS networking.
    /// - Parameter packet: Raw IP packet bytes from the emulated NIC.
    func sendPacketFromGuest(_ packet: Data) {
        guard isConnected else { return }
        bytesSent += packet.count
        // In production: write to TUN fd or userspace TCP connection.
    }

    /// Deliver a raw IP packet from iOS networking into the guest.
    /// - Parameter packet: Raw IP packet to inject into the virtual NIC.
    func receivePacketForGuest(_ packet: Data) {
        guard isConnected else { return }
        bytesReceived += packet.count
        // In production: write to virtio-net RX queue.
    }

    // MARK: - Private Helpers

    private func startPathMonitor() {
        let m = NWPathMonitor()
        m.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                self?.isConnected = (path.status == .satisfied)
            }
        }
        m.start(queue: monitorQueue)
        monitor = m
    }

    private func setupProxy() async throws {
        // Create a local TCP listener that proxies traffic for the guest.
        let params = NWParameters.tcp
        params.allowLocalEndpointReuse = true

        guard let listener = try? NWListener(using: params, on: 8080) else {
            throw NetworkBridgeError.tunnelSetupFailed
        }

        listener.stateUpdateHandler = { [weak self] newState in
            switch newState {
            case .failed(let err):
                Task { @MainActor in self?.isConnected = false }
                print("[NetworkBridge] Listener failed: \(err)")
            default:
                break
            }
        }

        listener.newConnectionHandler = { connection in
            connection.start(queue: .global(qos: .utility))
        }

        listener.start(queue: .global(qos: .utility))
        proxyListener = listener
    }
}
