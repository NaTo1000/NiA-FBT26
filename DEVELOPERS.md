# NiA FBT26 — Developer Guide & Resources

> **For the Flipper Zero community & ethical cybersecurity professionals.**

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Runtime Parameters](#runtime-parameters)
- [Building Images](#building-images)
- [Testing](#testing)
- [Versioning](#versioning)
- [Contributing](#contributing)
- [Developer Links](#developer-links)

---

## 🚀 Quick Start

```bash
# Clone and set up
git clone https://github.com/NaTo1000/NiA-FBT26.git
cd NiA-FBT26
./setup.sh

# Run with default config
python3 src/main.py

# Run with custom parameters
python3 src/main.py --version v2.0.0 --port 8080 --log-level DEBUG

# Run with environment variables
NIA_SERVER_PORT=9090 NIA_DEBUG=true python3 src/main.py

# Run via Docker
docker run -e NIA_SERVER_PORT=8080 ghcr.io/nato1000/nia-fbt26-app:latest
```

---

## 🏗️ Architecture

```
NiA-FBT26/
├── src/                    # Python source
│   ├── main.py             # Entry point with CLI args
│   ├── core/               # Config, device management
│   ├── gui/                # PyQt6 GUI components
│   ├── builders/           # FAP/firmware build systems
│   └── ...
├── config/
│   ├── runtime.json        # Runtime parameter schema
│   └── settings.json       # User settings with runtime_flags
├── docker/                 # Multi-stage Dockerfiles
│   ├── Dockerfile.app
│   ├── Dockerfile.orchestrator
│   ├── Dockerfile.api
│   ├── Dockerfile.code_gen
│   └── Dockerfile.code_review
├── scripts/
│   ├── build_images.sh     # Build all Docker images
│   └── test_all.sh         # Run full test suite
├── tests/
│   ├── unit/               # Unit tests (pytest)
│   └── integration/        # Integration tests
├── versions/
│   ├── v1.0.0/             # Version config + changelog
│   └── v2.0.0/
└── .github/workflows/ci.yml  # CI/CD pipeline
```

---

## ⚙️ Runtime Parameters

### Config File (`config/runtime.json`)

Override any parameter at runtime using environment variables or CLI flags.

| Config Key | Env Var | CLI Flag | Default |
|---|---|---|---|
| `runtime.log_level` | `NIA_LOG_LEVEL` | `--log-level` | `INFO` |
| `runtime.debug` | `NIA_DEBUG` | `--debug` | `false` |
| `runtime.environment` | `NIA_ENV` | `--env` | `production` |
| `server.port` | `NIA_SERVER_PORT` | `--port` | `8080` |
| `server.host` | `NIA_SERVER_HOST` | `--host` | `0.0.0.0` |
| `build.parallel_jobs` | `NIA_BUILD_JOBS` | `--jobs` | `4` |

### Example: Launch with Custom Parameters

```bash
# CLI args
python3 src/main.py --version v2.0.0 --port 9090 --log-level DEBUG --debug

# Environment variables (Docker-friendly)
export NIA_ENV=production
export NIA_LOG_LEVEL=WARNING
export NIA_SERVER_PORT=8080
python3 src/main.py

# Docker with env vars
docker run \
  -e NIA_ENV=production \
  -e NIA_SERVER_PORT=8080 \
  -e NIA_LOG_LEVEL=INFO \
  -p 8080:8080 \
  ghcr.io/nato1000/nia-fbt26-app:2.0.0
```

---

## 🐳 Building Images

### Build All Images

```bash
# Using the build script
VERSION=2.0.0 REGISTRY=ghcr.io/nato1000 ./scripts/build_images.sh

# Build individual image
docker build -f docker/Dockerfile.app -t nia-fbt26-app:dev .

# Build with cache
docker buildx build --cache-from type=gha -f docker/Dockerfile.app -t nia-fbt26-app:dev .
```

### Available Images

| Image | Purpose | Port |
|---|---|---|
| `nia-fbt26-app` | Main application | 8080 |
| `nia-fbt26-api` | REST API service | 8081 |
| `nia-fbt26-orchestrator` | AI model orchestration | 8082 |
| `nia-fbt26-code-gen` | Code generation (DeepSeek) | 8083 |
| `nia-fbt26-code-review` | Code review (CodeLlama) | 8084 |

### Registry

Images are published to GitHub Container Registry:
- `ghcr.io/nato1000/nia-fbt26-app:latest`
- `ghcr.io/nato1000/nia-fbt26-app:2.0.0`

---

## 🧪 Testing

### Run All Tests

```bash
# Using the test script
./scripts/test_all.sh

# Using pytest directly
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── unit/
│   ├── test_config.py          # Config manager and JSON validation
│   └── test_runtime_params.py  # Runtime parameters and CLI args
└── integration/
    └── test_config_integration.py  # End-to-end config/version checks
```

### CI/CD

Tests run automatically on every push and pull request via GitHub Actions.
See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## 🏷️ Versioning

This project uses **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

| Version | Codename | Status | Notes |
|---|---|---|---|
| v1.0.0 | Flipper | ✅ Stable | Initial release |
| v2.0.0 | Medusa | 🔄 Beta | Full AI stack + cybersecurity |

### Releasing a New Version

```bash
# 1. Update version files
echo "X.Y.Z" > versions/current.txt
# 2. Create version directory
mkdir -p versions/vX.Y.Z
# 3. Add version.json and CHANGELOG.md
# 4. Tag and push
git tag vX.Y.Z
git push origin vX.Y.Z
```

The CI pipeline will automatically build and publish Docker images for tagged releases.

---

## 🤝 Contributing

1. Fork the repository: [NaTo1000/NiA-FBT26](https://github.com/NaTo1000/NiA-FBT26/fork)
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes in `tests/`
4. Run the test suite: `./scripts/test_all.sh`
5. Commit your changes: `git commit -m 'Add my feature'`
6. Push the branch: `git push origin feature/my-feature`
7. Open a Pull Request

### Code Style

```bash
# Format with Black
black src/

# Lint with flake8
flake8 src/ --max-line-length=120
```

---

## 🔗 Developer Links

### Project Resources

| Resource | Link |
|---|---|
| 📦 Repository | [github.com/NaTo1000/NiA-FBT26](https://github.com/NaTo1000/NiA-FBT26) |
| 🐛 Issues | [github.com/NaTo1000/NiA-FBT26/issues](https://github.com/NaTo1000/NiA-FBT26/issues) |
| 💬 Discussions | [github.com/NaTo1000/NiA-FBT26/discussions](https://github.com/NaTo1000/NiA-FBT26/discussions) |
| 🔀 Pull Requests | [github.com/NaTo1000/NiA-FBT26/pulls](https://github.com/NaTo1000/NiA-FBT26/pulls) |
| 📋 Projects | [github.com/NaTo1000/NiA-FBT26/projects](https://github.com/NaTo1000/NiA-FBT26/projects) |
| 📦 Packages (GHCR) | [github.com/NaTo1000?tab=packages](https://github.com/NaTo1000?tab=packages) |

### Flipper Zero Resources

| Resource | Link |
|---|---|
| 🐬 Flipper Zero Official | [flipperzero.one](https://flipperzero.one) |
| 📖 Flipper Docs | [docs.flipper.net](https://docs.flipper.net) |
| 🔧 Flipper Firmware (Official) | [github.com/flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) |
| ⚡ Unleashed Firmware | [github.com/DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) |
| 🌊 Momentum Firmware | [github.com/Next-Flip/Momentum-Firmware](https://github.com/Next-Flip/Momentum-Firmware) |
| 🎮 Flipper Application Catalog | [github.com/flipperdevices/flipper-application-catalog](https://github.com/flipperdevices/flipper-application-catalog) |
| 📺 FBT Docs | [github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md) |

### AI Models (HuggingFace)

| Model | Purpose | Link |
|---|---|---|
| DeepSeek Coder | Code generation | [huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct) |
| CodeLlama 13B | Code review | [huggingface.co/meta-llama/CodeLlama-13b-Instruct-hf](https://huggingface.co/meta-llama/CodeLlama-13b-Instruct-hf) |
| Llama 3 70B | NL→CLI | [huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct) |
| Mistral 7B | Docs generation | [huggingface.co/mistralai/Mistral-7B-Instruct-v0.2](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2) |
| Phi-3 Mini | Log analysis | [huggingface.co/microsoft/Phi-3-mini-4k-instruct](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) |
| StarCoder2 7B | Firmware analysis | [huggingface.co/bigcode/starcoder2-7b](https://huggingface.co/bigcode/starcoder2-7b) |
| BGE Small EN | GitHub ranking | [huggingface.co/BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) |

### ESP32 & Embedded

| Resource | Link |
|---|---|
| 🔩 ESP-IDF | [docs.espressif.com/projects/esp-idf](https://docs.espressif.com/projects/esp-idf/en/latest/) |
| 📱 PlatformIO | [platformio.org](https://platformio.org) |
| 🤖 TensorFlow Lite Micro | [tensorflow.org/lite/microcontrollers](https://www.tensorflow.org/lite/microcontrollers) |
| 🧠 Edge Impulse | [edgeimpulse.com](https://edgeimpulse.com) |

### iOS & macOS

| Resource | Link |
|---|---|
| 🍎 SwiftUI Docs | [developer.apple.com/swiftui](https://developer.apple.com/swiftui/) |
| 🧪 XCTest | [developer.apple.com/documentation/xctest](https://developer.apple.com/documentation/xctest) |
| 📦 Swift Package Manager | [swift.org/package-manager](https://www.swift.org/package-manager/) |

### Tools & Infrastructure

| Resource | Link |
|---|---|
| 🧪 pytest | [docs.pytest.org](https://docs.pytest.org) |
| 🐳 Docker Buildx | [docs.docker.com/buildx](https://docs.docker.com/buildx/working-with-buildx/) |
| ⚙️ GitHub Actions | [docs.github.com/actions](https://docs.github.com/en/actions) |
| 📦 GHCR | [docs.github.com/packages](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) |

---

## 🛡️ Ethical Use

This project is intended **exclusively for authorized cybersecurity research and development**. All security-related features have ethical use enforcement enabled in `config/runtime.json`.

By using this software, you agree to:
- Only use security tools on systems you own or have explicit authorization to test
- Comply with all applicable laws and regulations
- Follow responsible disclosure for any vulnerabilities discovered
- Not use this software for unauthorized access, surveillance, or harm

---

## 📞 Support & Troubleshooting

**Common Issues:**

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: PyQt6` | Run `pip install PyQt6` or `./setup.sh` |
| ESP32 flash timeout | Check USB cable, increase `device.usb_timeout` in `config/runtime.json` |
| GitHub API rate limit | Add your token to `config/settings.json` or `NIA_GITHUB_TOKEN` env var |
| Build cache errors | Delete `.build_cache/` and retry |
| Ollama model not found | Run `ollama pull <model>` first |

**Get help:**
- 🐛 [Open an issue](https://github.com/NaTo1000/NiA-FBT26/issues/new)
- 💬 [Start a discussion](https://github.com/NaTo1000/NiA-FBT26/discussions/new)

---

*Built with ❤️ by [NaTo1000](https://github.com/NaTo1000) — For the Flipper Zero Community*
