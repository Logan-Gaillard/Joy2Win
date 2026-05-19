import configparser
import os

class Config:
    _instance = None
    _defaults = {
        "mac_address": "FFFFFFFFFFFF",
        "type_controller": 0,
        "orientation": 0,
        "led_player": "0001",
        "enable_dsu": False,
        "mouse_mode": 0,
    }

    # Singleton pattern to ensure only one instance of Config exists
    def __new__(cls, config_path="config.ini"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_path = config_path
            cls._instance._init_defaults()
            cls._instance.load_config()
        return cls._instance

    def _init_defaults(self):
        for key, value in self._defaults.items():
            setattr(self, key, value)

    def load_config(self):
        config_parser = configparser.ConfigParser()
        if not os.path.exists(self._config_path):
            print(f"{self._config_path} not found. Using default values.")
            return

        config_parser.read(self._config_path)
        if "Controller" in config_parser:
            section = config_parser["Controller"]
            self.type_controller = int(section.get("type_controller", self.type_controller))
            self.orientation = int(section.get("orientation", self.orientation))
            self.led_player = str(section.get("led_player", self.led_player))
            self.enable_dsu = section.get("enable_dsu", str(self.enable_dsu)).lower() == '1'
            self.mouse_mode = int(section.get("mouse_mode", self.mouse_mode if self.mouse_mode == 0 or self.mouse_mode == 1 or self.mouse_mode == 2 else 0))
            
            configMacAddress = section.get("mac_address", self.mac_address)
            if(configMacAddress and len(configMacAddress) >= 12 and len(configMacAddress) <= 17 and all(c in "0123456789ABCDEF:-" for c in configMacAddress.upper())): # Valid MAC address format like AABBCCDDEEFF
                configMacAddress = configMacAddress.replace(":", "")
                configMacAddress = configMacAddress.replace("-", "")
                self.mac_address = bytes.fromhex(configMacAddress)[::-1] # Convert mac to little-endian format
            else:
                print(f"Invalid MAC address in {self._config_path}. Using default: {self.mac_address}")
                self.mac_address = self._defaults["mac_address"]

        else:
            print(f"Section 'Controller' not found in {self._config_path}. Using default values.")
            self._init_defaults()

    def getConfig(self):
        return {
            "mac_address": self.mac_address,
            "type_controller": self.type_controller,
            "orientation": self.orientation,
            "led_player": self.led_player,
            "enable_dsu": self.enable_dsu,
            "mouse_mode": self.mouse_mode,
        }