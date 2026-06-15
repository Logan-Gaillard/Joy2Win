from program.controllers.controllers import BaseController
from bleak import BleakClient
import vgamepad as vg
class RightJoyCon(BaseController):
    
    mouse_buttons_watch = {
        "LEFT": "R",
        "RIGHT": "ZR",
        "MIDDLE": "R_STICK",
    }

    button_format = [
        {"button": "Y", "data": 0x01, "byte": 0},
        {"button": "X", "data": 0x02, "byte": 0},
        {"button": "B", "data": 0x04, "byte": 0},
        {"button": "A", "data": 0x08, "byte": 0},
        {"button": "SR_RIGHT", "data": 0x10, "byte": 0},
        {"button": "SL_RIGHT", "data": 0x20, "byte": 0},
        {"button": "R", "data": 0x40, "byte": 0},
        {"button": "ZR", "data": 0x80, "byte": 0},
        {"button": "Plus", "data": 0x02, "byte": 1},
        {"button": "R_STICK", "data": 0x04, "byte": 1},
        {"button": "HOME", "data": 0x10, "byte": 1},
        {"button": "C", "data": 0x40, "byte": 1},
    ]

    def __init__(self, device: BleakClient):
        super().__init__(device)

    def update_datas(self, data):
        if self.hid_report_handle == 0x000A - 1:
            super().update_datas(data)
        else:
            print("Updating Right Joy-Con data...")

        if self.controller_orientation == "HORIZONTAL":
            temp_x = self.right_stick["x"]
            temp_y = self.right_stick["y"]
            self.right_stick["x"] = temp_y
            self.right_stick["y"] = -temp_x

    def to_controller_format(self):
        return {
            "buttons": self.pressed_buttons,
            "sticks": {
                "primary": self.right_stick,
                "secondary": None,
            },
            "mouse": self.mouse,
            "magnetometer": self.magnetometer,
            "motion": self.motion,
            "battery": self.battery
        }
    
    def get_dictionnary_driver(self):
        if self.config["controller_driver"] == "CUSTOM":
            return {
                "Y": 12,
                "X": 13,
                "B": 14,
                "A": 15,
                "SR_RIGHT": 16,
                "SL_RIGHT": 17,
                "R": 18,
                "ZR": 19,
                "Plus": 20,
                "R_STICK": 21,
                "HOME": 22,
                "C": 23
            }

        if not self.isAlone:
            return {
                "A": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
                },
                "B": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CROSS
                },
                "X": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
                },
                "Y": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
                },
                "R": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
                },
                "Plus": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
                },
                "R_STICK": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT
                },
                "HOME": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
                    "ds4": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS
                },
                "ZR": {
                    "xbox": "ZR",
                    "ds4": "ZR"
                },
                "C": {
                    "xbox": None,
                    "ds4": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
                },
            }
        else:
            if self.controller_orientation == "HORIZONTAL":
                return {
                    "A": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CROSS
                    },
                    "B": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
                    },
                    "Y": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
                    },
                    "X": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
                    },
                    "SL_RIGHT": {
                        "xbox": "ZL",
                        "ds4": "ZL"
                    },
                    "SR_RIGHT": {
                        "xbox": "ZR",
                        "ds4": "ZR"
                    },
                    "HOME": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
                        "ds4": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS
                    },
                    "Plus": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
                    },
                    "C": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHARE
                    },
                    "R_STICK": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT
                    },
                    "R": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
                    },
                    "ZR": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
                    }
                }
            else:
                return {
                    "A": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
                    },
                    "B": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CROSS
                    },
                    "X": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
                    },
                    "Y": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
                    },
                    "R": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
                    },
                    "Plus": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
                    },
                    "R_STICK": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT
                    },
                    "HOME": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
                        "ds4": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS
                    },
                    "ZR": {
                        "xbox": "ZR",
                        "ds4": "ZR"
                    },
                    "C": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHARE
                    },
                    "SL_RIGHT": {
                        "xbox": "ZL",
                        "ds4": "ZL"
                    },
                    "SR_RIGHT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
                    },
                }
            
    async def init_and_ready(self):
        await super().init_and_ready()

        response_primary_stick_calibration = await self.commands.send_command_and_wait_response("READ_DATA", {"size": 0x09, "address": 0xA8300100})
        calibration_data = self.unpack_12bit_sequence(response_primary_stick_calibration[0x10::])

        self.sticks_options.x_axis.center = calibration_data[0]
        self.sticks_options.y_axis.center = calibration_data[1]
        self.sticks_options.x_axis.max = calibration_data[0] + calibration_data[2]
        self.sticks_options.y_axis.max = calibration_data[1] + calibration_data[3]
        self.sticks_options.x_axis.min = calibration_data[0] - calibration_data[4]
        self.sticks_options.y_axis.min = calibration_data[1] - calibration_data[5]

        # print(f"Primary stick calibration data: {response_primary_stick_calibration.hex()}")
        # print(f"Primary stick calibration: {self.sticks_options.x_axis.min} {self.sticks_options.x_axis.center} {self.sticks_options.x_axis.max} | {self.sticks_options.y_axis.min} {self.sticks_options.y_axis.center} {self.sticks_options.y_axis.max}")