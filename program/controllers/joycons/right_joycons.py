from controllers.controllers import BaseController

class RightJoyCon(BaseController):
    hid_report_handle = (0x000E) - 1

    def notification_handler(self, _, data):
        print(f"Right Joy-Con Notification: {data.hex()}")