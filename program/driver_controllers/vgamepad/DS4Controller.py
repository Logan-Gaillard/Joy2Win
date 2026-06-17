from program.driver_controllers.DriverController import DriverController
import vgamepad as vg

class DS4Controller(DriverController):
    def __init__(self, controller: DriverController):
        super().__init__(controller)

        if DriverController.driver is None:
            DriverController.driver = vg.VDS4Gamepad()

    def set_input(self):
        pressed_controller_button = self.controller.to_controller_format()["buttons"]
        pressed_driver_button = DriverController.pressed_buttons
        driver_dictionnary = self.controller.get_dictionnary_driver()

        if DriverController.driver is not None:
            for dict_buttons, vgamepad_button in driver_dictionnary.items():
                vgamepad_button = vgamepad_button.get("ds4")
                isPressedController = dict_buttons in pressed_controller_button
                isPressedDriver = dict_buttons in pressed_driver_button

                if isinstance(vgamepad_button, vg.DS4_SPECIAL_BUTTONS):
                    if isPressedController and not isPressedDriver:
                        DriverController.driver.press_special_button(vgamepad_button)
                        DriverController.pressed_buttons.append(dict_buttons)
                    elif not isPressedController and isPressedDriver:
                        DriverController.driver.release_special_button(vgamepad_button)
                        DriverController.pressed_buttons.remove(dict_buttons)

                if isinstance(vgamepad_button, vg.DS4_BUTTONS):
                    if isPressedController and not isPressedDriver:
                        DriverController.driver.press_button(vgamepad_button)
                        DriverController.pressed_buttons.append(dict_buttons)
                    elif not isPressedController and isPressedDriver:
                        DriverController.driver.release_button(vgamepad_button)
                        DriverController.pressed_buttons.remove(dict_buttons)

                elif isinstance(vgamepad_button, vg.DS4_DPAD_DIRECTIONS):
                    if isPressedController and not isPressedDriver:
                        DriverController.driver.directional_pad(vgamepad_button)
                        DriverController.pressed_buttons.append(dict_buttons)
                    elif not isPressedController and isPressedDriver:
                        DriverController.driver.directional_pad(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
                        DriverController.pressed_buttons.remove(dict_buttons)

                elif isinstance(vgamepad_button, str):
                    if vgamepad_button == "ZR":
                        if isPressedController and not isPressedDriver:
                            DriverController.driver.right_trigger(255)
                            DriverController.pressed_buttons.append(dict_buttons)
                        elif not isPressedController and isPressedDriver:
                            DriverController.driver.right_trigger(0)
                            DriverController.pressed_buttons.remove(dict_buttons)
                    elif vgamepad_button == "ZL":
                        if isPressedController and not isPressedDriver:
                            DriverController.driver.left_trigger(255)
                            DriverController.pressed_buttons.append(dict_buttons)
                        elif not isPressedController and isPressedDriver:
                            DriverController.driver.left_trigger(0)
                            DriverController.pressed_buttons.remove(dict_buttons)

            DriverController.driver.update()

    def set_sticks(self):
        controller_stick = self.controller.to_controller_format()["sticks"]["primary"]

        from program.controllers.joycons.left_joycons import LeftJoyCon
        from program.controllers.joycons.right_joycons import RightJoyCon
        if isinstance(self.controller, LeftJoyCon):
                DriverController.driver.left_joystick_float(controller_stick["x"], -controller_stick["y"])
        elif isinstance(self.controller, RightJoyCon):
            if self.controller.isAlone:
                DriverController.driver.left_joystick_float(controller_stick["x"], -controller_stick["y"])
            else:
                DriverController.driver.right_joystick_float(controller_stick["x"], -controller_stick["y"])

        DriverController.driver.update()

    def notify_update(self):
        mouse_enabled = self.mouse_interract()

        if not mouse_enabled:
            self.set_input()
            self.set_sticks()