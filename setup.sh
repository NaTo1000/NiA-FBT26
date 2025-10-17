#!/bin/bash
set -e

echo "🔧 Setting up NiA FBT26..."

# Check Python version
python3 --version || { echo "Python 3.8+ required"; exit 1; }

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

# Download FBT wrapper scripts
echo "📥 Downloading FBT utilities..."
mkdir -p scripts/fbt

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

echo "✅ Setup complete!"
echo "Run ./nia-fbt26 to start the application"
