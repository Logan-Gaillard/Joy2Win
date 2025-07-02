from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight
from pyvjoystick import vigem as vg

joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

gamepad = vg.VX360Gamepad()

Controls = {
    "Left": {
        "L": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "Minus": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    },
    "Right": {
        "R": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "Plus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        "Home": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    }
}

def check_control(side):
    for btnName, btnValue in Controls[side].items():
        if joyconLeft.buttons.get(btnName, False) or joyconRight.buttons.get(btnName, False):
            gamepad.press_button(btnValue)
        else:
            gamepad.release_button(btnValue)

        if(side == "Left"):
            gamepad.left_joystick(joyconLeft.analog_stick["X"], joyconLeft.analog_stick["Y"])
            gamepad.left_trigger(255 if joyconLeft.buttons["ZL"] else 0)
        elif(side == "Right"):
            gamepad.right_joystick(joyconRight.analog_stick["X"], joyconRight.analog_stick["Y"])
            gamepad.right_trigger(255 if joyconRight.buttons["ZR"] else 0)

def notify_duo_joycons(client, side, data):
    if side == "Left":
        joyconLeft.update(data)
    elif side == "Right":
        joyconRight.update(data)
    else:
        print("Unknown controller side.")

    check_control(side)
    
    gamepad.update()
    
    return client