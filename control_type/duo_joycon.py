from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight
import pyvjoy

joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

vjoy = pyvjoy.VJoyDevice(1)  # vJoy ID 1

Controls = {
    "Left": {
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
    "Right": {
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
    }
}

async def update_vjoy(side):
    for side in ["Left", "Right"]:
        for btnName, btnValue in Controls[side].items():
            pressed = (joyconLeft.buttons.get(btnName, False) if side == "Left" else joyconRight.buttons.get(btnName, False))
            vjoy.set_button(btnValue, pressed)

    vjoy.set_axis(pyvjoy.HID_USAGE_X, joyconLeft.analog_stick["X"])
    vjoy.set_axis(pyvjoy.HID_USAGE_Y, joyconLeft.analog_stick["Y"])
    vjoy.set_axis(pyvjoy.HID_USAGE_RX, joyconRight.analog_stick["X"])
    vjoy.set_axis(pyvjoy.HID_USAGE_RY, joyconRight.analog_stick["Y"])


async def notify_duo_joycons(client, side, data):
    if side == "Left":
        await joyconLeft.update(data)
    elif side == "Right":
        await joyconRight.update(data)
    else:
        print("Unknown controller side.")

    await update_vjoy(side)
    
    return client