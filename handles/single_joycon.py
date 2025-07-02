from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight
from pyvjoystick import vigem as vg

joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

gamepad = vg.VX360Gamepad()

Controls = {
    "Left": {
        "0": { #The orientation of the Joy-Con is vertical
            "L": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "Minus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "SL": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "Capture": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        },
        "1": { #The orientation of the Joy-Con is horizontal
            "SL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "SR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "Minus": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "Capture": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            
        },
    },
    "Right": {
        "0": { #The orientation of the Joy-Con is vertical
            "R": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "Plus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "Home": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            "SL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "GameChat": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,

        },
        "1": { #The orientation of the Joy-Con is horizontal
            "SL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "SR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "Plus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "Home": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "GameChat": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        },
    }
}

def check_control(side, orientation):
    for btnName, btnValue in Controls[side][str(orientation)].items():
        if joyconLeft.buttons.get(btnName, False) or joyconRight.buttons.get(btnName, False):
            gamepad.press_button(btnValue)
        else:
            gamepad.release_button(btnValue)

        if(side == "Left"):
            gamepad.left_joystick(joyconLeft.analog_stick["X"], joyconLeft.analog_stick["Y"])
            if orientation == 0:
                gamepad.left_trigger(255 if joyconLeft.buttons["ZL"] else 0)
                gamepad.right_trigger(255 if joyconLeft.buttons["SR"] else 0)
            elif orientation == 1:
                gamepad.left_trigger(255 if joyconLeft.buttons["ZL"] else 0)
                gamepad.right_trigger(255 if joyconLeft.buttons["L"] else 0)
        elif(side == "Right"):
            gamepad.right_joystick(joyconRight.analog_stick["X"], joyconRight.analog_stick["Y"])
            if orientation == 0:
                gamepad.left_trigger(255 if joyconRight.buttons["SR"] else 0)
                gamepad.right_trigger(255 if joyconRight.buttons["ZR"] else 0)
            elif orientation == 1:
                gamepad.left_trigger(255 if joyconRight.buttons["R"] else 0)
                gamepad.right_trigger(255 if joyconRight.buttons["ZR"] else 0)

def notify_duo_joycons(client, side, orientation, data):
    if side == "Left":
        if joyconLeft.orientation != orientation:
            joyconLeft.orientation = orientation

        joyconLeft.update(data)
    elif side == "Right":
        if joyconRight.orientation != orientation:
            joyconRight.orientation = orientation

        joyconRight.update(data)
    else:
        print("Unknown controller side.")

    check_control(side, orientation)
    
    gamepad.update()
    
    return client