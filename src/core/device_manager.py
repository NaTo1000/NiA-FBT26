class DeviceManager:
    def __init__(self):
        self.device = None
        self.connected = False
    
    def connect(self):
        print("Connecting to Flipper Zero...")
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
    
    def flash_firmware(self, firmware_path):
        print(f"Flashing firmware: {firmware_path}")
