from program.controllers.controllers import BaseController
from bleak import BleakClient

class LeftJoyCon(BaseController):

    def __init__(self, device: BleakClient):
        super().__init__(device)

        self.mouse_buttons_watch = {
            "LEFT": "L",
            "RIGHT": "ZL",
            "MIDDLE": "L_STICK",
            "SCROLL": "left_stick",
        }

    def update_datas(self, data):
        if self.hid_report_handle == 0x000A - 1:
            super().update_datas(data)
        else:
            print("Updating Left Joy-Con data...")

    def to_controller_format(self):
        return {
            "buttons": self.pressed_buttons,
            "left_stick": self.left_stick,
            "mouse": self.mouse,
            "magnetometer": self.magnetometer,
            "motion": self.motion,
            "battery": self.battery
        }