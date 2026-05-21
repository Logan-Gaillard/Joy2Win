from bleak import BleakClient
from program.ControllerCommands import ControllerCommands
from program.config import Config
import platform, struct, random
from program.driver_controllers.vgamepad.DS4Controller import DS4Controller
from program.driver_controllers.vgamepad.XboxController import XboxController
from program.driver_controllers.pyvjoy import CustomController
from program.constant import RED_TEXT, GREEN_TEXT, YELLOW_TEXT, RESET_TEXT, BOLD_TEXT

class BaseController:
    hid_report_handle = 0x000A - 1
    command_handle = 0x0014 - 1
    response_command_handle = 0x001A - 1

    button_format = [
        {"button": "Y", "data": 0x01, "byte": 0},
        {"button": "X", "data": 0x02, "byte": 0},
        {"button": "B", "data": 0x04, "byte": 0},
        {"button": "A", "data": 0x08, "byte": 0},
        {"button": "SR_RIGHT", "data": 0x10, "byte": 0},
        {"button": "SL_RIGHT", "data": 0x20, "byte": 0},
        {"button": "R", "data": 0x40, "byte": 0},
        {"button": "ZR", "data": 0x80, "byte": 0},

        {"button": "Minus", "data": 0x01, "byte": 1},
        {"button": "Plus", "data": 0x02, "byte": 1},
        {"button": "R_STICK", "data": 0x04, "byte": 1},
        {"button": "L_STICK", "data": 0x08, "byte": 1},
        {"button": "HOME", "data": 0x10, "byte": 1},
        {"button": "CAPTURE", "data": 0x20, "byte": 1},
        {"button": "C", "data": 0x40, "byte": 1},

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
        self.device = device
        self.controller_client = BleakClient(self.device)
        self.commands = ControllerCommands(self)
        self.config = Config().getConfig()
        self.driver_controller = None
        self.controller_id = random.randint(10000, 99999)

        self.mouse_buttons_watch = {
            "LEFT": None,
            "RIGHT": None,
            "MIDDLE": None,
            "SCROLL": None,
        }

        if self.config["controller_driver"] in ["XBOX", "DS4", "CUSTOM"]:
            self.controller_client_type = self.config["controller_driver"]
            if self.config["controller_driver"] == "XBOX":
                self.driver_controller = XboxController(self)
            elif self.config["controller_driver"] == "DS4":
                self.driver_controller = DS4Controller(self)
            elif self.config["controller_driver"] == "CUSTOM":
                self.driver_controller = CustomController(self)
            else:
                print(f"{RED_TEXT}Invalid controller_driver value in config. Using default: XBOX{RESET_TEXT}")

        self.pressed_buttons = []

        self.left_stick = {
            "x": 0,
            "y": 0
        }

        self.right_stick = {
            "x": 0,
            "y": 0
        }

        self.mouse = {
            "x_pos": 0,
            "y_pos": 0,
            "x_delta": 0,
            "y_delta": 0,
            "surface_quality": 0,
            "distance": 0
        }

        self.magnetometer = {
            "x": 0,
            "y": 0,
            "z": 0
        }

        self.motion = {
            "timestamp": 0,
            "temperature": 0,
            "accel_x": 0,
            "accel_y": 0,
            "accel_z": 0,
            "gyro_x": 0,
            "gyro_y": 0,
            "gyro_z": 0
        }

        self.battery = {
            "voltage": 0,
            "current": 0
        }

    async def connect(self):
        await self.controller_client.connect()
        if self.controller_client.is_connected:
            print(f"Connected to {self.device.address}")
        else:
            print("Failed to connect.")
    
    async def disconnect(self):
        await self.controller_client.disconnect()
        if not self.controller_client.is_connected:
            print(f"Disconnected from {self.device.address}")
        else:
            print("Failed to disconnect.")
        
    async def start_notify(self):
        await self.controller_client.start_notify(self.hid_report_handle, self.notification_handler)
        await self.controller_client.start_notify(self.response_command_handle, self.commands.receive_response)

    async def init_and_ready(self):
        # Initial feature with button, analog sticks and rumble
        feature_flags = 0b00100011

        if self.config["enable_dsu"]:
            # adding IMU and Magnometer feature flags
            feature_flags |= 0b10000100
        
        if self.config["mouse_mode"] in [1,2]:
            # adding mouse data feature flag
            feature_flags |= 0b00010000

        await self.start_notify()
    
        await self.commands.send_command_and_wait_response("SET_FEATURE", {"flags": feature_flags})
        await self.commands.send_command_and_wait_response("ENABLE_FEATURE", {"flags": feature_flags})

        # Set led with configuration
        led_mask = int(self.config["led_player"])
        print(f"Setting LED mask to: {led_mask}")
        await self.commands.send_command_and_wait_response("SET_LED", {"led_mask": led_mask})

        # Play connected and ready vibration sample
        await self.commands.send_command_and_wait_response("PLAY_VIBRATION_SAMPLE", {"id": 0x05})

        response_primary_stick_calibration = await self.commands.send_command_and_wait_response("READ_DATA", {"size": 0x0B, "address": 0x001FC040})

        print(f"Primary stick calibration data: {response_primary_stick_calibration.hex()}")

        if platform.system() == 'Windows':
            version = platform.version()
            build_number = int(version.split('.')[-1])
            if build_number >= 22000:
                from bleak.backends.winrt.client import BleakClientWinRT
                from winrt.windows.devices.bluetooth import BluetoothLEPreferredConnectionParameters
                backend = self.controller_client._backend
                if isinstance(backend, BleakClientWinRT):
                    backend._requester.request_preferred_connection_parameters(BluetoothLEPreferredConnectionParameters.throughput_optimized)

    def notification_handler(self, _, data):
        self.update_datas(data)

        if self.driver_controller != None:
            self.driver_controller.notify_update()
        
    def update_datas(self, data):
        report_counter = struct.unpack('<I', data[0x0 : 0x4])[0]

        buttons = data[0x4 : 0x4 + 0x4]
        left_stick = data[0xA : 0xA + 0x3]
        right_stick = data[0xD : 0xD + 0x3]

        mouse = data[0x10 : 0x10 + 0x8]

        magnetometer = data[0x19 : 0x19 + 0x6]

        volt_battery = struct.unpack('<H', data[0x1F : 0x1F + 0x2])[0]
        current_battery = struct.unpack('<H', data[0x22 : 0x22 + 0x2])[0] # IDK is it

        motion = data[0x2A : 0x2A + 0x12]

        for button in self.button_format:
            if buttons[button["byte"]] & button["data"]:
                if button["button"] not in self.pressed_buttons:
                    self.pressed_buttons.append(button["button"])
            else:
                if button["button"] in self.pressed_buttons:
                    self.pressed_buttons.remove(button["button"])

        # TODO : Read SPI and include saved calibrations
        self.left_stick = {
            "x": ((left_stick[1] & 0x0F) << 8) | left_stick[0],
            "y": (left_stick[2] << 4) | ((left_stick[1] & 0xF0) >> 4)
        }

        # TODO : Read SPI and include saved calibrations
        self.right_stick = {
            "x": ((right_stick[1] & 0x0F) << 8) | right_stick[0],
            "y": (right_stick[2] << 4) | ((right_stick[1] & 0xF0) >> 4)
        }
        
        mouse_pos = {
            "x": struct.unpack('<h', mouse[0x0: 0x0 + 0x2])[0],
            "y": struct.unpack('<h', mouse[0x2: 0x2 + 0x2])[0]
        }

        self.mouse = {
            "x_delta": ((mouse_pos["x"] - self.mouse["x_pos"] + 32768) % int.from_bytes(b'\xff\xff', 'big')) - 32768,
            "y_delta": ((mouse_pos["y"] - self.mouse["y_pos"] + 32768) % int.from_bytes(b'\xff\xff', 'big')) - 32768,
            "x_pos": mouse_pos["x"],
            "y_pos": mouse_pos["y"],
            "surface_quality": struct.unpack('<h', mouse[0x4: 0x4 + 0x2])[0],
            "distance": struct.unpack('<h', mouse[0x6: 0x6 + 0x2])[0],
        }

        self.magnetometer = {
            "x": struct.unpack('<h', magnetometer[0x0: 0x0 + 0x2])[0],
            "y": struct.unpack('<h', magnetometer[0x2: 0x2 + 0x2])[0],
            "z": struct.unpack('<h', magnetometer[0x4: 0x4 + 0x2])[0]
        }

        self.motion = {
            "timestamp": struct.unpack('<I', motion[0x0: 0x0 + 0x4])[0],
            "temperature": struct.unpack('<h', motion[0x4: 0x4 + 0x2])[0],
            "accel_x": struct.unpack('<h', motion[0x6: 0x6 + 0x2])[0],
            "accel_y": struct.unpack('<h', motion[0x8: 0x8 + 0x2])[0],
            "accel_z": struct.unpack('<h', motion[0xA: 0xA + 0x2])[0],
            "gyro_x": struct.unpack('<h', motion[0xC: 0xC + 0x2])[0],
            "gyro_y": struct.unpack('<h', motion[0xE: 0xE + 0x2])[0],
            "gyro_z": struct.unpack('<h', motion[0x10: 0x10 + 0x2])[0]
        }

        self.battery = {
            "voltage": volt_battery,
            "current": current_battery
        }

    def to_controller_format(self):
        pass