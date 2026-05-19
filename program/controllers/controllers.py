from bleak import BleakClient
from program.ControllerCommands import ControllerCommands
from program.config import Config
import platform

class BaseController:
    hid_report_handle = 0x000A - 1
    command_handle = 0x0014 - 1
    response_command_handle = 0x001A - 1

    def __init__(self, device: BleakClient):
        self.device = device
        self.controller_client = BleakClient(self.device)
        self.commands = ControllerCommands(self)
        self.config = Config().getConfig()

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
    
        await self.commands.send_command_and_wait_response("SET_FEATURE", {"flags": f"{feature_flags:02x}"})
        await self.commands.send_command_and_wait_response("ENABLE_FEATURE", {"flags": f"{feature_flags:02x}"})

        # Set led with configuration
        led_mask = int(self.config["led_player"], 10)
        print(f"Setting LED mask to: {led_mask}")
        await self.commands.send_command_and_wait_response("SET_LED", {"led_mask": f"{led_mask:02x}"})

        if platform.system() == 'Windows':
            version = platform.version()
            build_number = int(version.split('.')[-1])
            if build_number >= 22000:
                from bleak.backends.winrt.client import BleakClientWinRT
                from winrt.windows.devices.bluetooth import BluetoothLEPreferredConnectionParameters
                backend = self.controller_client._backend
                if isinstance(backend, BleakClientWinRT):
                    backend._requester.request_preferred_connection_parameters(BluetoothLEPreferredConnectionParameters.throughput_optimized)

        # Play connected and ready vibration sample
        await self.commands.send_command_and_wait_response("PLAY_VIBRATION_SAMPLE", {"id": "05"})

    def notification_handler(self, _, data):
        print(f"Notification: {data.hex()}")
        pass

    def update_datas(self):
        pass