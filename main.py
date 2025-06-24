import asyncio
from bleak import BleakClient
from pyvjoystick import vigem as vg

MAC_JOYCON_LEFT = "xx:xx:xx:xx:xx" # REPLACE with your left Joy-Con MAC
MAC_JOYCON_RIGHT = "xx:xx:xx:xx:xx"  # REPLACE with your right Joy-Con MAC

# How to find the MAC addresson Nintendo Switch 2 :
# 1. Connect the Joy-Con to your Switch.
# 2. Go to System Settings > Controllers and Sensors.
# 3. Scroll down to "Bluetooth Devices" and select the Joy-Con.
# 4. The MAC address will be displayed at the bottom of the screen.

UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

# Init manette virtuelle Xbox 360
gamepad = vg.VX360Gamepad()

def detect_buttons(type, btn0, btn1):

    if(btn0 >= 32):
        if(type == 'l'):
            #Capture (rien pour XBOX pour l'instant)
            print("Capture")
        btn0 -= 32


    if(btn0 >= 16):
        if (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)
        btn0 -= 16
    else:
        if (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)


    if(btn0 >= 8):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        btn0 -= 8
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)


    if(btn0 >= 4):
        if (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
        btn0 -= 4
    else:
        if (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)


    if(btn0 >= 1):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
        btn0 -= 1
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)

    #Détection de btn1
    if(btn1 >= 128):
        if(type == 'l'):
            gamepad._report.bLeftTrigger = 255
        elif (type == 'r'):
            gamepad._report.bRightTrigger = 255
        btn1 -= 128
    else:
        if(type == 'l'):
            gamepad._report.bLeftTrigger = 0
        elif (type == 'r'):
            gamepad._report.bRightTrigger = 0


    if(btn1 >= 64):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        btn1 -= 64
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)


    if(btn1 >= 32): 
        #SL (rien pour XBOX pour l'instant)
        btn1 -= 32
    if(btn1 >= 16):
        #SR (rien pour XBOX pour l'instant)
        btn1 -= 16


    if(btn1 >= 8):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B) #Y for XBOX
        btn1 -= 8
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)


    if(btn1 >= 4):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A) #X for XBOX
        btn1 -= 4
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A) 


    if(btn1 >= 2):
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y) #B for XBOX
        btn1 -= 2
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)


    if(btn1 >= 1): 
        if(type == 'l'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        elif (type == 'r'):
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X) #A for XBOX
        btn1 -= 1
    else:
        if(type == 'l'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        elif (type == 'r'):
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X) #A for XBOX

    gamepad.update()

def detect_joystick(type, axis: bytes):
    rx = axis[0] | ((axis[1] & 0x0F) << 8)
    ry = (axis[1] >> 4) | (axis[2] << 4)

    if(type == "r"):
        gamepad.right_joystick(*scale_joystick(rx, ry))
    elif(type == "l"):
        gamepad.left_joystick(*scale_joystick(rx, ry))


    gamepad.update()

def scale_joystick(raw_x: int, raw_y: int) -> tuple[int, int]:
    JOYCON_MIN = 700
    JOYCON_MAX = 3270
    JOYCON_CENTER = (JOYCON_MAX + JOYCON_MIN) / 2.0  # ≈ 2000

    XBOX_MAX = 32767
    XBOX_MIN = -32768

    centered_x = float(raw_x) - JOYCON_CENTER
    normalized_x = centered_x / ((JOYCON_MAX - JOYCON_MIN) / 2.0)
    scaled_x = int(round(normalized_x * XBOX_MAX))

    centered_y = float(raw_y) - JOYCON_CENTER
    normalized_y = centered_y / ((JOYCON_MAX - JOYCON_MIN) / 2.0)
    scaled_y = int(round(normalized_y * XBOX_MAX))

    scaled_x = max(XBOX_MIN, min(XBOX_MAX, scaled_x))
    scaled_y = max(XBOX_MIN, min(XBOX_MAX, scaled_y))

    return scaled_x, scaled_y

def on_notification_joyL(_, data: bytes):

    #print(data.hex())
    detect_buttons("l", data[5], data[6])
    detect_joystick("l", data[10:13])

def on_notification_joyR(_, data: bytes):
    #print(data.hex())
    detect_buttons("r", data[5], data[4])
    detect_joystick("r", data[13:16])


async def main():
    loop = asyncio.get_event_loop()

    client_left = BleakClient(MAC_JOYCON_LEFT, pair=False)
    client_right = BleakClient(MAC_JOYCON_RIGHT, pair=False)

    await client_left.connect()
    await client_right.connect()

    try:
        await client_left.start_notify(UUID, lambda h, d: loop.run_in_executor(None, on_notification_joyL, h, d))
        await client_right.start_notify(UUID, lambda h, d: loop.run_in_executor(None, on_notification_joyR, h, d))
        print("Joycons connected and notifications started.")
        await asyncio.Event().wait()
    finally:
        await client_left.disconnect()
        await client_right.disconnect()
if __name__ == "__main__":
    asyncio.run(main())