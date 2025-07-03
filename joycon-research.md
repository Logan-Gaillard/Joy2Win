# Joy-Con 2 - BLE UUID Testing & Command Analysis

## Tested UUIDs (Captured on Joy-Con 2 (R))

| UUID | Description |
|------|-------------|
| `fa19b0fb-cd1f-46a7-84a1-bbb09e00c149` | Not crash, does nothing |
| `649d4ac9-8eb7-4e6c-af44-1ea54fe5f005` | **Command handler** ✅ |
| `65a724b3-f1e7-4a61-8078-a342376b27ff` | Vibrates + **Crash** (Suspected: HID Vibration?) |
| `4147423d-fdae-4df7-a4f7-d23e5df59f8d` | Not crash, does nothing |
| `c765a961-d9d8-4d36-a20a-5315b111836a` | **Response handler** Can be notify |
| `640ca58e-0e88-410c-a7f3-426faf2b690b` | Cannot write |
| `d3bd69d2-841c-4241-ab15-f86f406d2a80` | Cannot write |
| `ab7de9be-89fe-49ad-828f-118f09df7fde` | Cannot write |
| `ab7de9be-89fe-49ad-828f-118f09df7fdf` | **Crash** ❌ |

---

## Command Example: Set LED

```09 91 00 07 00 08 00 00 0X 00 00 00 00 00 00 00```

| Byte(s) | Meaning |
|---------|--------|
| `09` | Command: Set LED |
| `91` | Request type |
| `00/01` | 00: USB ? / 01: BLE ? - Request interface (BLE?) |
| `07` | Sub-command: Set LED |
| `00 08 00 00` | Unknown |
| `0X` | LED bitmask (4 bits = 4 LEDs, combine to select) |
| `00 00 00 00 00 00 00` | Padding / reserved  / Jamming ? |

---

## Response (on UUID: `649d4ac9-8eb7-4e6c-af44-1ea54fe5f005`)
```WW XX YY ZZ 10 78 00 00```

| Byte | Meaning |
|------|--------|
| `WW` | Echo of the command sent |
| `XX` | Status (00 = error, 01 = success, 04 = unknown) |
| `YY` | Echo of the resquest interface |
| `ZZ` | Sub-command echoed |
| `10 78 00 00` | May can change ? |

---

## Reference

- LED command based on: [BlueRetro GitHub Repo](https://github.com/darthcloud/BlueRetro/)

## Notice

- I don't have any nRF dongle to sniff Bluetooth data.  
- I'm not an expert in reverse engineering; theses informations may be incorrect.