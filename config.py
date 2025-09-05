import configparser
import os

class Config:
    _instance = None
    _defaults = {
        "controller": 0,
        "orientation": 0,
        "led_player": 0b0001,
        "save_mac_address": False,
        "enable_dsu": False,
        "mouse_mode": 0,
        "controller_type": 0,
        "mac_address": "FFFFFFFFFFFF"
    }

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
            self.controller = int(section.get("controller", self.controller if self.controller in [0,1,2] else 0))
            self.orientation = int(section.get("orientation", self.orientation if self.orientation in [0,1] else 0))
            self.led_player = str(section.get("led_player", self.led_player))
            self.save_mac_address = section.get("save_mac_address", str(self.save_mac_address)).lower() == '1'
            self.enable_dsu = section.get("enable_dsu", str(self.enable_dsu)).lower() == '1'
            self.mouse_mode = int(section.get("mouse_mode", self.mouse_mode if self.mouse_mode in [0,1,2] else 0))
            self.controller_type = int(section.get("controller_type", self.controller_type if self.controller_type in [0,1,2] else 0))

            if "Bluetooth" in config_parser:
                section = config_parser["Bluetooth"]
                configMacAddress =  section.get("mac_address", self.mac_address)
                if(configMacAddress and len(configMacAddress) == 12 and all(c in "0123456789ABCDEF" for c in configMacAddress.upper())): # Valid MAC address format like AABBCCDDEEFF
                    self.mac_address = bytes.fromhex(configMacAddress)[::-1] # Convert mac to little-endian format
                else:
                    print(f"Invalid MAC address in {self._config_path}. Using default: {self.mac_address}")
                    self.mac_address = self._defaults["mac_address"]
            else:
                print(f"Section 'Bluetooth' not found in {self._config_path}. disabling save_mac_address.")
                self.save_mac_address = False
        else:
            print(f"Section 'Controller' not found in {self._config_path}. Using default values.")
            self._init_defaults()

    def getConfig(self):
        return {
            "controller": self.controller,
            "orientation": self.orientation,
            "led_player": self.led_player,
            "save_mac_address": self.save_mac_address,
            "enable_dsu": self.enable_dsu,
            "mouse_mode": self.mouse_mode,
            "controller_type": self.controller_type,
            "mac_address": self.mac_address
        }