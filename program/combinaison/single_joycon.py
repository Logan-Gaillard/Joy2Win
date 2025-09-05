from controllers.JoyconL import JoyConLeft
from controllers.JoyconR import JoyConRight

from program.dsu.dsu_server import controller_update

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

#Calculating latency
lastTime = time.time()

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

async def update(joycon, side, orientation, isInMouse): # Update vJoy buttons and axes based on Joy-Con state
    for btnName, btnValue in Controls[side][str(orientation)].items():
        pressed = joycon.buttons.get(btnName, False) and not isInMouse # Set True if it is pressed and not in mouse mode
        vjoy.set_button(btnValue, pressed) # Set the button state in vJoy

        if not isInMouse: # Only update axes if not in mouse mode
            vjoy.set_axis(pyvjoy.HID_USAGE_X, joycon.analog_stick["X"])
            vjoy.set_axis(pyvjoy.HID_USAGE_Y, joycon.analog_stick["Y"])
            
        if config["enable_dsu"] == True: # Update DSU server with motion data
            await controller_update(joycon.motionTimestamp, joycon.accelerometer, joycon.gyroscope)


async def controller_traitement(joycon, side, orientation, data):
    global firstCall, previousMouseX, previousMouseY, targetX, targetY, lastTime, leftPressed, rightPressed

    isMouseMode = joycon.mouse["distance"] == "00" or joycon.mouse["distance"] == "01" # Check if mouse mode is active based on mouse distance

    # Initialize mouse mode if not already done
    if firstCall == False and (config['mouse_mode'] == 2 or config["mouse_mode"] == 1 and isMouseMode == True):
        threading.Thread(target=mouse_loop, daemon=True).start()
        firstCall = True

    # Update controller orientation
    if joycon.orientation != orientation:
        joycon.orientation = orientation

    await joycon.update(data) # Update Joy-Con state with received data

    await update(joycon, side, orientation, isMouseMode) # Update vJoy buttons and axes

    if config['mouse_mode'] == 2 or config["mouse_mode"] == 1 and isMouseMode == True:
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

        mouse.scroll(joycon.mouseBtn["scrollX"] / 32768, joycon.mouseBtn["scrollY"] / 32768)

    # Latency calculation
    currentTime = time.time()
    elapsedTime = (currentTime - lastTime) * 1000  # Convert to milliseconds
    lastTime = currentTime
    #print(f"Latency: {elapsedTime:.4f} milliseconds")


async def notify_single_joycons(client, side, orientation, data):
    if(side == "Left"):
        await controller_traitement(joyconLeft, side, orientation, data)
    elif(side == "Right"):
        await controller_traitement(joyconRight, side, orientation, data)
    return client