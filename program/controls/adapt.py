import pyvjoy
vjoy = pyvjoy.VJoyDevice(1)  # vJoy ID 1

Controls = {
    "Left": {
        "ZL": 1, "L": 3, "L3": 19,
        "Right": 9, "Down": 10, "Up": 11,
        "Left": 12, "Minus": 14, "SLL": 17,
        "SRL": 18, "Capture": 22,
    },
    "Right": {
        "ZR": 2, "R": 4, "R3": 20,
        "A": 5, "B": 6, "X": 7,
        "Y": 8,"Plus": 13, "SRR": 15,
        "SLR": 16, "Home": 21, "GameChat": 23,
    }
}

def adapt_control(controller, side):
    for btnName, btnValue in Controls[side].items():
        pressed = controller.buttons.get(btnName, False)
        vjoy.set_button(btnValue, pressed)

        if(side == "Left"):
            vjoy.set_axis(pyvjoy.HID_USAGE_X, controller.analog_stick["X"])
            vjoy.set_axis(pyvjoy.HID_USAGE_Y, controller.analog_stick["Y"])
        elif(side == "Right"):
            vjoy.set_axis(pyvjoy.HID_USAGE_RX, controller.analog_stick["X"])
            vjoy.set_axis(pyvjoy.HID_USAGE_RY, controller.analog_stick["Y"])