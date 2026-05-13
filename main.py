import asyncio, os
from bleak import BleakClient, BleakScanner
from program.constant import MANUFACTURER_ID, ID_VENDOR, PRODUCT_JOYCON_RIGHT, PRODUCT_JOYCON_LEFT, GENERIC_ACCESS_DEVICE_NAME, LEFT_HID_REPORT_HANDLE
import struct 
from program.controllers.controllers import BaseController
from program.controllers.joycons.left_joycons import LeftJoyCon
from program.controllers.joycons.right_joycons import RightJoyCon


# Check if the operating system is Windows
if(os.name != 'nt'):
    print("This application is only supported on Windows.")
    exit(1)

async def scan_devices(number_of_devices=1):
    print("Scanning for Joy-Con 2 devices...")

    devices = []
    stop_event = asyncio.Event()

    async def callback(device, adv_data):

        manufacturer_data = adv_data.manufacturer_data.get(MANUFACTURER_ID)
        if manufacturer_data:
            vendor = struct.unpack('<H', manufacturer_data[3:5])[0]
            product = struct.unpack('<H', manufacturer_data[5:7])[0]

            if any(d.device.address == device.address for d in devices):
                return

            if vendor == ID_VENDOR:
                if product == PRODUCT_JOYCON_LEFT:
                    print(f"Found Joy-Con Left: {device.address}")
                    joycon = LeftJoyCon(device)
                    devices.append(joycon)
                    await joycon.connect()
            
                elif product == PRODUCT_JOYCON_RIGHT:
                    print(f"Found Joy-Con Right: {device.address}")
                    joycon = RightJoyCon(device)
                    devices.append(joycon)
                    await joycon.connect()

                if len(devices) >= number_of_devices:
                    stop_event.set()



    async with BleakScanner(callback):
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            print("Device scanning cancelled.")
        except Exception as e:
            print(f"An error occurred during scanning: {e}")

    return devices

def notification_handler(_, data):
    print(f"Notification: {data.hex()}")

async def main():
    try:
        number_of_devices = 2
        devices = await scan_devices(number_of_devices)

        if not devices:
            print("No Joy-Con 2 devices found.")
            return

        if len(devices) < number_of_devices:
            print(f"Only found {len(devices)} device(s). Expected {number_of_devices}.")
            return
        
        print(f"Successfully connected to {len(devices)} device(s). Starting notifications...")
        
        await asyncio.gather(*(joycon.start_notify() for joycon in devices))

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())