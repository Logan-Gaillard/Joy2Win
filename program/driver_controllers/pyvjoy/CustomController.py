from program.driver_controllers.DriverController import DriverController
import pyvjoy

class CustomController(DriverController):
    def __init__(self, controller: DriverController):
        super().__init__(controller)

        if DriverController.driver is None:
            DriverController.driver = pyvjoy.VJoyDevice(1)

    def set_input(self):
        pressed_controller_button = self.controller.to_controller_format()["buttons"]
        pressed_driver_button = DriverController.pressed_buttons
        driver_dictionnary = self.controller.get_dictionnary_driver()

        for dict_buttons, input_button in driver_dictionnary.items():
            isPressedController = dict_buttons in pressed_controller_button
            isPressedDriver = dict_buttons in pressed_driver_button

            if isPressedController and not isPressedDriver:
                DriverController.driver.set_button(input_button, 1)
                DriverController.pressed_buttons.append(dict_buttons)
            elif not isPressedController and isPressedDriver:
                DriverController.driver.set_button(input_button, 0)
                DriverController.pressed_buttons.remove(dict_buttons)

    def set_sticks(self):
        controller_stick = self.controller.to_controller_format()["sticks"]["primary"]

        from program.controllers.joycons.left_joycons import LeftJoyCon
        from program.controllers.joycons.right_joycons import RightJoyCon

        # Convert float range (-1.0 to 1.0) to vJoy range (0x0000 to 0x8000)
        val_x = int(0x4000 * (controller_stick["x"] + 1))
        val_y = int(0x4000 * (-controller_stick["y"] + 1))

        if isinstance(self.controller, LeftJoyCon):
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_X, val_x)
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_Y, val_y)
        elif isinstance(self.controller, RightJoyCon):
            if self.controller.isAlone:
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_X, val_x)
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_Y, val_y)
            else:
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_RX, val_x)
                DriverController.driver.set_axis(pyvjoy.HID_USAGE_RY, val_y)

    def notify_update(self):
        mouse_enabled = self.mouse_interract()

        if not mouse_enabled:
            self.set_input()
            self.set_sticks()