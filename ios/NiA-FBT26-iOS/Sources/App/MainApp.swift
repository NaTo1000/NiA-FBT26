import SwiftUI

@main
struct NiAFBT26App: App {
    @StateObject private var settings = AppSettings()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(settings)
        }
    }
}

struct ContentView: View {
    var body: some View {
        TabView {
            FAPBuilderView()
                .tabItem {
                    Label("FAP Builder", systemImage: "hammer.fill")
                }
            FirmwareBuilderView()
                .tabItem {
                    Label("Firmware", systemImage: "cpu.fill")
                }
            AIResearchView()
                .tabItem {
                    Label("AI Research", systemImage: "brain")
                }
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
        }
    }
}
