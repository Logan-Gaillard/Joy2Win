import configparser
import os
from program.constant import RED_TEXT, GREEN_TEXT, YELLOW_TEXT, RESET_TEXT, BOLD_TEXT

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
    issues = 0

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
            
            # !!! Type Controller !!!#
            controller_type = int(section.get("type_controller", self.type_controller))
            if controller_type in [0, 1]:
                self.type_controller = controller_type
            else:
                print(f"{RED_TEXT}Invalid type_controller value in {self._config_path}. Using default: {self.type_controller}{RESET_TEXT}")
                self.issues += 1
                
            # !!! Orientation !!!#
            orientation = int(section.get("orientation", self.orientation))
            if orientation in [0, 1]:
                self.orientation = orientation
            else:
                print(f"{RED_TEXT}Invalid orientation value in {self._config_path}. Using default: {self.orientation}{RESET_TEXT}")
                self.issues += 1

            # !!! Player LED !!!#
            led_player = str(section.get("led_player", self.led_player))
            if led_player.isdigit() and 0 <= int(led_player) <= 15:
                self.led_player = led_player
            else:
                print(f"{RED_TEXT}Invalid led_player value in {self._config_path}. Using default: {self.led_player}{RESET_TEXT}")
                self.issues += 1

            # !!! Enable DSU !!!#
            enableDsu = section.get("enable_dsu", str(self.enable_dsu)).lower()
            if enableDsu in ['0', '1']:
                self.enable_dsu = enableDsu == '1'
            else:
                print(f"{RED_TEXT}Invalid enable_dsu value in {self._config_path}. Using default: {self.enable_dsu}{RESET_TEXT}")
                self.issues += 1

            # !!! Mouse Mode !!!#
            mouse_mode = int(section.get("mouse_mode", self.mouse_mode))
            if mouse_mode in [0, 1, 2]:
                self.mouse_mode = mouse_mode
            else:
                print(f"{RED_TEXT}Invalid mouse_mode value in {self._config_path}. Using default: {self.mouse_mode}{RESET_TEXT}")
                self.issues += 1

            # !!! MAC Address !!!#
            configMacAddress = section.get("mac_address", self.mac_address)
            if(configMacAddress and len(configMacAddress) >= 12 and len(configMacAddress) <= 17 and all(c in "0123456789ABCDEF:-" for c in configMacAddress.upper())): # Valid MAC address format like AABBCCDDEEFF
                configMacAddress = configMacAddress.replace(":", "")
                configMacAddress = configMacAddress.replace("-", "")
                self.mac_address = bytes.fromhex(configMacAddress)[::-1] # Convert mac to little-endian format
            else:
                print(f"{RED_TEXT}Invalid MAC address in {self._config_path}. Using default: {self.mac_address}{RESET_TEXT}")
                self.issues += 1

            issues_msg = f"{YELLOW_TEXT}{BOLD_TEXT}{self.issues} issue(s) found." if self.issues != 0 else ""
            print(f"{GREEN_TEXT}Configuration loaded ! {issues_msg}{RESET_TEXT}")

        else:
            print(f"{RED_TEXT}Section 'Controller' not found in {self._config_path}. Using default values.{RESET_TEXT}")
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