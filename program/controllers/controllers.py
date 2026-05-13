from bleak import BleakClient

class BaseController:
    hid_report_handle = 0x000A - 1

    def __init__(self, device: BleakClient):
        self.device = device
        self.controller_client = BleakClient(self.device)

    async def connect(self):
        await self.controller_client.connect()
        if self.controller_client.is_connected:
            print(f"Connected to {self.device.address}")
        else:
            print("Failed to connect.")
        
    async def start_notify(self):
        await self.controller_client.start_notify(self.hid_report_handle, self.notification_handler)

    def notification_handler(self, _, data):
        print(f"Notification: {data.hex()}")
        pass

    def update_datas(self):
        pass