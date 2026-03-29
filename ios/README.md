# NiA-FBT26 iOS App

A native SwiftUI iOS companion app for the NiA-FBT26 Flipper Zero development suite.

## Requirements

- Xcode 15+
- iOS 15.0+ deployment target
- macOS 13+ (Ventura) for building
- A running instance of the NiA-FBT26 orchestration backend (see root `README.md`)

## Project Structure

```
ios/NiA-FBT26-iOS/
├── Sources/
│   ├── App/
│   │   └── MainApp.swift          # App entry point + TabView
│   ├── Views/
│   │   ├── FAPBuilderView.swift   # FAP code generation UI
│   │   ├── FirmwareBuilderView.swift # Firmware build/analyze UI
│   │   └── AIResearchView.swift   # Multi-model research conferencing UI
│   ├── Settings/
│   │   └── SettingsView.swift     # Server config + API key (Keychain)
│   ├── Networking/
│   │   └── APIManager.swift       # URLSession-based API client
│   └── Models/
│       └── AIResponse.swift       # Codable data models
└── Tests/
    └── APIManagerTests.swift      # Unit tests for models and networking
```

## Setup

### 1. Start the Backend

On your Mac or server running the orchestration layer:

```bash
export HUGGINGFACE_API_KEY=your_key_here
cd docker
docker compose -f docker-compose.full.yml up --build
```

The super orchestrator will listen on port **7000**.

### 2. Open in Xcode

1. Open `ios/NiA-FBT26-iOS/NiA-FBT26-iOS.xcodeproj` in Xcode.
2. Select your target device or simulator (iOS 15+).
3. In the **Settings** tab of the app, enter your Mac's local IP address as the server URL (e.g. `http://192.168.1.x`) and port `7000`.

### 3. Build & Run

Press **⌘R** in Xcode to build and run.

## Configuration

Server URL and port are persisted via `UserDefaults`. The HuggingFace API key is stored securely in the **iOS Keychain** (`kSecAttrAccessibleWhenUnlockedThisDeviceOnly`).

Default configuration (`config/settings.json`):

```json
{
  "ios": {
    "server_url": "http://localhost:7000",
    "huggingface_api_key": "",
    "bluetooth_enabled": true
  }
}
```

## Features

| Tab | Description |
|-----|-------------|
| **FAP Builder** | Write or describe FAP code; send to AI for code generation |
| **Firmware Builder** | Pick firmware source files; build and analyze with AI |
| **AI Research** | Select models, enter a topic, run a multi-model conference |
| **Settings** | Configure server URL/port, HuggingFace key, Bluetooth |

## Bluetooth (Flipper Zero)

The app uses **CoreBluetooth** to connect directly to a Flipper Zero device. Enable Bluetooth in the Settings tab. The device must be in pairing mode. Once connected, firmware flashing commands are sent over BLE.

## Network Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/fap/generate` | FAP code generation |
| `POST /api/firmware/build` | Firmware build |
| `POST /api/firmware/analyze` | Firmware AI analysis |
| `POST /api/research/conference` | Multi-model conferencing |
| `POST /api/ai/query` | Single-model query |

## Running Tests

In Xcode, press **⌘U** to run all unit tests in `Tests/APIManagerTests.swift`.

## Offline Mode

When the server is unreachable, the app displays a clear error message. Recent results are displayed from the session until a connection is re-established.
