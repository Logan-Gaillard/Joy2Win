import asyncio, traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from program.controllers.controllers import BaseController

COMMAND_TYPE = {
    "SET_LED": {
        #"data": "09 91 01 07 00 08 00 00 X 00 00 00 00 00 00 00",
        "data" : [0x09, 0x91, 0x01, 0x07, 0x00, 0x08, 0x00, 0x00, "led_mask", 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        "args": [
            {"name": "led_mask", "size": 0x1}
        ]
    },

    "PLAY_VIBRATION_SAMPLE": {
        #"data": "0A 91 01 02 00 04 00 00 X 00 00 00",
        "data": [0x0A, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, "id", 0x00, 0x00, 0x00],
        "args": [
            {"name": "id", "size": 0x1}
        ]
    },

    "SET_FEATURE": {
        #"data": "0C 91 01 02 00 04 00 00 X 00 00 00",
        "data": [0x0C, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, "flags", 0x00, 0x00, 0x00],
        "args": [
            {"name": "flags", "size": 0x1}
        ]
    },

    "ENABLE_FEATURE": {
        #"data": "0C 91 01 04 00 04 00 00 X 00 00 00",
        "data": [0x0C, 0x91, 0x01, 0x04, 0x00, 0x04, 0x00, 0x00, "flags", 0x00, 0x00, 0x00],
        "args": [
            {"name": "flags", "size": 0x1}
        ]
    },

    "READ_DATA": {
        #"data": "02 91 01 04 00 08 00 00 X 7E 00 00 Y",
        "data": [0x02, 0x91, 0x01, 0x04, 0x00, 0x08, 0x00, 0x00, "size", 0x7E, 0x00, 0x00, "address"],
        "args": [
            {"name": "size", "size": 0x1},
            {"name": "address", "size": 0x4}
        ]
    },
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

                final_data = []

                arg_bytes_map = {}

                for arg_def in command["args"]:
                    name = arg_def["name"]
                    size = arg_def["size"]
                    val = args.get(name, 0)

                    if val == 0:
                        raise ValueError(f"Missing required argument: {name}")
                    
                    actual_size = (val.bit_length() + 7) // 8
                    # print(f"Argument {name}: value={hex(val)}, size={size} bytes, actual_size={actual_size} bytes")
                
                    if actual_size > size:
                        raise ValueError(f"Argument {name} exceeds maximum size. Expected {size} - got {actual_size}.")
                    
                    arg_bytes_map[name] = list(val.to_bytes(size))

                for item in command["data"]:
                    if isinstance(item, str):
                        final_data.extend(arg_bytes_map[item])
                    else:
                        final_data.append(item)

            data_bytes = bytes(final_data if command.get("args") and args else data)                    

            # print(f"Sending command: {commandType} with data: {data_bytes.hex()}")

            await self.controller.controller_client.write_gatt_char(self.controller.command_handle, data_bytes)
        
        except Exception as e:
            print(f"Error occurred while sending command: {e}")
            traceback.print_exc()

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