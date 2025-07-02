# 🎮 Joy-Con 2 to Xbox 360 Virtual Controller

This temporary project allows you to connect your **Nintendo Switch 2 Joy-Con** to a Windows PC and emulate an **Xbox 360 controller** using BLE and ViGEm.

---

## 🚀 Installation

1. Clone this repository :
   ```bash
   git clone https://github.com/Logan-Gaillard/jc2x360.git
   cd jc2x360
   ```

2. Install Python dependencies :
    ```
    pip install bleak pyvjoystick
    ```

3.  Install the ViGEmBus driver (required for virtual controllers) :
    https://github.com/ViGEm/ViGEmBus/releases

4.  Install vJoy :
    https://sourceforge.net/projects/vjoystick/

## 🕹️ Usage

1. Copy the `config-exemple.ini` file, rename it to `config.ini`, and edit it according to your needs.

2. Run the script :
    ```bash
    python main.py
    ```

3. Follow the instructions displayed when the script starts.

Your Joy-Con will now act like a virtual Xbox 360 controller.

## Author
Made by **Octokling**