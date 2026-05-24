# Changelog — v2.0.0 (Medusa)

## 🚀 Major Release — Full AI Stack

### Added
- **AI Orchestration Stack** — 10 integrated AI models (DeepSeek, CodeLlama, Llama, Mistral, Phi-3, StarCoder2, BGE)
- **Multi-Model Research Lab** — AI models conferencing for complex analysis tasks
- **Self-Healing Runner Manager** — Auto-restarts and recovers failed AI model services
- **ESP32 TinyML Firmware** — Edge AI with quantized models for signal classification and log analysis
- **iOS SwiftUI App** — Full mobile companion with AI integration (Xcode 15+)
- **ARM64 / AArch64 / RISC-V Edition** — Optimized embedded builds
- **Raspberry Pi 5 Edition** — Hardware-accelerated builds for RPi5
- **Thumb Drive VM Edition** — Portable bootable VM with full suite
- **jessicAi medusa** — Ethical cybersecurity AI assistant for authorized penetration testing
- **MiniOS Emulation Layer** — Run MiniOS tools on iOS via SwiftUI host
- **Runtime Parameter System** — `config/runtime.json` with CLI args and env var overrides
- **Multi-Stage Docker Builds** — Efficient layered images with GitHub Actions CI/CD
- **Semantic Versioning** — `versions/` directory with per-version configs and changelogs
- **Developer Portal** — `DEVELOPERS.md` with comprehensive resource links

### Changed
- Python minimum version raised to 3.10
- Node.js minimum version raised to 18
- Configuration format updated with `runtime_flags` and `ports` sections
- API endpoints now versioned under `/api/v2/`

### Fixed
- Build cache invalidation on minor config changes
- ESP32 flash timeout on slow USB connections
- GitHub API rate limiting during bulk searches

### Security
- Ethical use enforcement added to all cybersecurity features
- Audit logging for all security tool operations
- Authorized operations allowlist in `config/runtime.json`

---
*Released: 2024-06-01*
