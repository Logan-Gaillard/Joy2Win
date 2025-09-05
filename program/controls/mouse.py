import threading
import ctypes
from pynput.mouse import Controller, Button
import time

mouse = Controller()

firstCall = False

targetX, targetY, previousMouseX, previousMouseY = 0, 0, 0, 0
isLeftPressed, isRightPressed = False, False

PUL = ctypes.POINTER(ctypes.c_ulong) # PUL(Pointer to an Unsigned Long)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]
    
class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong),
                ("_input", _INPUT)]

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800


def mouse_control(deltaX, deltaY, joycon):
    global firstCall, targetX, targetY, previousMouseX, previousMouseY, isLeftPressed, isRightPressed
    if(firstCall == False):
        initMouse()
        return

    deltaX = (joycon.mouse["X"] - previousMouseX + 32768) % 65536 - 32768 # Normalize mouse X movement
    deltaY = (joycon.mouse["Y"] - previousMouseY + 32768) % 65536 - 32768 # Normalize mouse Y movement
    previousMouseX = joycon.mouse["X"]
    previousMouseY = joycon.mouse["Y"]

    targetX += deltaX
    targetY += deltaY

    if joycon.mouseBtn["Left"] == True:
        if(isLeftPressed == False):
            isLeftPressed = True
            mouse.press(Button.left)
    else:
        if(isLeftPressed == True):
            isLeftPressed = False
            mouse.release(Button.left)

    if joycon.mouseBtn["Right"] == True:
        if(isRightPressed == False):
            isRightPressed = True
            mouse.press(Button.right)
    else:
        if(isRightPressed == True):
            isRightPressed = False
            mouse.release(Button.right)

    mouse.scroll(joycon.mouseBtn["scrollX"] / 32768, joycon.mouseBtn["scrollY"] / 32768)  # Scroll vertically

def mouse_loop():
    global targetX, targetY
    sensitivity = 0.25  # Réduire la sensibilité (0.25 = 25%)
    while True:
        stepX = int(targetX * sensitivity)
        stepY = int(targetY * sensitivity)
        if stepX != 0 or stepY != 0:
            inp = INPUT(type=0, mi=MOUSEINPUT(dx=stepX, dy=stepY, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=None))
            ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            targetX -= stepX
            targetY -= stepY
        time.sleep(0.006)  # 6 ms


def initMouse():
    global firstCall
    if firstCall == False:
        threading.Thread(target=mouse_loop, daemon=True).start()
        firstCall = True