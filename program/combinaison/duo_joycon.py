from program.controllers.JoyconL import JoyConLeft
from program.controllers.JoyconR import JoyConRight

from program.dsu.dsu_server import controller_update

from config import Config

# Controls
from program.controls.mouse import mouse_control
from program.controls.adapt import adapt_control
from program.controls.playstation import playstation_control
from program.controls.xbox import xbox_control

import pyvjoy


# Initialize Joy-Con controllers
joyconLeft = JoyConLeft()
joyconRight = JoyConRight()

# Read the configuration from config.ini
config = Config().getConfig()

# Initialize vJoy device
vjoy = pyvjoy.VJoyDevice(1)  # vJoy ID 1

jcMouseMode = None  # None



def getState(joycon):
    if ((joycon.mouse["distance"] in ["00", "01", "02"] and (jcMouseMode == None or jcMouseMode == joycon)) and config['mouse_mode'] == 1) or config['mouse_mode'] == 2:
        return "mouse"
    
    if config['controller_type'] == 0:
        return "adapt"
    elif config['controller_type'] == 1:
        return "playstation"
    elif config['controller_type'] == 2:
        return "xbox"

async def update(controllerSide, joycon):
    global jcMouseMode
    state = getState(joycon)

    if state == "mouse":
        jcMouseMode = joycon
        return mouse_control(0, 0, joycon)
    elif jcMouseMode == joycon:
        jcMouseMode = None
    

    if state == "adapt":
        return adapt_control(joycon, controllerSide)
    elif state == "playstation":
        return playstation_control(joycon, controllerSide)
    elif state == "xbox":
        return xbox_control(joycon, controllerSide)



async def notify_duo_joycons(client, side, data):
    if side == "Left":
        await joyconLeft.update(data)
        await update(side, joyconLeft)
    elif side == "Right":
        await joyconRight.update(data)
        await update(side, joyconRight)
    else:
        print("Unknown controller side.")
    
    return client