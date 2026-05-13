import asyncio, os
from bleak import BleakClient, BleakScanner
from program.constant import MANUFACTURER_ID, ID_VENDOR, PRODUCT_JOYCON_RIGHT, PRODUCT_JOYCON_LEFT, GENERIC_ACCESS_DEVICE_NAME, LEFT_HID_REPORT_HANDLE
import struct 

# Check if the operating system is Windows
if(os.name != 'nt'):
    print("This application is only supported on Windows.")
    exit(1)

async def scan_devices():
    print("Scanning for Joy-Con 2 devices...")

    device_found = None
    stop_event = asyncio.Event()

    def callback(device, adv_data):
        nonlocal device_found

        manufacturer_data = adv_data.manufacturer_data.get(MANUFACTURER_ID)
        if manufacturer_data:
            vendor = struct.unpack('<H', manufacturer_data[3:5])[0]
            product = struct.unpack('<H', manufacturer_data[5:7])[0]

            if vendor == ID_VENDOR and device_found is None:
                if product == PRODUCT_JOYCON_RIGHT:
                    print(f"Found Joy-Con Right: {device.address}")
                    device_found = device
                    stop_event.set()
                elif product == PRODUCT_JOYCON_LEFT:
                    print(f"Found Joy-Con Left: {device.address}")
                    device_found = device
                    stop_event.set()

    async with BleakScanner(callback) as scanner:
        await stop_event.wait()

    return device_found

def notification_handler(_, data):
    print(f"Notification: {data.hex()}")

async def main():
    try:
        device = await scan_devices()

        client = BleakClient(device)
        await client.connect()

        device_name = await client.read_gatt_char(GENERIC_ACCESS_DEVICE_NAME)
        print(f"Connected to {device_name.decode('utf-8')}")

        await client.start_notify(LEFT_HID_REPORT_HANDLE - 1, notification_handler)

        while True:
            await asyncio.sleep(1)



    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())