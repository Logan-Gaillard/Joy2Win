import asyncio, os
from bleak import BleakClient, BleakScanner
from config import Config
from enum import Enum
from program.controller_command import ControllerCommand, UUID_NOTIFY, UUID_CMD_RESPONSE
from program.dsu.dsu_server import main_dsu

from program.controller_def import ControllerManager, JoyCon, JoyConSide, ControllerType


if(os.name != 'nt'): # Si le système d'exploitation n'est pas Windows
    print("This application is only supported on Windows.")
    exit(1) # Quitter le programme

# Manufacture Joy-Con 2
manufact = {
    "id": 0x0553,  # Nintendo Co., Ltd. (https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/)
    "joycon2-data-prefix": bytes([0x01, 0x00, 0x03, 0x7e, 0x05])  # Le prefix de la donnée du fabricant pour Joy-Con 2
}

# Lecture de la configuration depuis avec config.ini
config = Config().getConfig()

# Manageur des manettes connectés
controllerManager = None


##TODO 
# Main function
# Scan function
# Connect function
# Notifier handler function
# Disconnect function

async def scan():
    print("Scanning for Controllers...")
    devices = await BleakScanner.discover()
    for device in devices:
        print (device.details)


async def main():
    global controllerManager

    if config["controller"] == 0: #Both joycons
        controllerManager = ControllerManager(ControllerType.JOYCON)

        await scan()


    elif config["controller"] == "1": #Left joycon
        controllerManager = ControllerManager(ControllerType.JOYCON)

    elif config["controller"] == 2: #Right joycon
        controllerManager = ControllerManager(ControllerType.JOYCON)

    # Garder le programme en cours d'exécution pour recevoir les notifications
    while True:
        await asyncio.sleep(1)

asyncio.run(main())