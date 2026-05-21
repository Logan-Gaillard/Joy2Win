from program.controllers.controllers import BaseController
from bleak import BleakClient

class RightJoyCon(BaseController):

    def __init__(self, device: BleakClient):
        super().__init__(device)

        self.mouse_buttons_watch = {
            "LEFT": "R",
            "RIGHT": "ZR",
            "MIDDLE": "R_STICK",
            "SCROLL": "right_stick",
        }

    def update_datas(self, data):
        if self.hid_report_handle == 0x000A - 1:
            super().update_datas(data)
        else:
            print("Updating Right Joy-Con data...")

    def to_controller_format(self):
        return {
            "buttons": self.pressed_buttons,
            "right_stick": self.right_stick,
            "mouse": self.mouse,
            "magnetometer": self.magnetometer,
            "motion": self.motion,
            "battery": self.battery
        }