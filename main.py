import asyncio, os
from bleak import BleakScanner
from program.constant import BOLD_TEXT, RESET_TEXT, RED_TEXT, MANUFACTURER_ID, ID_VENDOR, PRODUCT_JOYCON_RIGHT, PRODUCT_JOYCON_LEFT
import struct 
from program.controllers.controllers import BaseController
from program.controllers.joycons.left_joycons import LeftJoyCon
from program.controllers.joycons.right_joycons import RightJoyCon
from program.config import Config

# Check if the operating system is Windows
if(os.name != 'nt'):
    print(f"{RED_TEXT}This application is only supported on Windows.{RESET_TEXT}")
    exit(1)

config = Config()
devices: list[BaseController] = []

async def scan_devices(number_of_devices=1):
    print(f"Scanning for {BOLD_TEXT}{number_of_devices}{RESET_TEXT} Joy-Con 2 devices...")
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


async def main():
    try:
        number_of_devices = config.type_controller == 0 and 2 or 1
        devices = await scan_devices(number_of_devices)

        if not devices:
            print(f"{RED_TEXT}No Joy-Con 2 devices found.{RESET_TEXT}")
            return

        if len(devices) < number_of_devices:
            print(f"{RED_TEXT}Only found {len(devices)} device(s). Expected {number_of_devices}.{RESET_TEXT}")
            return
        
        print(f"Successfully connected to {len(devices)} device(s). Starting notifications...")
        
        await asyncio.gather(*(joycon.init_and_pairing() for joycon in devices))

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        print("Disconnect controllers and exiting...")
        for joycon in devices:
            await joycon.disconnect()
        exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")