from enum import Enum
from typing import List

class ControllerType(Enum):
    JOYCON =  0
    SINGLE_JOYCON = 1

class JoyConSide(Enum):
    NONE : "None"
    LEFT = "Left"
    RIGHT = "Right"

class Controller:
    def __init__(self, controllerType: ControllerType, client):
        self.controllerType = controllerType
        self.client = client 
    
    def getInfo(self):
        return {
            "Type": str(self.controllerType)
        }
    

class JoyCon(Controller):
    def __init__(self, side: JoyConSide, orientation: str):
        super().__init__(ControllerType.JOYCON)
        self.side = side
        self.orientation = orientation

    def getInfo(self):
        return {
            "Type": self.controllerType,
            "Side": self.side,
            "Orientation": self.orientation
        }

class ControllerManager:
    def __init__(self, controllerType: ControllerType):
        self.controllers: List[Controller] = []
        self.configControllerType = controllerType

    def addController(self, controller: Controller):
        self.controllers.append(controller)

    def removeController(self, client):
        self.controllers = [ctrl for ctrl in self.controllers if ctrl.client != client]

    def getControllers(self):
        return self.controllers

    def count(self): 
        return len(self.controllers)
    
    def listInfo(self):
        return [ctrl.getInfo for ctrl in self.controllers]
    
    def getConfigControllerType(self):
        return self.configControllerType