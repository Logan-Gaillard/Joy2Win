from bleak import BleakClient

class BaseController:
    hid_report_handle = None

    def __init__(self, device: BleakClient, config):
        self.device = device
        

    def notification_handler(self, _, data):
        print(f"Notification: {data.hex()}")
        pass
