import socket
import struct
import zlib
import random

SERVER_ADDR = ("192.168.1.150", 26760)
PROTOCOL_VERSION = 1001
CLIENT_ID = random.randint(0, 0xFFFFFFFF)

def crc32(data):
    return zlib.crc32(data) & 0xFFFFFFFF

def build_packet(msg_type, payload=b""):
    header = bytearray()
    header += b"DSUC"  # From client
    header += struct.pack("<H", PROTOCOL_VERSION)
    header += struct.pack("<H", len(payload) + 4)  # length excl. header
    header += b"\x00\x00\x00\x00"  # CRC placeholder
    header += struct.pack("<I", CLIENT_ID)
    header += struct.pack("<I", msg_type)
    full = header + payload
    crc = crc32(full)
    full[8:12] = struct.pack("<I", crc)
    return full

def send_request_controller_info(sock):
    payload = struct.pack("<iBBBB", 4, 0, 1, 2, 3)  # ask for slots 0-3
    packet = build_packet(0x100001, payload)
    sock.sendto(packet, SERVER_ADDR)
    print("Sent 0x100001: controller info request")

def send_request_data_stream(sock, slot=0):
    payload = struct.pack("<BB6s", 1, slot, b"\x00"*6)  # slot-based
    packet = build_packet(0x100002, payload)
    sock.sendto(packet, SERVER_ADDR)
    print(f"Sent 0x100002: start data stream for slot {slot}")

def parse_controller_data(data):
    if len(data) < 77:
        return
    slot = data[0]
    connected = data[11]
    if not connected:
        return

    packet_id = struct.unpack("<I", data[12:16])[0]
    buttons1 = data[16]
    buttons2 = data[17]
    lx, ly = data[20], data[21]
    rx, ry = data[22], data[23]
    ax = struct.unpack("<f", data[56:60])[0]
    ay = struct.unpack("<f", data[60:64])[0]
    az = struct.unpack("<f", data[64:68])[0]
    gx = struct.unpack("<f", data[68:72])[0]
    gy = struct.unpack("<f", data[72:76])[0]
    gz = struct.unpack("<f", data[76:80])[0]

    print(f"[Slot {slot}] Packet {packet_id}")
    print(f"  Buttons: {bin(buttons1)} {bin(buttons2)}")
    print(f"  Left Stick: ({lx}, {ly}) | Right Stick: ({rx}, {ry})")
    print(f"  Accel: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f}")
    print(f"  Gyro : X={gx:.2f}, Y={gy:.2f}, Z={gz:.2f}")
    print("-" * 40)

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))  # use any port

    send_request_controller_info(sock)
    send_request_data_stream(sock, slot=0)

    while True:
        data, addr = sock.recvfrom(2048)
        if data[:4] != b"DSUS":
            continue

        print(f"Received data from {addr}: {data.hex()}")

if __name__ == "__main__":
    run_client()