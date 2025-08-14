# 🎮 Joy-Con 2 Windows compatibility

This temporary project allows you to connect your **Nintendo Switch 2 Joy-Con** to a Windows PC using BLE and vJoy.

Why it's temporary ?

My repo is just a little to

---

## 🚀 Installation

1. Clone this repository :
   ```bash
   git clone https://github.com/Logan-Gaillard/Joy2Win.git
   cd Joy2Win
   ```

2. Install Python dependencies :
    ```
    pip install bleak pyvjoy pynput
    ```

4.  Install vJoy :
    https://sourceforge.net/projects/vjoystick/

5. Configure vJoy :  
        - Open "Configure vJoy"  
        - Select controller n°1  
        - Set 24 buttons or higher  
        - Restart your computer  

## 🕹️ Usage

1. Copy the `config-exemple.ini` file, rename it to `config.ini`, and edit it according to your needs.

2. Run the script :
    ```bash
    python main.py
    ```

3. Follow the instructions displayed when the script starts.

Your Joy-Con 2 will be compatible with your Windows.

## ✨ Features

- Select usage type and Joy-Con orientation (single or paired, horizontal or vertical (only for single joycon))
- Player LED indicator support (By default, player 1)
- Vibration feedback when Joy-Con is successfully connected.
- Use motion sensor with DSU server (For emulators)
- Automatic mouse control

## Repositories
- [pyvjoy](https://github.com/tidzo/pyvjoy)
- [switch2_controller_research](https://github.com/ndeadly/switch2_controller_research)

## Author
Made by **Octokling**

Helped by :  
- narr_the_reg
- ndeadly
