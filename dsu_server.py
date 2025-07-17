import socket
import struct
import random
import zlib
import asyncio
import threading

IP_ADDRESS = '0.0.0.0'
PORT = 26760
SERVER_ID = random.randint(0, 0xFFFFFFFF)

sendWaitClientMsg = False
sendClientConnectedMsg = False

idPacket = 0
isReadyToSend = False
DSUClientAddr = None

sock = None

def incrementIdPacket():
    global idPacket
    idPacket += 1
    if idPacket > 0xFFFFFFFF:  # Reset if it exceeds 32-bit unsigned int
        idPacket = 1
    return idPacket

## DSU Server response functions: Controller information ##
async def responseInfoController():
    slotInfo = bytearray([
        0x01, 0x00, 0x10, 0x00, # Message type: 0x01001000 (Information about controllers) | 4 bytes
        0x00, # Slot ID | 1 byte
        0x02, # Connected (0x02) or not connected (0x00) | 1 byte
        0x02, # Type gyro (0x02 = complet) | 1 byte
        0x02, # Type de connexion (0x02 = Bluetooth) | 1 byte
        *bytes.fromhex('AABBCCDDEEFF')[::-1], # Serial number (reversed) | 6 bytes
        0x05, # Type de manette (0x05 = Pro Controller) | 1 byte
        0x00  # always 0x00 | 1 byte
        # Total length: 12 bytes
    ])

    # Ensure slotInfo is exactly 12 bytes
    if len(slotInfo) != 12 + 4:
        raise ValueError(f"slotInfo length is {len(slotInfo)}, expected 12")

    header = bytearray([
        *b'DSUS', # Header identifier: 'DSUS' | 4 bytes
        0xE9, 0x03, # Version 0xE903 | 2 bytes
        0x10, 0x00, # Length of slotInfo (payload) | 2 bytes, always 12
        0x00, 0x00, 0x00, 0x00, # CRC placeholder (4 octets zéro) | 4 bytes
        *SERVER_ID.to_bytes(4, 'little'), # Server ID (Uint32, 4 bytes, little endian) | 4 bytes
        # Total length: 16 bytes
    ])

    struct_response = header + slotInfo # Assemble pour le calcul (avec CRC à 0)
    crc = zlib.crc32(struct_response) & 0xFFFFFFFF # Calcul du CRC sur le paquet avec le header
    header[8:12] = struct.pack('<I', crc) # Met le vrai CRC dans le header original
    struct_response = header + slotInfo # Recrée le paquet complet avec le bon CRC

    return struct_response

## DSU Server response functions: Controller data ##
async def responseDataController(timestampMotion, accel, gyro):
    global idPacket
    idPacket = incrementIdPacket()  # Increment packet ID

    slotInfo = bytearray([
        0x02, 0x00, 0x10, 0x00, # Message type: 0x02001000 (Ask data from controller)
        0x00, # Slot ID | 1 bytes
        0x02, #Connected (0x02) or not connected (0x00) | 1 bytes
        0x02, #Type gyro (0x02 = complet) | 1 bytes
        0x02, #Type de connexion (0x02 = Bluetooth) | 1 bytes
        *bytes.fromhex('AABBCCDDEEFF')[::-1], # Serial number (reversed) | 6 bytes
        0x05, # Type de manette (0x05 = Pro Controller) | 1 bytes
        # Total length: 11 bytes
    ])

    controllerStats = bytearray([
        0x01,  # connected
        *idPacket.to_bytes(4, 'little'),  # packet ID
        0b00000000,  # buttons byte 1
        0b00000000,  # buttons byte 2
        0x00,  # HOME
        0x00,  # Touch
        128, 128,  # Left Stick X/Y
        128, 128,  # Right Stick X/Y
        0, 0, 0, 0,  # analog D-PAD L/D/R/U
        0, 0, 0, 0,  # analog Y/B/A/X
        0, 0, 0, 0,  # analog R1/L1/R2/L2
        0, 0, 0, 0, 0, 0,  # touch 1 (inactive)
        0, 0, 0, 0, 0, 0,  # touch 2 (inactive)
        *b'\x00\x00\x00\x00', *struct.pack("<i", timestampMotion), #  4 null bytes because + Timestamp (value already in bytes, lenght 4 bytes, little endian) | 8 bytes
        *struct.pack("<3f", accel["X"], accel["Y"], accel["Z"]), # Accelerometer data (already in bytes, length 4 bytes) | 4 bytes
        *struct.pack("<3f", gyro["X"], gyro["Y"], gyro["Z"]) # Gyroscope data (already in bytes, length 4 bytes) | 4 bytes
    ])

    data = slotInfo + controllerStats

    header = bytearray([
        *b'DSUS',
        0xE9, 0x03, # Version 0xE903
        len(data) & 0xFF, (len(data) >> 8) & 0xFF,
        0x00, 0x00, 0x00, 0x00, # CRC placeholder (4 octets zéro)
        *SERVER_ID.to_bytes(4, 'little'),
    ])

    struct_response = header + data # Assemble pour le calcul (avec CRC à 0)
    crc = zlib.crc32(struct_response) & 0xFFFFFFFF # Assemble pour le calcul (avec CRC à 0)
    header[8:12] = struct.pack('<I', crc) # Met le vrai CRC dans le header original
    struct_response = header + data # Recrée le paquet complet avec le bon CRC

    return struct_response

## Send message to DSU client ##
async def send_message(data, addr):
    #print(f"Sending data to {addr}: {data.hex()}")
    sock.sendto(data, addr)
    #print(f"Sent data to {addr}: {data.hex()}")

## Initialize DSU server ##
async def wait_response():
    global DSUClientAddr, isReadyToSend, sendWaitClientMsg, sendClientConnectedMsg
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            #print(f"Received data from {addr}: {data.hex()}")
            if len(data) < 20:
                print(f"Received too short packet: {data.hex()}")
                continue
            header = data[0:16] # Lenght 16 bytes
            message_type = data[16:20] # Lenght 4 bytes
            
            if header[0:4] == b'DSUC' and header[4:6] == b'\xE9\x03':

                if message_type.hex() == "01001000": #Information about controllers
                    #print(f"Received DSU client request from {addr}: {data.hex()}, message type: {message_type.hex()}")
                    await send_message(await responseInfoController(), addr)

                elif message_type.hex() == "02001000": #Ask data from controller
                    if sendClientConnectedMsg == False:
                        sendClientConnectedMsg = True
                        isReadyToSend = True
                        DSUClientAddr = addr
                        print("DSU Client connected !")
            else:
                #print(f"Received unexpected data from {addr}: {data.hex()}")
                continue
            # Process data here if needed
        except ConnectionResetError as e:
            DSUClientAddr = None
            isReadyToSend = False
            sendWaitClientMsg = False
            sendClientConnectedMsg = False
            continue
        except socket.timeout:
            continue
    return

async def controller_update(timestampBytes, accelBytes, gyroBytes):
    global DSUClientAddr, isReadyToSend
    if DSUClientAddr is not None and isReadyToSend is True:
        response = await responseDataController(timestampBytes, accelBytes, gyroBytes)
        await send_message(response, DSUClientAddr)

def main_dsu():
    global sendWaitClientMsg, sock
    if sock is None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((IP_ADDRESS, PORT))
        sock.settimeout(1)
        print(f"DSU Server listening on {IP_ADDRESS}:{PORT}")
    if sendWaitClientMsg == False and sock is not None:
        sendWaitClientMsg = True
        print("Waiting for DSU client to connect...")
        threading.Thread(target=lambda: asyncio.run(wait_response()), daemon=True).start()