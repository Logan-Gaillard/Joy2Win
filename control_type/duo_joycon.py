from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight

from dsu_server import controller_update

from config import Config
from pynput.mouse import Controller, Button

import pyvjoy
import threading
import time


# Initialize Joy-Con controllers
joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

# Read the configuration from config.ini
config = Config().getConfig()

# Initialize vJoy device
vjoy = pyvjoy.VJoyDevice(1)  # vJoy ID 1

# Initialize mouse loop at the start
firstCall = False

# Mouse movement variables
mouse = Controller()

targetX, targetY = 0, 0
previousMouseX, previousMouseY = 0, 0
leftPressed = False
rightPressed = False
joyconMouseMode = None

def mouse_loop():
    global targetX, targetY
    while True:
        stepX = targetX // 6
        stepY = targetY // 6
        if stepX != 0 or stepY != 0:
            mouse.move(stepX, stepY)
            targetX -= stepX
            targetY -= stepY
        time.sleep(0.006)  # 60 ms


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

async def update(controllerSide, joycon):
    global targetX, targetY, previousMouseX, previousMouseY, leftPressed, rightPressed, joyconMouseMode, firstCall

    isMouseMode = joycon.mouse["distance"] == "00" or joycon.mouse["distance"] == "01"
    if joyconMouseMode is None and isMouseMode is True and config['mouse_mode'] != 0:
        joyconMouseMode = controllerSide
    elif isMouseMode is False and joyconMouseMode == controllerSide:
        joyconMouseMode = None

    if firstCall == False and isMouseMode == True:
        threading.Thread(target=mouse_loop, daemon=True).start()
        firstCall = True

    for side in ["Left", "Right"]:
        for btnName, btnValue in Controls[side].items():
            pressed = (joyconLeft.buttons.get(btnName, False) if side == "Left" else joyconRight.buttons.get(btnName, False)) if side != joyconMouseMode else False
            vjoy.set_button(btnValue, pressed)

    if joyconMouseMode != "Left":
        vjoy.set_axis(pyvjoy.HID_USAGE_X, joyconLeft.analog_stick["X"])
        vjoy.set_axis(pyvjoy.HID_USAGE_Y, joyconLeft.analog_stick["Y"])
    if joyconMouseMode != "Right":
        vjoy.set_axis(pyvjoy.HID_USAGE_RX, joyconRight.analog_stick["X"])
        vjoy.set_axis(pyvjoy.HID_USAGE_RY, joyconRight.analog_stick["Y"])

        if controllerSide == "Right" and config["enable_dsu"] == True:
            await controller_update(joyconRight.motionTimestamp, joyconRight.accelerometer, joyconRight.gyroscope)

    if isMouseMode == True and joyconMouseMode == controllerSide:
        deltaX = (joycon.mouse["X"] - previousMouseX + 32768) % 65536 - 32768 # Normalize mouse X movement
        deltaY = (joycon.mouse["Y"] - previousMouseY + 32768) % 65536 - 32768 # Normalize mouse Y movement
        previousMouseX = joycon.mouse["X"]
        previousMouseY = joycon.mouse["Y"]

        targetX += deltaX
        targetY += deltaY

        if joycon.mouseBtn["Left"] == True:
            if not leftPressed:
                mouse.press(Button.left)
            leftPressed = True
        else:
            if leftPressed:
                mouse.release(Button.left)
            leftPressed = False

        if joycon.mouseBtn["Right"] == True:
            if not rightPressed:
                mouse.press(Button.right)
            rightPressed = True
        else:
            if rightPressed:
                mouse.release(Button.right)
            rightPressed = False

        mouse.scroll(joycon.mouseBtn["scrollX"] / 32768, joycon.mouseBtn["scrollY"] / 32768)  # Scroll vertically


async def notify_duo_joycons(client, side, data):
    if side == "Left":
        await joyconLeft.update(data)
        await update(side, joyconLeft)
    elif side == "Right":
        await joyconRight.update(data)
        await update(side, joyconRight)
    else:
        print("Unknown controller side.")
    
    return client