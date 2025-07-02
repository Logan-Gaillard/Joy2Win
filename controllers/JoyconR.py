import sys
import platform
import os
import ctypes

class JoyConRight:
    def __init__(self):
        self.name = "Joy-Con"
        self.side = "Right"
        self.orientation = 0  # Default orientation is vertical
        self.mac_address = ""

        self.buttons = {
            #these buttons is mapped to Upright usage (it need to invert the mapping for a sideways usage)
            "ZR": False,
            "R": False,
            "Plus": False,
            "SL": False,
            "SR": False,
            "Y": False,
            "B": False,
            "X": False,
            "A": False,
            "R3": False,
            "Home": False,
            "GameChat": False,
        }
        self.analog_stick = {
            #these values is mapped to Upright usage (it need to invert the mapping for a sideways usage)
            "X": 0.0,
            "Y": 0.0
        }

        # I hope i can implement this later with HID
        #self.accelerometer = {
        #    "X": 0.0,
        #    "Y": 0.0,
        #    "Z": 0.0
        #}

        # I hope i can implement this later with HID
        #self.gyroscope = {
        #    "X": 0.0,
        #    "Y": 0.0,
        #    "Z": 0.0
        #}

        self.battery_level = 100.0
        self.alertSent = False
        self.is_connected = False

    def update(self, datas):
        # Update button states based on the received data
        btnDatas = datas[4] << 8 | datas[5]
        JoystickDatas = datas[13:16]

        self.buttons["ZR"] = bool(btnDatas & 0x8000)
        self.buttons["R"] = bool(btnDatas & 0x4000)
        self.buttons["Plus"] = bool(btnDatas & 0x0002)
        self.buttons["SL"] = bool(btnDatas & 0x2000)
        self.buttons["SR"] = bool(btnDatas & 0x1000)
        self.buttons["Y"] = bool(btnDatas & 0x0100)
        self.buttons["B"] = bool(btnDatas & 0x0400)
        self.buttons["X"] = bool(btnDatas & 0x0200)
        self.buttons["A"] = bool(btnDatas & 0x0800)
        self.buttons["R3"] = bool(btnDatas & 0x0004)
        self.buttons["Home"] = bool(btnDatas & 0x0010)
        self.buttons["GameChat"] = bool(btnDatas & 0x0040)

        self.analog_stick["X"], self.analog_stick["Y"] = joystick_decoder(JoystickDatas, self.orientation)

        # Update battery level only if the new value is lower than the current one
        self.battery_level = round(datas[31] / 255.0 * 100, 1)

        if(self.battery_level < 10.0 and self.is_connected and not self.alertSent):
            self.notify_low_battery()
            self.alertSent = True

        self.is_connected = True

    def print_status(self, datas):
        sys.stdout.write(f"\033[2;0H")
        print(f"JoyCon Right Status:")
        print(f"  Buttons: {self.buttons}                    ")
        print(f"  Analog Stick: {self.analog_stick}                    ")
        #print(f"  Accelerometer: {self.accelerometer}")
        #print(f"  Gyroscope: {self.gyroscope}")
        print(f"  Battery Level: {self.battery_level}%                    ")
        print(f"  Connected: {self.is_connected}                    ")
        #print(f"  Datas received: " + str(datas.hex()))

    def setMacAddress(self, mac_address):
        self.mac_address = mac_address

    def notify_low_battery(self):
        msg = f"{self.name} {self.side} : low battery ({self.battery_level}%)"

        if platform.system() == "Windows":
            ctypes.windll.user32.MessageBoxW(0, msg, "Alert Joy-Con", 0)
        elif platform.system() == "Linux":
            os.system(f'notify-send "Alert Joy-Con" "{msg}"')
        else:
            print(f"[Alert] {msg}")

def joystick_decoder(data, orientation):
    if len(data) != 3:
        print("Invalid joystick data length")
        return 0, 0
    # Decode the joystick data
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = ((data[2] << 4)) | ((data[1] & 0xF0) >> 4)

    # Normalize the values to the range of -1.0 to 1.0
    x = max(-1.0, min(1.0, (x - 2048) / 2048.0 * 1.7))
    y = max(-1.0, min(1.0, (y - 2048) / 2048.0 * 1.7))

    # Scale the values to the range of -32768 to 32767
    x = int(x * 32767)
    y = int(y * 32767)

    if orientation == 1:
        # Invert the X and Y values for horizontal orientation
        old_x = x
        old_y = y
        x = old_y
        y = -old_x

    return x, y