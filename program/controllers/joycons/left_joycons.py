from program.controllers.controllers import BaseController
from bleak import BleakClient
import vgamepad as vg

class LeftJoyCon(BaseController):

    mouse_buttons_watch = {
        "LEFT": "L",
        "RIGHT": "ZL",
        "MIDDLE": "L_STICK",
    }

    button_format = [
        {"button": "Minus", "data": 0x01, "byte": 1},
        {"button": "L_STICK", "data": 0x08, "byte": 1},
        {"button": "CAPTURE", "data": 0x20, "byte": 1},
        {"button": "DPAD_DOWN", "data": 0x01, "byte": 2},
        {"button": "DPAD_UP", "data": 0x02, "byte": 2},
        {"button": "DPAD_RIGHT", "data": 0x04, "byte": 2},
        {"button": "DPAD_LEFT", "data": 0x08, "byte": 2},
        {"button": "SR_LEFT", "data": 0x10, "byte": 2},
        {"button": "SL_LEFT", "data": 0x20, "byte": 2},
        {"button": "L", "data": 0x40, "byte": 2},
        {"button": "ZL", "data": 0x80, "byte": 2}
    ]

    def __init__(self, device: BleakClient):
        super().__init__(device)

    def update_datas(self, data):
        if self.hid_report_handle == 0x000A - 1:
            super().update_datas(data)
        else:
            print("Updating Left Joy-Con data...")
            
        if self.controller_orientation == "HORIZONTAL":
            temp_x = self.left_stick["x"]
            temp_y = self.left_stick["y"]
            self.left_stick["x"] = -temp_y
            self.left_stick["y"] = temp_x

    def to_controller_format(self):
        return {
            "buttons": self.pressed_buttons,
            "sticks": {
                "primary": self.left_stick,
                "secondary": None
            },
            "mouse": self.mouse,
            "magnetometer": self.magnetometer,
            "motion": self.motion,
            "battery": self.battery
        }
    
    def get_dictionnary_driver(self):
        if self.config["controller_driver"] == "CUSTOM":
            return {
                "Minus": 1,
                "L_STICK": 2,
                "CAPTURE": 3,
                "DPAD_DOWN": 4,
                "DPAD_UP": 5,
                "DPAD_RIGHT": 6,
                "DPAD_LEFT": 7,
                "SR_LEFT": 8,
                "SL_LEFT": 9,
                "L": 10,
                "ZL": 11
            }

        if not self.isAlone:
            return {
                "DPAD_RIGHT": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                    "ds4": vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
                },
                "DPAD_LEFT": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                    "ds4": vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST
                },
                "DPAD_UP": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                    "ds4": vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH
                },
                "DPAD_DOWN": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                    "ds4": vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH
                },
                "L": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
                },
                "Minus": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHARE
                },
                "L_STICK": {
                    "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                    "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT
                },
                "ZL": {
                    "xbox": "ZL",
                    "ds4": "ZL"
                },
                "CAPTURE": {
                    "xbox": None,
                    "ds4": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
                },
            }
        else:
            if self.controller_orientation == "HORIZONTAL":
                return {
                    "DPAD_RIGHT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
                    },
                    "DPAD_UP": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
                    },
                    "DPAD_LEFT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CROSS
                    },
                    "DPAD_DOWN": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
                    },
                    "SL_LEFT": {
                        "xbox": "ZL",
                        "ds4": "ZL"
                    },
                    "SR_LEFT": {
                        "xbox": "ZR",
                        "ds4": "ZR"
                    },
                    "CAPTURE": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHARE
                    },
                    "Minus": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
                    },
                    "L_STICK": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT
                    },
                    "L": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
                    },
                    "ZL": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
                    }
                }
            else:
                return {
                    "DPAD_RIGHT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
                    },
                    "DPAD_DOWN": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_CROSS
                    },
                    "DPAD_UP": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
                    },
                    "DPAD_LEFT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
                    },
                    "L": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
                    },
                    "Minus": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
                    },
                    "L_STICK": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT
                    },
                    "CAPTURE": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHARE
                    },
                    "ZL": {
                        "xbox": "ZL",
                        "ds4": "ZL"
                    },
                    "SL_LEFT": {
                        "xbox": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                        "ds4": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
                    },
                    "SR_LEFT": {
                        "xbox": "ZR",
                        "ds4": "ZR"
                    }
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