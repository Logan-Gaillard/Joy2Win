from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight
import pyvjoy

joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

vjoy = pyvjoy.VJoyDevice(1)  # vJoy ID 1

Controls = {
    "Left": {
        "0": { #The orientation of the Joy-Con is vertical
            "ZL": 1,
            "L": 3,
            "L3": 19,
            "Right": 9,
            "Down": 10,
            "Up": 11,
            "Left": 12,
            "Minus": 14,
            "SLL": 17,
            "SRL": 18,
            "Capture": 22,
        },
        "1": { #The orientation of the Joy-Con is horizontal
            "ZL": 3, #L
            "L": 4, #R
            "L3": 19,
            "Right": 11, #Up
            "Down": 9, #Right
            "Up": 12, #Left
            "Left": 10, #Down
            "Minus": 13, #Plus
            "SLL": 1, #ZL
            "SRL": 2, #ZR
            "Capture": 22,
        },
    },
    "Right": {
        "0": { #The orientation of the Joy-Con is vertical
            "ZR": 2,
            "R": 4,
            "R3": 20,
            "A": 5,
            "B": 6,
            "X": 7,
            "Y": 8,
            "Plus": 13,
            "SRR": 15,
            "SLR": 16,
            "Home": 21,
            "GameChat": 23,
        },
        "1": { #The orientation of the Joy-Con is horizontal
            "ZR": 4, #R
            "R": 3, #L
            "R3": 19, #L3
            "A": 6, #B
            "B": 8, #Y
            "X": 5, #A
            "Y": 7, #X
            "Plus": 13,
            "SRR": 2, #ZR button
            "SLR": 1, #ZL button
            "Home": 21,
            "GameChat": 22, #Capture
        },
    }
}

async def update_vjoy(side, orientation):
    for btnName, btnValue in Controls[side][str(orientation)].items():
        if side == "Left":
            pressed = joyconLeft.buttons.get(btnName, False)
        else:
            pressed = joyconRight.buttons.get(btnName, False)
        vjoy.set_button(btnValue, pressed)

        if(side == "Left"):
            #Joystick control
            vjoy.set_axis(pyvjoy.HID_USAGE_X, joyconLeft.analog_stick["X"])
            vjoy.set_axis(pyvjoy.HID_USAGE_Y, joyconLeft.analog_stick["Y"])
            
        elif(side == "Right"):
            #print(f"Joysticks {joyconRight.analog_stick}")
            vjoy.set_axis(pyvjoy.HID_USAGE_X, joyconRight.analog_stick["X"])
            vjoy.set_axis(pyvjoy.HID_USAGE_Y, joyconRight.analog_stick["Y"])

async def notify_single_joycons(client, side, orientation, data):
    #print(f"Joy-Con data : {data.hex()}")
    if side == "Left":
        if joyconLeft.orientation != orientation:
            joyconLeft.orientation = orientation

        await joyconLeft.update(data)
    elif side == "Right":
        if joyconRight.orientation != orientation:
            joyconRight.orientation = orientation

        await joyconRight.update(data)
    else:
        print("Unknown controller side.")

    await update_vjoy(side, orientation)

    return client