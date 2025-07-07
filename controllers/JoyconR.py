import sys
import platform
import os
import ctypes
import struct

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
            "SLR": False,
            "SRR": False,
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
            "X": 0,
            "Y": 0
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

    async def update(self, datas):
        # Update button states based on the received data
        btnDatas = datas[4] << 8 | datas[5]
        JoystickDatas = datas[13:16]

        gyroX, gyroY, gyroZ = struct.unpack("<3h", bytes(datas[0x30:0x36]))

        motionsensorDatas = {
            "timestamp": (datas[0x2A + 0x03] << 24) | (datas[0x2A + 0x02] << 16) | (datas[0x2A + 0x01] << 8) | datas[0x2A],
            "temperature": (datas[0x2E + 0x01] << 8) | datas[0x2E],
            #"GyroX": (datas[0x30 + 0x01] << 8) | datas[0x30],
            "GyroX": gyroX,
            "?": (datas[0x32 + 0x01] << 8) | datas[0x32],
            "??": (datas[0x34 + 0x01] << 8) | datas[0x34],
            "???": (datas[0x36 + 0x01] << 8) | datas[0x36],
            "????": (datas[0x38 + 0x01] << 8) | datas[0x38],
            "?????": (datas[0x3A + 0x01] << 8) | datas[0x3A],
        }

        #print(f"motionsensorDatas: {datas[0x2A:0x3B].hex()}", end=" ")
        #print(f"timestamp: {motionsensorDatas['timestamp']} soit {motionsensorDatas['timestamp'] / 45000:.1f} s", end=" ")
        #print(f"temperature: {motionsensorDatas['temperature']} soit {25 + motionsensorDatas['temperature'] / 127:.2f} °C", end=" ")
        #print(f"GyroX: {motionsensorDatas['GyroX']} (bin: {motionsensorDatas['GyroX']:016b}) (hex: {motionsensorDatas['GyroX']:04x}) = ")

        self.buttons["ZR"] = bool(btnDatas & 0x8000)
        self.buttons["R"] = bool(btnDatas & 0x4000)
        self.buttons["Plus"] = bool(btnDatas & 0x0002)
        self.buttons["SLR"] = bool(btnDatas & 0x2000)
        self.buttons["SRR"] = bool(btnDatas & 0x1000)
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

# Return stick values from 0 and 32768
def joystick_decoder(data, orientation):
    if len(data) != 3:
        return 4096 * 4, 4096 * 4
    
    X_STICK_MIN = 780
    X_STICK_MAX = 3260
    Y_STICK_MIN = 820
    Y_STICK_MAX = 3250

    # Decode the joystick data, max values are
    x_raw = ((data[1] & 0x0F) << 8) | data[0]
    y_raw = (data[2] << 4) | ((data[1] & 0xF0) >> 4)

    x = max(0, min((x_raw - X_STICK_MIN) / (X_STICK_MAX - X_STICK_MIN), 1))
    y = 1 - max(0, min((y_raw - Y_STICK_MIN) / (Y_STICK_MAX - Y_STICK_MIN), 1))

    x = int(x * 32768)
    y = int(y * 32768)

    if orientation == 1:  # Horizontal orientation
        # Swap X and Y for horizontal orientation
        x, y = y, x
        # Invert Y axis for horizontal orientation
        x = 32768 - x

    return x, y