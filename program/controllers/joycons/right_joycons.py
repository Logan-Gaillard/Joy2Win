from program.controllers.controllers import BaseController
from bleak import BleakClient

class RightJoyCon(BaseController):

    def __init__(self, device: BleakClient):
        super().__init__(device)

    def notification_handler(self, _, data):
        print(f"Right Joy-Con Notification: {data.hex()}")

    def update_datas(self):
        print("Updating Right Joy-Con data...")