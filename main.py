import asyncio, os, configparser
from bleak import BleakClient, BleakScanner

# Constants
manufact = {
    "id": 0x0553,  # Nintendo Co., Ltd. (https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/)
    "data-prefix": bytes([0x01, 0x00, 0x03, 0x7e, 0x05])  # Manufacturer data prefix for Joy-Con (I hope this prefix is correct, and it same for everyone)
}
UUID_NOTIFY = "ab7de9be-89fe-49ad-828f-118f09df7fd2"
UUID_CMD = "649d4ac9-8eb7-4e6c-af44-1ea54fe5f005"

#Config variables (by default)
config = {
    "type": 0,  # 0 = Both JoyCons, 1 = Joycon Left, 2 = Joycon Right
    "orientation": 0  # 0 = Vertical, 1 = Horizontal
}

clients = []  # List to hold connected clients

async def scan_joycons():
    device_controller = None

    def callback(device, advertisement_data):
        nonlocal device_controller
        data = advertisement_data.manufacturer_data.get(manufact["id"])
        if not data:
            return

        if data.startswith(manufact["data-prefix"]):
            if not device_controller:
                print(f"Controller with address: {device.address} found.")
                device_controller = device

    scanner = BleakScanner(callback)
    await scanner.start()

    while True:
        if device_controller:
            break
        await asyncio.sleep(0.5)
    await scanner.stop()

    return device_controller

# Connect the controller and attribute to a notification handler
async def connect(device_controller):
    client = BleakClient(device_controller)
    try:
        await client.connect()
        if client.is_connected:
            return client
        else:
            print("Failed to connect.")
            return None
    except Exception as e:
        print(f"Failed to connect to {device_controller}: {e}")
        return None
    

def load_config():
    global config
    config_parser = configparser.ConfigParser()
    config_parser.read("config.ini")

    if "Controller" in config_parser:
        if "type" in config_parser["Controller"]:
            config["type"] = int(config_parser["Controller"]["type"])
        if "orientation" in config_parser["Controller"]:
            config["orientation"] = int(config_parser["Controller"]["orientation"])
    else:
        print("No 'Controller' section found in config.ini. Using default values.")


async def init_controller(name, side, orientation, type=0):
    print(f"Scanning for {name} {side}, press the sync button...")
    device = await scan_joycons()

    if device:
        client = await connect(device)
        if client is not None:
            clients.append(client)

            print(f"{name} {side} connected successfully.")

            if type == 0:
                # Notify controller to handle both Joy-Cons, because the controller is connected
                await handle_duo_joycons(client, side)

            elif type == 1:
                await handle_single_joycon(client, side, orientation)

            elif type == 2:
                await handle_single_joycon(client, side, orientation)

        else:
            print(f"Failed to connect {name} {side}.")
    else:
        print(f"Joy-Con {name} {side} not found.")

async def main():
    try:
        os.system("cls" if os.name == "nt" else "clear")
        load_config()

        if(not config["orientation"] == 0 and not config["orientation"] == 1):
            print("Invalid orientation in config.ini. Please set 'orientation' to 0 (Vertical) or 1 (Horizontal).\nDefaulting to vertical.")
            config["orientation"] = 0  # Default to vertical if invalid


        if config["type"] == 0:
            await init_controller("Joy-Con", "Left", config["orientation"], 0)
            await init_controller("Joy-Con", "Right", config["orientation"], 0)
        elif config["type"] == 1:
            await init_controller("Joy-Con", "Left", config["orientation"], 1)
        elif config["type"] == 2:
            await init_controller("Joy-Con", "Right", config["orientation"], 2)
        else:
            print("Invalid controller type in config.ini. Please set 'type' to 0, 1, or 2.\nDefaulting to both Joy-Cons.")
            await init_controller("Joy-Con", "Left", config["orientation"], 0)
            await init_controller("Joy-Con", "Right", config["orientation"], 0)
        
        while True:
            await asyncio.sleep(1)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Interrupting...")

    finally:
        print("Disconnecting controllers...")
        for client in clients:
            if client.is_connected:
                await client.disconnect()
        print("All controllers disconnected.")



async def handle_duo_joycons(client, side):
    from handles.duo_joycon import notify_duo_joycons
    data = bytes.fromhex('09910007000800000100000000000000') # Found in : https://github.com/darthcloud/BlueRetro/
    await client.write_gatt_char(UUID_CMD, data)

    def notification_handler(sender, data):
        notify_duo_joycons(client, side, data)

    await client.start_notify(UUID_NOTIFY, notification_handler)

async def handle_single_joycon(client, side, orientation):
    from handles.single_joycon import notify_duo_joycons
    data = bytes.fromhex('09910007000800000100000000000000') # Found in : https://github.com/darthcloud/BlueRetro/
    await client.write_gatt_char(UUID_CMD, data)

    def notification_handler(sender, data):
        notify_duo_joycons(client, side, orientation, data)

    await client.start_notify(UUID_NOTIFY, notification_handler)




#Used to get the manufacturer data from joycons
#async def scan_all():
    #devices = await BleakScanner.discover()
    #for d in devices:
    #    md = d.metadata.get("manufacturer_data", {})
    #    if md:
    #        for manu_id, data_bytes in md.items():
    #            print(f"Device: {d.name}, ID: {manu_id}, Data: {data_bytes.hex()}")


if __name__ == "__main__":
    asyncio.run(main())