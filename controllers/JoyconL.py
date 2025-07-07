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
        #self.accelerometer = {
        #    "X": 0,
        #    "Y": 0,
        #    "Z": 0
        #}
        #self.gyroscope = {
        #    "X": 0,
        #    "Y": 0,
        #    "Z": 0
        #}
        self.battery_level = 100.0
        self.alertSent = False
        self.is_connected = False

    async def update(self, datas):
        # Update button states based on the received data
        btnDatas = datas[5] << 8 | datas[6]
        JoystickDatas = datas[10:13]

        gyroX, gyroY, gyroZ = struct.unpack("<3h", bytes(datas[0x30:0x36]))
        accelX, accelY, accelZ = struct.unpack("<3h", bytes(datas[0x36:0x3C]))

        motionsensorDatas = {
            "timestamp": (datas[0x2A + 0x03] << 24) | (datas[0x2A + 0x02] << 16) | (datas[0x2A + 0x01] << 8) | datas[0x2A],
            "temperature": (datas[0x2E + 0x01] << 8) | datas[0x2E],
            #"GyroX": (datas[0x30 + 0x01] << 8) | datas[0x30],
            #"GyroY": (datas[0x32 + 0x01] << 8) | datas[0x32],
            #"GyroZ": (datas[0x34 + 0x01] << 8) | datas[0x34],
            "GyroX": gyroX,
            "GyroY": gyroY,
            "GyroZ": gyroZ,
            "AccelX": accelX,
            "AccelY": accelY,
            "AccelZ": accelZ,
            "???": (datas[0x36 + 0x01] << 8) | datas[0x36],
            "????": (datas[0x38 + 0x01] << 8) | datas[0x38],
            "?????": (datas[0x3A + 0x01] << 8) | datas[0x3A],
        }

        #print(f"motionsensorDatas: {datas[0x2A:0x3B].hex()}", end=" ")
        #print(f"timestamp: {motionsensorDatas['timestamp']} soit {motionsensorDatas['timestamp'] / 45000:.1f} s", end=" ")
        #print(f"temperature: {motionsensorDatas['temperature']} soit {25 + motionsensorDatas['temperature'] / 127:.2f} °C", end=" ")
        #print(f"GyroX: {motionsensorDatas['GyroX']} (bin: {motionsensorDatas['GyroX']:016b}) (hex: {motionsensorDatas['GyroX']:04x}) = ")

        #print("Gyro: ", gyroX, gyroY, gyroZ, "Accel: ", accelX, accelY, accelZ)

        self.buttons["SL"] = bool(btnDatas & 0x0020)
        self.buttons["SR"] = bool(btnDatas & 0x0010)
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

        # Update battery level only if the new value is lower than the current one
        self.battery_level = round(datas[31] / 255.0 * 100, 1)

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