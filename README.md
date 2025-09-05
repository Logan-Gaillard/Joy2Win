# 🎮 Joy-Con 2 Windows compatibility

This is a little project in python to allows you to connect your **Nintendo Switch 2 Joy-Con** to a Windows PC using BLE and vJoy.

---

## 🚀 Installation

1. Clone this repository :

   ```bash
   git clone https://github.com/Logan-Gaillard/Joy2Win.git
   cd Joy2Win
   ```

2. Install Python dependencies :

   ```
   pip install bleak pyvjoy pynput pyvjoystick
   ```

3. Install vJoy and VIGEM:
   https://sourceforge.net/projects/vjoystick/

4. Configure vJoy :
   - Open "Configure vJoy"
   - Select controller 1
   - Set 24 buttons or higher
   - Restart your computer

## 🕹️ Usage

1. Duplicate the `config-template.ini` file, rename it to `config.ini`, and edit it according to your needs.

2. Run the script in the Joy2Win directory (wherever you cloned it):

   ```bash
   python main.py
   ```

3. Follow the instructions displayed when the script starts.

4. Confirm that the controller is connected. - Search in Windows for "Set up USB game controllers". - You should see "vJoy Device" there.

Your Joy-Con 2 controllers are now connected to your Windows computer.

## ✨ Features

- Select usage type and Joy-Con 2 orientation (Single, Both, Vertically/Horizontally)
- Player LED indicator support
- Vibration feedback when Joy-Con 2 is successfully connected
- Motion sensor support (DSU server)
- Mouse control (can be alternated with controller mode)
- Xbox/PlayStation compatibility

## Repositories

- [pyvjoy](https://github.com/tidzo/pyvjoy)
- [pyvjoystick](https://github.com/fsadannn/pyvjoystick)
- [switch2_controller_research](https://github.com/ndeadly/switch2_controller_research)

## **NOTICE !**

**THIS REPO IS A TEMPORARY PROJECT**  
Currently, Joy-Con 2 controllers only work on Windows. Other operating systems are not supported due to the way the controllers communicate.

On this project's [community Discord server](https://discord.gg/gegfNZ5Ucz), some people are working hard to figure out how Switch 2 controllers communicate.

> [!WARNING]  
> **⚠ This Discord server is NOT part of this project, and NO support for this program will be provided there.**  
> For questions or issues, please contact `octokling` on Discord or open an Issue here.

> [!NOTE]  
> I am not a Bluetooth communication expert. I have been helped many times to understand how it works.

## Author

Made by **Octokling**

Helped by :

- narr_the_reg
- ndeadly
