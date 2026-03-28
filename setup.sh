#!/bin/bash
set -e

echo "🔧 Setting up NiA FBT26 v2.0..."

# Check Python 3.11+
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo "❌ Python 3.11+ is required (found $PY_VERSION)"
    exit 1
fi
echo "✅ Python $PY_VERSION found"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Arduino CLI (optional)
if [ ! -f "tools/arduino-cli" ]; then
    echo "🔧 Installing Arduino CLI..."
    mkdir -p tools
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=./tools sh
fi

# Create default config if not present
if [ ! -f "config/settings.json" ]; then
    echo "📝 Creating default config/settings.json..."
    mkdir -p config
    python3 -c "
import json
cfg = {
    'version': '2.0.0',
    'firmware_path': '~/flipper-firmware',
    'sdk_path': '~/flipper-sdk',
    'arduino_path': '~/Arduino',
    'esp32_tools': '~/.platformio',
    'python_env': '.venv',
    'editor': {'theme': 'monokai', 'font_size': 12, 'tab_size': 4, 'show_line_numbers': True},
    'build': {'parallel_jobs': 4, 'optimization': 'size', 'debug': True},
    'github': {'token': '', 'cache_duration': 3600},
    'ai_integration': {'huggingface_api_key': '', 'model_endpoint': '', 'local_model_path': ''},
    'device': {'auto_connect': True, 'default_baud_rate': 115200}
}
json.dump(cfg, open('config/settings.json', 'w'), indent=2)
print('config/settings.json created')
"
fi

# Create launch script
echo "🚀 Creating launch script..."
cat > nia-fbt26 << 'LAUNCH'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 src/main.py "$@"
LAUNCH
chmod +x nia-fbt26

echo ""
echo "✅ Setup complete!"
echo "Run ./nia-fbt26 to start the application"

