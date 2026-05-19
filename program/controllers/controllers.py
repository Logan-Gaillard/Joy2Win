from bleak import BleakClient
from program.ControllerCommands import ControllerCommands

class BaseController:
    hid_report_handle = 0x000A - 1
    command_handle = 0x0014 - 1
    response_command_handle = 0x001A - 1

    def __init__(self, device: BleakClient):
        self.device = device
        self.controller_client = BleakClient(self.device)
        self.commands = ControllerCommands(self)

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

    async def init_and_pairing(self):
        await self.start_notify()

        result = await self.commands.send_command_and_wait_response("SET_LED", {"led_mask": format(int("0101", 2), '02x')})
        print(f"result: {result.hex()}")

        # Paring process
        #controllerAddrs = await self.commands.send_command_and_wait_response("JOY2_SAVE_MC_ADDR_STEP1", {"mac-addr1": "001122334455", "mac-addr2": "66778899AABB"})
        #print(f"Controller addresses: {controllerAddrs.hex()}")

    def notification_handler(self, _, data):
        print(f"Notification: {data.hex()}")
        pass

    def update_datas(self):
        pass