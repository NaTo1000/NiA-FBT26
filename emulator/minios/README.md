# MiniOS Emulator Build Scripts

Scripts for building MiniOS binaries and disk images optimised for use with the iOS emulator app.

## Prerequisites

| Tool | Purpose |
|------|---------|
| Docker | Reproducible cross-compilation environment |
| `mkfs.ext4` (e2fsprogs) | Raw disk image formatting |
| `xz` | Image compression |
| `sha256sum` | Checksum generation |

On macOS, install prerequisites via Homebrew:

```bash
brew install e2fsprogs xz coreutils
```

## Building

```bash
cd emulator/minios

# Default: ARM64 image
./build.sh

# x86_64 image
./build.sh --arch x86_64

# Custom output directory
./build.sh --output /tmp/minios-images

# Clean build
./build.sh --clean
```

## Output

```
dist/
  minios-arm64-1.0.0.img        Raw ext4 disk image
  minios-arm64-1.0.0.img.xz     Compressed image (ship this)
  SHA256SUMS                    Checksums for verification
```

## Deploying to iOS

1. Build and compress the image:

   ```bash
   ./build.sh --arch arm64
   ```

2. **Bundle with Xcode** (recommended for demo):  
   Drag `dist/minios-arm64-1.0.0.img` into `ios/MiniOSEmulator/Resources/`.  
   The `MiniOSLoader` will find it in the app bundle automatically.

3. **Side-load to device**:  
   Copy the image to the app's Documents directory via iTunes File Sharing or `ideviceinstaller`.

## Included Tools

| Tool | Purpose |
|------|---------|
| Nmap | Network discovery and port scanning |
| Ncat | Networking Swiss Army knife |
| OpenSSL | TLS diagnostics, certificate inspection |
| curl | HTTP/HTTPS client |
| BusyBox | Lightweight Unix utilities |
| Python 3 | Scripting and custom tool development |

## Security

All tools are configured for **authorised security testing only**.  
Misuse against networks you do not own or have explicit permission to test is illegal.

## Architecture

```
iOS App (SwiftUI)
  └─ EmulatorCore
       ├─ MiniOSLoader  ──── reads disk image
       ├─ NetworkingBridge ── TUN/TAP or proxy
       └─ ARM64→x86 DBT ──── dynamic binary translation
```
