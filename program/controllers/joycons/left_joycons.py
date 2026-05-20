from program.controllers.controllers import BaseController
from bleak import BleakClient

class LeftJoyCon(BaseController):

    def __init__(self, device: BleakClient):
        super().__init__(device)

    def update_datas(self, data):
        if self.hid_report_handle == 0x000A - 1:
            super().update_datas(data)
        else:
            print("Updating Left Joy-Con data...")