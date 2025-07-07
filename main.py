import asyncio, os
from bleak import BleakClient, BleakScanner
from config import Config
from controller_command import ControllerCommand, UUID_NOTIFY, UUID_CMD_RESPONSE, COMMAND_TYPE

if(os.name != 'nt'):
    print("This application is only supported on Windows.")
    exit(1)

config = Config().getConfig()

# Constants
manufact = {
    "id": 0x0553,  # Nintendo Co., Ltd. (https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/)
    "data-prefix": bytes([0x01, 0x00, 0x03, 0x7e, 0x05])  # Manufacturer data prefix for Joy-Con (I hope this prefix is correct, and it same for everyone)
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

async def handle_duo_joycons(client, side):
    from control_type.duo_joycon import notify_duo_joycons

    async def notification_handler(sender, data):
        asyncio.create_task(notify_duo_joycons(client, side, data))

    def response_handler(sender, data):
        ControllerCommand().receive_response(client, data)

    await client.start_notify(UUID_CMD_RESPONSE, response_handler)

    await initSendControllerCmd(client, "Joy-Con")

    await client.stop_notify(UUID_CMD_RESPONSE)

    await client.start_notify(UUID_NOTIFY, notification_handler)

async def handle_single_joycon(client, side, orientation):
    from control_type.single_joycon import notify_single_joycons

    async def notification_handler(sender, data):
        asyncio.create_task(notify_single_joycons(client, side, orientation, data))

    def response_handler(sender, data):
        ControllerCommand().receive_response(client, data)

    await client.start_notify(UUID_CMD_RESPONSE, response_handler)

    await initSendControllerCmd(client, "Joy-Con")

    await client.stop_notify(UUID_CMD_RESPONSE)

    await client.start_notify(UUID_NOTIFY, notification_handler)

"""

"""
async def initSendControllerCmd(client, controllerName):
    controllerCommand = ControllerCommand()
    if(controllerName == "Joy-Con"):
        await controllerCommand.send_command(client, "JOY2_CONNECTED_VIBRATION")
        # Convert binary string (e.g., "0101") to hexadecimal string (e.g., "5")

        if len(config['led_player']) != 4 or not all(c in '01' for c in config['led_player']): #Length is 4 and only contains '0' and '1'
            print("LED player incorrectly set in config.ini, defaulting to 0001.")
            config['led_player'] = "0001"

        await controllerCommand.send_command(client, "JOY2_SET_PLAYER_LED", {"led_player": format(int(config['led_player'], 2), 'x')}) # Convert binary string to hex string
        await controllerCommand.send_command(client, "JOY2_INIT_SENSOR_DATA")
        await controllerCommand.send_command(client, "JOY2_START_SENSOR_DATA")

    


async def main():
    try:
        if(not config['orientation'] == 0 and not config['orientation'] == 1):
            print("Invalid orientation in config.ini. Please set 'orientation' to 0 (Vertical) or 1 (Horizontal).\nDefaulting to vertical.")
            config['orientation'] = 0  # Default to vertical if invalid


        if config['type'] == 0:
            await init_controller("Joy-Con", "Left", config['orientation'], 0)
            await init_controller("Joy-Con", "Right", config['orientation'], 0)
        elif config['type'] == 1:
            await init_controller("Joy-Con", "Left", config['orientation'], 1)
        elif config['type'] == 2:
            await init_controller("Joy-Con", "Right", config['orientation'], 2)
        else:
            print("Invalid controller type in config.ini. Please set 'type' to 0, 1, or 2.\nDefaulting to both Joy-Cons.")
            await init_controller("Joy-Con", "Left", config['orientation'], 0)
            await init_controller("Joy-Con", "Right", config['orientation'], 0)

        while True:
            await asyncio.sleep(1)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Interrupting...")

    finally:
        print("Disconnecting controllers...")
        for client in clients:
            await client.disconnect()
        print("All controllers disconnected.")


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