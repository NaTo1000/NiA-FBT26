FROM python:3.11-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    libgl1 \
    libglib2.0-0 \
    libusb-1.0-0-dev \
    libegl1 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Install Arduino CLI
RUN mkdir -p /opt/tools && \
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
    | BINDIR=/opt/tools sh
ENV PATH="/opt/tools:${PATH}"

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create default config if not present
RUN python3 -c "
import json, os
cfg_path = 'config/settings.json'
if not os.path.exists(cfg_path):
    os.makedirs('config', exist_ok=True)
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
    json.dump(cfg, open(cfg_path, 'w'), indent=2)
"

ENTRYPOINT ["python3", "src/main.py"]
