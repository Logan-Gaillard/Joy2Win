from pyvjoystick import vigem as vg
gamepad = vg.VDS4Gamepad()

Controls = {
    "full": { 
        "Left": {"L": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, "Minus": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK
        },
        "Right": {"R": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A, "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B, "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, "Plus": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "Home": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
        }
    },

    1: { 
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
   
}



def playstation_control(controller, side, nbController = 2, orientation = 0):
    for btnName, btnValue in FullControls[side].items():
        if btnValue is None:
            continue
        if controller.buttons.get(btnName, False):
            gamepad.press_button(btnValue)
        else:
            gamepad.release_button(btnValue)
        


    gamepad.update()
    
