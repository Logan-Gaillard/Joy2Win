import configparser
import os

class Config:
    _instance = None
    _defaults = {
        "controller": 0,
        "orientation": 0,
        "led_player": 0b0001,
        "auto_connect": False,
        "enable_dsu": False,
        "mouse_mode": 0,
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
            self.controller = int(section.get("controller", self.controller))
            self.orientation = int(section.get("orientation", self.orientation))
            self.led_player = str(section.get("led_player", self.led_player))
            self.auto_connect = section.get("auto_connect", str(self.auto_connect)).lower() == '1'
            self.enable_dsu = section.get("enable_dsu", str(self.enable_dsu)).lower() == '1'
            self.mouse_mode = int(section.get("mouse_mode", self.mouse_mode if self.mouse_mode == 0 or self.mouse_mode == 1 or self.mouse_mode == 2 else 0))
        else:
            print("No 'Controller' section found in config.ini, please follow the example in config-example.ini file.")

    def getConfig(self):
        return {
            "controller": self.controller,
            "orientation": self.orientation,
            "led_player": self.led_player,
            "auto_connect": self.auto_connect,
            "enable_dsu": self.enable_dsu,
            "mouse_mode": self.mouse_mode
        }