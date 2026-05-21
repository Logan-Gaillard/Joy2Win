from program.driver_controllers.DriverController import DriverController

class CustomController(DriverController):
    def __init__(self, controller: DriverController):
        super().__init__(controller)

    def notify_update(self):
        mouse_enabled = self.mouse_interract()
        #clear console
        print("\033c", end="")
        print(f"Updating Custom Controller : {self.controller.to_controller_format()}")