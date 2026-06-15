from typing import TYPE_CHECKING
from pynput.mouse import Controller, Button
from program.config import Config

if TYPE_CHECKING:
    from program.controllers.controllers import BaseController

class DriverController:
    mouse_enabled_by = None
    pressed_buttons = []

    driver = None
    
    def __init__(self, controller: BaseController):
        self.controller = controller
        self.config = Config().getConfig()

        if self.config["mouse_mode"] != 0:
            self.mouse = Controller()
            self.pressed_mouse_buttons = set()
        
    def notify_update(self):
        pass

    def mouse_interract(self):
        mouse_data = self.controller.to_controller_format()["mouse"]
        button_data = self.controller.to_controller_format()["buttons"]
        button_mapping = self.controller.mouse_buttons_watch
        stick_data = self.controller.to_controller_format()["sticks"]["primary"]
        mouse_mode = self.config["mouse_mode"]

        if mouse_data and (DriverController.mouse_enabled_by == None or DriverController.mouse_enabled_by == self.controller.controller_id):
            if mouse_mode == 1:
                mouse_distance = mouse_data["distance"]
                if mouse_distance < 1000:
                    DriverController.mouse_enabled_by = self.controller.controller_id
                else:
                    DriverController.mouse_enabled_by = None
            elif mouse_mode == 2:
                DriverController.mouse_enabled_by = self.controller.controller_id
            else: DriverController.mouse_enabled_by = None

            if DriverController.mouse_enabled_by != None:
                self.mouse.move(mouse_data["x_delta"], mouse_data["y_delta"])

                if button_mapping["LEFT"] in button_data:
                    if "LEFT" not in self.pressed_mouse_buttons:
                        self.mouse.press(Button.left)
                        self.pressed_mouse_buttons.add("LEFT")
                elif "LEFT" in self.pressed_mouse_buttons:
                    self.mouse.release(Button.left)
                    self.pressed_mouse_buttons.discard("LEFT")

                if button_mapping["RIGHT"] in button_data:
                    if "RIGHT" not in self.pressed_mouse_buttons:
                        self.mouse.press(Button.right)
                        self.pressed_mouse_buttons.add("RIGHT")
                elif "RIGHT" in self.pressed_mouse_buttons:
                    self.mouse.release(Button.right)
                    self.pressed_mouse_buttons.discard("RIGHT")

                if button_mapping["MIDDLE"] in button_data:
                    if "MIDDLE" not in self.pressed_mouse_buttons:
                        self.mouse.press(Button.middle)
                        self.pressed_mouse_buttons.add("MIDDLE")
                elif "MIDDLE" in self.pressed_mouse_buttons:
                    self.mouse.release(Button.middle)
                    self.pressed_mouse_buttons.discard("MIDDLE")

                if stick_data:
                    scroll_x = stick_data["raw-x"] / 2
                    scroll_y = stick_data["raw-y"] / 2
                    self.mouse.scroll(scroll_x, scroll_y)

        return (DriverController.mouse_enabled_by == self.controller.controller_id)