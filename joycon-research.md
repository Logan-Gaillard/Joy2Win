# Testing UUID :
`fa19b0fb-cd1f-46a7-84a1-bbb09e00c149 : Not crash and do nothing`
`649d4ac9-8eb7-4e6c-af44-1ea54fe5f005 : Command`
`65a724b3-f1e7-4a61-8078-a342376b27ff : Vibrate + Crash` (HID Vibration ? )
`4147423d-fdae-4df7-a4f7-d23e5df59f8d : Not crash and do nothing`
`c765a961-d9d8-4d36-a20a-5315b111836a : Can't write`
`640ca58e-0e88-410c-a7f3-426faf2b690b : Can't write`
`d3bd69d2-841c-4241-ab15-f86f406d2a80 : Can't write`
`ab7de9be-89fe-49ad-828f-118f09df7fde : Can't write`
`ab7de9be-89fe-49ad-828f-118f09df7fdf : Crash`

With the repo : https://github.com/darthcloud/BlueRetro/

What i know with this ? :

Set led:
09910007000800000100000000000000

09 = Command Set Led
91 = Request Type: Request 
00|01 = Request Interface: BLE (I need to check what is the difference)
07 = Sub-Command Set Led
00 08 00 00 = ???
0X (X= 0 to F) = Led (4 bits for 4 leds combines i think)
00 00 00 00 00 00 00 = Jamming for other longer commands ?