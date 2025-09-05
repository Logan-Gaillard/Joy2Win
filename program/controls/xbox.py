from pyvjoystick import vigem as vg
gamepad = vg.VX360Gamepad()

FullControls = {
    "Left": {
        "ZL": None, "L": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, "Minus": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, "SLL": None,
        "SRL": None, "Capture": None,
    },
    "Right": {
        "ZR": None, "R": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A, "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B, "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, "Plus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START, "SRR": None,
        "SLR": None, "Home": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, "GameChat": None,
    }
}

def xbox_control(controller, side, nbController = 2):
    for btnName, btnValue in FullControls[side].items():
        if btnValue is None:
            continue
        if controller.buttons.get(btnName, False):
            gamepad.press_button(btnValue)
        else:
            gamepad.release_button(btnValue)
        


    gamepad.update()
    
