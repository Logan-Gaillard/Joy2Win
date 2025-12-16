import sys
import platform
import os
import ctypes
import struct

from config import Config

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
        self.accelerometer = {
            "X": 0.0,
            "Y": 0.0,
            "Z": 0.0,
        }

        # I hope i can implement this later with HID
        self.gyroscope = {
            "X": 0.0, # Roll
            "Y": 0.0, # Pitch
            "Z": 0.0, # Yaw
        }

        self.mouse = {
            "X": 0.0,
            "Y": 0.0,
            "distance": "0C"
        }

        self.mouseBtn = {
            "Left": False,
            "Right": False,
            "scrollX": 0.0,
            "scrollY": 0.0,
        }

        self.timestamp = bytes.fromhex("00000000") 
        self.motionTimestamp = bytes.fromhex("00000000")  # Placeholder for motion timestamp
        self.battery_level = 100.0
        self.alertSent = False
        self.is_connected = False

        
        # Read the configuration from config.ini
        self.config = Config().getConfig()

    async def update(self, datas):
        # Update button states based on the received data
        btnDatas = datas[4] << 8 | datas[5]
        JoystickDatas = datas[13:16]
        mouseDatas = datas[16:24]

        self.mouse["X"], self.mouse["Y"] = struct.unpack("<hh", mouseDatas[:4])
        self.mouse["distance"] = mouseDatas[7:8].hex()

        #print(f"JoyCon Right Datas: {mouseDatas.hex()}, Mouse X: {self.mouse['X']}, Mouse Y: {self.mouse['Y']}, Mouse Distance: {self.mouse['distance']}")

        self.timestamp = bytes.fromhex(datas[0:4].hex())

        self.motionTimestamp = struct.unpack("<i", datas[0x2A:0x2E])[0]

        accel_x_raw, accel_y_raw, accel_z_raw = struct.unpack("<3h", datas[0x30:0x36])
        gyro_x_raw, gyro_y_raw, gyro_z_raw = struct.unpack("<3h", datas[0x36:0x3C])

        accel_factor = 1 / 4096  # 1G = 4096
        gyro_factor = 360 / 6048  # 360° = 6048

        self.accelerometer["X"] = -accel_x_raw * accel_factor
        self.accelerometer["Y"] = -accel_z_raw * accel_factor
        self.accelerometer["Z"] = accel_y_raw * accel_factor

        self.gyroscope["X"] = gyro_x_raw * gyro_factor
        self.gyroscope["Y"] = -gyro_z_raw * gyro_factor
        self.gyroscope["Z"] = gyro_y_raw * gyro_factor

        #print(f"X of 360°: {self.gyroscope['X']:2f} : {(self.gyroscope['X'] * 360 / 48000):2f}, Y of 360°: {self.gyroscope['Y']:2f} : {self.gyroscope['Y'] * 360 / 48000:2f}, Z of 360°: {self.gyroscope['Z']:2f} : {self.gyroscope['Z'] * 360 / 48000:2f}")


        #print(f"Timestamp: {self.timestamp.hex()}, Accel: ({self.accelerometer['X']}, {self.accelerometer['Y']}, {self.accelerometer['Z']}), Gyro: ({self.gyroscope['X']}, {self.gyroscope['Y']}, {self.gyroscope['Z']})")

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

        self.mouseBtn["Left"] = bool(btnDatas & 0x4000) #R
        self.mouseBtn["Right"] = bool(btnDatas & 0x8000) #ZR
        self.mouseBtn["scrollX"], self.mouseBtn["scrollY"] = scroll_decoder(JoystickDatas)

        if self.mouseBtn["scrollY"] < self.config["scroll_deadzone"] and self.mouseBtn["scrollY"] > self.config["scroll_deadzone"] * -1:
            self.mouseBtn["scrollY"] = 0
        # print(f"{self.mouseBtn['scrollX']}, {self.mouseBtn['scrollY']}")

        # Update battery level only if the new value is lower than the current one
        battery_raw = (datas[31]) | (datas[32] << 8)
        self.battery_level = round(battery_raw * 100 / 4095)

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

def scroll_decoder(data):
    if len(data) != 3:
        return 0, 0

    X_STICK_MIN = 780
    X_STICK_MAX = 3260
    Y_STICK_MIN = 820
    Y_STICK_MAX = 3250

    x_raw = ((data[1] & 0x0F) << 8) | data[0]
    y_raw = (data[2] << 4) | ((data[1] & 0xF0) >> 4)

    # Centrer autour de zéro
    x_center = (X_STICK_MAX + X_STICK_MIN) / 2
    y_center = (Y_STICK_MAX + Y_STICK_MIN) / 2

    x = x_raw - x_center
    y = y_raw - y_center

    # Normaliser pour obtenir une plage [-32768, 32767]
    x = int(max(-1, min(x / ((X_STICK_MAX - X_STICK_MIN) / 2), 1)) * 32767)
    y = int(max(-1, min(y / ((Y_STICK_MAX - Y_STICK_MIN) / 2), 1)) * 32767)

    if x > -3000 and x < 3000:
        x = 0
    if y > -3000 and y < 3000:
        y = 0

    return x, y