import asyncio

UUID_NOTIFY = "ab7de9be-89fe-49ad-828f-118f09df7fd2"
UUID_CMD = "649d4ac9-8eb7-4e6c-af44-1ea54fe5f005"
UUID_CMD_RESPONSE = "c765a961-d9d8-4d36-a20a-5315b111836a"

COMMAND_TYPE = {
    "JOY2_CONNECTED_VIBRATION": {"data": "0A9101020004000003000000", "wait_response": True, "args": None},

    "JOY2_SET_PLAYER_LED": {"data": "09910007000800000X00000000000000", "wait_response": True, "args": [{"name": "led_player", "letter": "X", "length": 1}]},

    "JOY2_INIT_SENSOR_DATA": {"data": "0c91010200040000FF000000", "wait_response": True, "args": None}, #Thanks to "Narr the Reg" and "ndeadly"

    "JOY2_FINALIZE_SENSOR_DATA": {"data": "0c91010300040000FF000000", "wait_response": True, "args": None}, #Thanks to "Narr the Reg" and "ndeadly"

    "JOY2_START_SENSOR_DATA": {"data": "0c91010400040000FF000000", "wait_response": True, "args": None}, #Thanks to "Narr the Reg" and "ndeadly"

    # Save mac address
    # Found info : switch2_controller_research by ndeadly
    "JOY2_SAVE_MC_ADDR_STEP1": {"data": "15910101000e00000002XY", "wait_response": True, "args": [{"name": "mac-addr1", "letter": "X", "length": 12},{"name": "mac-addr2", "letter": "Y", "length": 12}]},
    "JOY2_SAVE_MC_ADDR_STEP2": {"data": "15910104001100000008065a60e902e4e102029e3fa39a78d1", "wait_response": True, "args": None},
    "JOY2_SAVE_MC_ADDR_STEP3": {"data": "159101020011000000934e580f163aeecfb575fc9136b22fbb", "wait_response": True, "args": None},
    "JOY2_SAVE_MC_ADDR_STEP4": {"data": "159101030001000000", "wait_response": True, "args": None},

}

class ControllerCommand:
    _instance = None
    onSendCmd = False
    cmdAnswered = False
    clientSending = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ControllerCommand, cls).__new__(cls)
        return cls._instance

    async def send_command(self, client, commandType, args=None):
        try:
            if self.onSendCmd:
                return False
            
            self.onSendCmd = True
            self.cmdAnswered = False
            self.clientSending = client

            command = COMMAND_TYPE[commandType] # Get the command details
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

            # Convert hex string to bytes
            data_bytes = bytes.fromhex(data)

            print(f"Sending command: {commandType} with data: {data_bytes.hex()}")

            await client.write_gatt_char(UUID_CMD, data_bytes)
            
            if command["wait_response"]: #If need to wait for a response
                while not self.cmdAnswered:
                    await asyncio.sleep(0.1)

            self.onSendCmd = False
            self.clientSending = None

            return True

        except Exception as e:
            self.onSendCmd = False
            self.clientSending = None
            print(f"Failed to send command: {e}")
            return False

    def receive_response(self, client, data):
        if data and self.clientSending == client:
            self.cmdAnswered = True
