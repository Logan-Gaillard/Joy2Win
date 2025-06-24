# 🎮 Joy-Con 2 to Xbox 360 Virtual Controller

This temporary project allows you to connect your **Nintendo Switch 2 Joy-Con** to a Windows PC and emulate an **Xbox 360 controller** using BLE and ViGEm.

---

## 🚀 Installation

1. Clone this repository :
   ```bash
   git clone https://github.com/your-name/jc2x360.git
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
1. Open main.py in your code editor.

2. Replace MAC_JOYCON_LEFT and MAC_JOYCON_RIGHT with the MAC address of your Joy-Con 2.

3. Hold the sync button until the LED search animation starts.

4. Run the script :
    ```bash
    python main.py
    ```

Your Joy-Con will now act like a virtual Xbox 360 controller.

## 🔍 How to find your Joy-Con MAC address
1. Connect the Joy-Con to your Switch.

2. Go to System Settings > Controllers and Sensors.

3. Select Bluetooth Devices.

4. The MAC address will appear at the bottom of the screen.

## Author
Made by **Octokling**