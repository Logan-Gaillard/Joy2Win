import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from program.controllers.controllers import BaseController

COMMAND_TYPE = {
    # Example command structure
    # "COMMAND_NAME": {
    #   "data": "0000000XYZ",
    #   "args": [ (List of required arguments for the command)
    #       {"name": "ARG_NAME", (Name of the argument)
    #        "letter": "X", (Single letter identifier to replace in the hex string)
    #       "length": 2}, (Length of the argument in characters for validation)
    #   ]
    # }
    "SET_LED": {"data": "0991010700080000X00000000000000", "args": [{"name": "led_mask", "letter": "X", "length": 2}]},
    "PLAY_VIBRATION_SAMPLE": {"data": "0A91010200040000X000000","args": [{"name": "id", "letter": "X", "length": 2}]},


    "SET_FEATURE": {"data": "0C91010200040000X000000","args": [{"name": "flags", "letter": "X", "length": 2}]},
    "ENABLE_FEATURE": {"data": "0C91010400040000X000000","args": [{"name": "flags", "letter": "X", "length": 2}]},
}


class ControllerCommands:
    def __init__(self, controller):
        self.controller: BaseController = controller
        self.waiting_response = False
        self.response_data = None

    async def send_command(self, commandType, args=None):
        try:

            command = COMMAND_TYPE[commandType] # Get the command details
            if command is None:
                print(f"Command {commandType} not found in COMMAND_TYPE.")
                return False
            
            data = command["data"] # Get the command data

            if command.get("args") and args: # If command requires arguments
                for arg in command["args"]: # Get all required arguments
                    letter = arg["letter"] # Get the letter to replace in hex string
                    name = arg["name"] # Get the argument name
                    if name in args: # Check args has the argument
                        value = str(args[name])
                        if len(value) == arg["length"]: # Check if the argument length is valid
                            data = data.replace(letter, value)
                        else: # If the argument length is invalid
                            raise ValueError(f"Invalid argument length for: {name}")
                    else: # If the argument is missing
                        raise ValueError(f"Missing argument: {name}")
                    
            data_bytes = bytes.fromhex(data)

            print(f"Sending command: {commandType} with data: {data}, bytes: {data_bytes.hex()}")

            await self.controller.controller_client.write_gatt_char(self.controller.command_handle, data_bytes)
        
        except Exception as e:
            print(f"Error occurred while sending command: {e}")

    async def send_command_and_wait_response(self, commandType, args=None):
        self.waiting_response = True

        await self.send_command(commandType, args)

        while self.waiting_response:
            await asyncio.sleep(0.1)

        response = self.response_data
        self.response_data = None

        return response

    async def receive_response(self, _, data):
        # print(f"Received response: {data.hex()}")
        self.response_data = data
        self.waiting_response = False