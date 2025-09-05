import sys
import platform
import os
import ctypes
import struct

class JoyConLeft:
    def __init__(self):
        self.name = "Joy-Con"
        self.side = "Left"
        self.orientation = 0  # Default orientation is vertical
        self.mac_address = ""
        
        self.buttons = {
            #these buttons is mapped to Upright usage (it need to invert the mapping for a sideways usage)
            "ZL": False,
            "L": False,
            "Minus": False,
            "SLL": False,
            "SRL": False,
            "Left": False,
            "Down": False,
            "Up": False,
            "Right": False,
            "L3": False,
            "Capture": False,
        }
        self.analog_stick = {
            #these values is mapped to Upright usage (it need to invert the mapping for a sideways usage)
            "X": 0,
            "Y": 0
        }

        self.accelerometer = {
            "X": 0.0,
            "Y": 0.0,
            "Z": 0.0,
        }
        
        self.gyroscope = {
            "X": 0.0, # Pitch
            "Y": 0.0, # Roll
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
        self.motionTimestamp = bytes.fromhex("00000000")
        self.battery_level = 100.0
        self.alertSent = False
        self.is_connected = False

    async def update(self, datas):
        # Update button states based on the received data
        btnDatas = datas[5] << 8 | datas[6]
        JoystickDatas = datas[10:13]
        mouseDatas = datas[16:24]

        self.mouse["X"], self.mouse["Y"] = struct.unpack("<hh", mouseDatas[:4])
        self.mouse["distance"] = mouseDatas[7:8].hex()

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

        #print(f"Timestamp: {self.timestamp.hex()}, Accel: ({self.accelerometer['X']}, {self.accelerometer['Y']}, {self.accelerometer['Z']}), Gyro: ({self.gyroscope['X']}, {self.gyroscope['Y']}, {self.gyroscope['Z']})")

        self.buttons["SLL"] = bool(btnDatas & 0x0020)
        self.buttons["SRL"] = bool(btnDatas & 0x0010)
        self.buttons["Minus"] = bool(btnDatas & 0x0100)
        self.buttons["L"] = bool(btnDatas & 0x0040)
        self.buttons["ZL"] = bool(btnDatas & 0x0080)
        self.buttons["Left"] = bool(btnDatas & 0x0008)
        self.buttons["Down"] = bool(btnDatas & 0x0001)
        self.buttons["Up"] = bool(btnDatas & 0x0002)
        self.buttons["Right"] = bool(btnDatas & 0x0004)
        self.buttons["L3"] = bool(btnDatas & 0x0800)
        self.buttons["Capture"] = bool(btnDatas & 0x2000)

        self.analog_stick["X"], self.analog_stick["Y"] = joystick_decoder(JoystickDatas, self.orientation)

        self.mouseBtn["Left"] = bool(btnDatas & 0x0040) #L
        self.mouseBtn["Right"] = bool(btnDatas & 0x0080) #ZL
        self.mouseBtn["scrollX"], self.mouseBtn["scrollY"] = scroll_decoder(JoystickDatas)

        # Update battery level only if the new value is lower than the current one
        battery_raw = (datas[31]) | (datas[32] << 8)
        self.battery_level = round(battery_raw * 100 / 4095)

        if(self.battery_level < 10.0 and self.is_connected and not self.alertSent):
            self.notify_low_battery()
            self.alertSent = True

        self.is_connected = True

    def print_status(self, datas):
        sys.stdout.write(f"\033[2;0H")
        print(f"JoyCon Left Status:")
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