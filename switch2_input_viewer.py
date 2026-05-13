import os
import sys
import time
import struct
import asyncio
import platform
import pickle

from bleak import BleakScanner, BleakClient
from PyQt5 import QtCore, QtGui, QtWidgets
import qasync
import numpy as np
import pyqtgraph as pg
from matplotlib import rcParams

# NOTE: for some reason all the handles are one less than these in bleak
INPUT_HANDLES = [0x000A, 0x000E]
COMMAND_HANDLES = [0x0014, 0x0016]
COMMAND_RESPONSE_HANDLES = [0x001A, 0x001E]

DEFAULT_FEATURE_FLAGS = 0x03 # 0x2f
DEFAULT_LED_PATTERN = 0b0110


def hexdump(data, width=16):
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
        ascii_repr = ''.join((chr(b) if 32 <= b < 127 else '.') for b in chunk)
        lines.append(f'{i:04X}  {hex_bytes:<{width*3}}  |{ascii_repr}|')
    return '\n'.join(lines)


def unpack_12bit_triplet(data):
    a = (data[0] | ((data[1] & 0x0F) << 8))
    b = ((data[1] >> 4) | (data[2] << 4))
    return a, b


def unpack_12bit_sequence(data):
    out = []
    view = memoryview(data).cast('B')
    for i in range(0, len(view), 3):
        out.extend(unpack_12bit_triplet(view[i:i+3]))

    return out


class FeatureFlagWidget(QtWidgets.QWidget):
    stateChanged = QtCore.pyqtSignal(int)

    BIT_FLAGS = {
        0: "Bit 0: Enable button state reporting",
        1: "Bit 1: Enable analog stick reporting",
        2: "Bit 2: Enable IMU reporting",
        3: "Bit 3: Unknown",
        4: "Bit 4: Enable mouse reporting",
        5: "Bit 5: Enable current reporting",
        6: "Bit 6: Unknown",
        7: "Bit 7: Enable magnetometer reporting"
    }

    def __init__(self):
        super().__init__()

        # Style for inset black square with white margin
        self.setStyleSheet("""
            QCheckBox::indicator {
                border: 1px solid gray;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: black;
                border: 1px solid gray;
                padding: 3px;
            }
        """)

        self.checkboxes = []

        label_layout = QtWidgets.QHBoxLayout()
        checkbox_layout = QtWidgets.QHBoxLayout()
        for i in reversed(range(8)):
            label = QtWidgets.QLabel("Bit " + str(i))
            #label.setAlignment(QtCore.Qt.AlignCenter)
            label_layout.addWidget(label)

            checkbox = QtWidgets.QCheckBox()
            checkbox.setToolTip(FeatureFlagWidget.BIT_FLAGS[i])
            checkbox.setTristate(False)
            checkbox.stateChanged.connect(self.on_state_changed)
            self.checkboxes.insert(0, checkbox)
            checkbox_layout.addWidget(checkbox)

        self.hex_label = QtWidgets.QLabel("Flags: 0x00")
        self.hex_label.setAlignment(QtCore.Qt.AlignCenter)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(label_layout)
        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(self.hex_label)

    def on_state_changed(self, state):
        value = self.get_state()
        self.hex_label.setText(f"Flags: 0x{value:02X}")
        self.stateChanged.emit(value)

    def set_state(self, state):
        for i in range(len(self.checkboxes)):
            self.checkboxes[i].setChecked((state >> i) & 1)

        self.stateChanged.emit(state & 0xff)

    def get_state(self):
        state = 0
        for i in range(len(self.checkboxes)):
            state |= self.checkboxes[i].isChecked() << i

        return state


class StickWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.x = 0x800
        self.y = 0x800
        self.setMinimumSize(100, 100)

        self.calibration = None

    def set_calibration(self, calibration):
        self.calibration = calibration

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) / 2 - 10

        painter.setPen(QtGui.QPen(QtCore.Qt.gray, 1))
        painter.drawLine(center.x(), int(center.y() - radius), center.x(), int(center.y() + radius))
        painter.drawLine(int(center.x() - radius), center.y(), int(center.x() + radius), center.y())
        painter.drawEllipse(center, int(radius), int(radius))

        if self.calibration:
            x = self.x - self.calibration[0]
            x /= self.calibration[4] if x < 0 else self.calibration[2]
            y = self.y - self.calibration[1]
            y /= self.calibration[5] if y < 0 else self.calibration[3]
            dot_x = center.x() + x * radius
            dot_y = center.y() - y * radius
        else:
            x = (self.x - 0x800) / 0x800
            y = (self.y - 0x800) / 0x800
            dot_x = center.x() + x * radius
            dot_y = center.y() - y * radius

        if self.isEnabled():
            painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QtCore.QRectF(dot_x - 4, dot_y - 4, 8, 8))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self.update()
        super().changeEvent(event)


class ButtonGridWidget(QtWidgets.QWidget):
    BUTTON_GRID_FORMATS = [
        # Handle 0x000A, Common
        [
            [(0, 0x80, "ZR"), (0, 0x40, "R"), (0, 0x20, "SL Right"), (0, 0x10, "SR Right"), (0, 0x08, "A"),       (0, 0x04, "B"),      (0, 0x02, "X"),  (0, 0x01, "Y")],
            [(1, 0x80, ""),   (1, 0x40, "C"), (1, 0x20, "Capture"),  (1, 0x10, "Home"),     (1, 0x08, "L‑Stick"), (1, 0x04, "R‑Stick"), (1, 0x02, "+"),  (1, 0x01, "-")],
            [(2, 0x80, "ZL"), (2, 0x40, "L"), (2, 0x20, "SL Left"),  (2, 0x10, "SR Left"),  (2, 0x08, "Left"),    (2, 0x04, "Right"),  (2, 0x02, "Up"), (2, 0x01, "Down")],
            [(3, 0x80, ""),   (3, 0x40, ""),  (3, 0x20, ""),         (3, 0x10, "Headset"),  (3, 0x08, ""),        (3, 0x04, ""),       (3, 0x02, "GL"), (3, 0x01, "GR")],
        ],
        # Handle 0x000E, JoyConR
        [
            [(0, 0x80, "Stick"), (0, 0x40, "+"),  (0, 0x20, "ZR"), (0, 0x10, "R"), (0, 0x08, "X"), (0, 0x04, "Y"), (0, 0x02, "A"), (0, 0x01, "B")],
            [(1, 0x80, "SL"),    (1, 0x40, "SR"), (1, 0x20, ""),   (1, 0x10, "C"), (1, 0x08, ""),  (1, 0x04, ""),  (1, 0x02, ""),  (1, 0x01, "Home")],
        ],
        # Handle 0x000E, JoyConL
        [
            [(0, 0x80, "Stick"), (0, 0x40, "-"),  (0, 0x20, "ZL"), (0, 0x10, "L"), (0, 0x08, "Up"), (0, 0x04, "Left"), (0, 0x02, "Right"), (0, 0x01, "Down")],
            [(1, 0x80, "SL"),    (1, 0x40, "SR"), (1, 0x20, ""),   (1, 0x10, ""),  (1, 0x08, ""),   (1, 0x04, ""),     (1, 0x02, ""),      (1, 0x01, "Capture")],
        ],
        # Handle 0x000E, Pro/GCN
        [
            [(0, 0x80, "R-Stick"), (0, 0x40, "+"), (0, 0x20, "ZR"), (0, 0x10, "R"), (0, 0x08, "X"),  (0, 0x04, "Y"),    (0, 0x02, "A"),       (0, 0x01, "B")],
            [(1, 0x80, "L-Stick"), (1, 0x40, "-"), (1, 0x20, "ZL"), (1, 0x10, "L"), (1, 0x08, "Up"), (1, 0x04, "Left"), (1, 0x02, "Right"),   (1, 0x01, "Down")],
            [(2, 0x80, ""),        (2, 0x40, ""),  (2, 0x20, ""),   (2, 0x10, "C"), (2, 0x08, "GL"), (2, 0x04, "GR"),   (2, 0x02, "Capture"), (2, 0x01, "Home")],
        ]
    ]

    def __init__(self, format=0):
        super().__init__()

        self.labels = {}

        self.layout_format = format
        self.button_grid = ButtonGridWidget.BUTTON_GRID_FORMATS[format]

        self.setup_ui()

    def setup_ui(self):
        # Create input buttons
        layout = QtWidgets.QGridLayout(self)
        # grid.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(2)
        layout.setVerticalSpacing(2)
        layout.setSpacing(2)

        def make_label(txt, is_placeholder=False):
            label = QtWidgets.QLabel(txt)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFixedSize(40, 20)
            if is_placeholder:
                label.setStyleSheet("background:#333;color:#666;border:1px solid #444;border-radius:3px;")
            else:
                label.setStyleSheet(self._style(False))
            return label

        for row, entries in enumerate(self.button_grid):
            for col, (byte_idx, bit_mask, name) in enumerate(entries):
                if not name:
                    label = make_label("", is_placeholder=True)
                    layout.addWidget(label, row, col)
                    continue
                label = make_label(name)
                layout.addWidget(label, row, col)
                self.labels[name] = label

    def _style(self, pressed):
        return (
            "background:#2b2b2b;color:" + ("white" if pressed else "#bbb") +
            ";border:1px solid #555;border-radius:3px;"
        )

    def set_button_state(self, buttons):
        for row in self.button_grid:
            for byte_idx, bit_mask, name in row:
                if not name or byte_idx is None or bit_mask is None:
                    continue
                pressed = bool(buttons[byte_idx] & bit_mask)
                self.labels[name].setStyleSheet(self._style(pressed))

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        for label in self.labels.values():
            if enabled:
                # Use normal style (not pressed)
                label.setStyleSheet(self._style(False))
            else:
                # Greyed-out style
                label.setStyleSheet(
                    "background:#444;color:#777;border:1px solid #555;border-radius:3px;"
                )


class TriggerBarWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setMaximumWidth(20)
        self.setMinimumHeight(90)

    def setValue(self, val):
        self.value = max(0, min(255, val))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QtCore.Qt.transparent)

        bg_color = QtGui.QColor(230, 230, 230) if self.isEnabled() else QtGui.QColor(210, 210, 210)
        painter.setBrush(bg_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(rect)

        if self.isEnabled():
            fill_height = int((self.value / 255) * rect.height())
            fill_rect = QtCore.QRect(0, rect.height() - fill_height, rect.width(), fill_height)

            gradient = QtGui.QLinearGradient(fill_rect.topLeft(), fill_rect.bottomLeft())
            gradient.setColorAt(0.0, QtGui.QColor(255, 100, 100))
            gradient.setColorAt(1.0, QtGui.QColor(150, 0, 0))

            painter.setBrush(gradient)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(fill_rect)

        border_color = QtCore.Qt.black if self.isEnabled() else QtGui.QColor(160, 160, 160)
        painter.setPen(border_color)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))


class TriggersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.calibration = None

        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.left_trigger = TriggerBarWidget()
        self.right_trigger = TriggerBarWidget()
        triggers_layout = QtWidgets.QHBoxLayout()
        triggers_layout.setContentsMargins(0, 0, 0, 0)
        triggers_layout.addWidget(self.left_trigger)
        triggers_layout.addWidget(self.right_trigger)

        label = QtWidgets.QLabel('Analog Triggers')
        label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        label.setAlignment(QtCore.Qt.AlignHCenter)
        layout.addWidget(label)
        layout.addLayout(triggers_layout)

    def set_calibration(self, calibration):
        self.calibration = calibration

    def set_trigger_state(self, triggers):
        if triggers:
            if self.calibration:
                LT = 255 * max(0, (triggers[0] - self.calibration[0]) / (0xff - self.calibration[0]))
                RT = 255 * max(0, (triggers[1] - self.calibration[1]) / (0xff - self.calibration[1]))
            else:
                LT = triggers[0]
                RT = triggers[1]

            self.left_trigger.setValue(LT)
            self.right_trigger.setValue(RT)


class MouseWidget(QtWidgets.QWidget):
     def __init__(self):
         super().__init__()
         self.input_handle = None
         self.labels = []

         self.setup_ui()

     def setup_ui(self):
         layout = QtWidgets.QFormLayout()
         layout.setContentsMargins(0, 0, 0, 0)
         layout.setLabelAlignment(QtCore.Qt.AlignRight)

         for field in ['ΔX', 'ΔY', 'SQUAL', 'LOD']:
             label = QtWidgets.QLabel('-')
             layout.addRow(field + ':', label)
             self.labels.append(label)

         label = QtWidgets.QLabel('Mouse')
         label.setAlignment(QtCore.Qt.AlignHCenter)
         main_layout = QtWidgets.QVBoxLayout(self)
         main_layout.addWidget(label)
         main_layout.addLayout(layout)

     def configure_input_format(self, input_handle):
         self.input_handle = input_handle

     def set_mouse_state(self, mouse_data):
         if mouse_data:
             if self.input_handle == 0x000A:
                 position_x = struct.unpack('<H', mouse_data[0:2])[0]
                 position_y = struct.unpack('<H', mouse_data[2:4])[0]
                 squal = struct.unpack('<H', mouse_data[4:6])[0]
                 lod = struct.unpack('<H', mouse_data[6:8])[0]
                 self.labels[0].setText('0x{:04X}'.format(position_x))
                 self.labels[1].setText('0x{:04X}'.format(position_y))
                 self.labels[2].setText('0x{:04X}'.format(squal))
                 self.labels[3].setText('0x{:04X}'.format(lod))
             else:
                 delta_x = struct.unpack('<h', mouse_data[0:2])[0]
                 delta_y = struct.unpack('<h', mouse_data[2:4])[0]
                 lod = struct.unpack('<B', mouse_data[4:5])[0]
                 self.labels[0].setText('0x{:04X}'.format(delta_x))
                 self.labels[1].setText('0x{:04X}'.format(delta_y))
                 self.labels[2].setText('')
                 self.labels[3].setText('0x{:02X}'.format(lod))


class MotionPlotWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Timer for motion plot updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_motion_plot)

        self.setup_ui()
        self.configure_motion_plot(0)

    def setup_ui(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.plot_widget.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.plot_widget.setMaximumHeight(250)
        self.plot_widget.setYRange(-32768, 32768)
        self.plot_widget.setBackground('w')
        plot_item = self.plot_widget.getPlotItem()
        plot_item.getAxis('left').setPen(pg.mkPen(color='k'))
        plot_item.getAxis('bottom').setPen(pg.mkPen(color='k'))
        plot_item.getAxis('left').setTextPen('k')
        plot_item.getAxis('bottom').setTextPen('k')
        plot_item.showGrid(x=True, y=True, alpha=0.3)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

        # Overlay frame for greyed out effect
        self.overlay = QtWidgets.QFrame(self.plot_widget)
        self.overlay.setStyleSheet("background-color: rgba(230, 230, 230, 150);")
        self.overlay.hide()
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.plot_widget.installEventFilter(self)

    def configure_motion_plot(self, format):
        # Motion data buffer
        self.buffer_length = 500 #200
        self.buffer_width = 14 if format == 0 else 40
        self.counter = 0
        self.xdata = np.arange(self.buffer_length)
        self.motion_buffer = np.zeros((self.buffer_length, self.buffer_width), dtype=np.uint8)

        self.motion_dtype = np.dtype('<i2')
        # self.motion_dtype = np.dtype([
        #     ('temperature', '<i2'),
        #     ('accel_x', '<i2'),
        #     ('accel_y', '<i2'),
        #     ('accel_z', '<i2'),
        #     ('gyro_x', '<i2'),
        #     ('gyro_y', '<i2'),
        #     ('gyro_z', '<i2'),
        # ])

        self.plot_widget.clear()
        colours = rcParams['axes.prop_cycle'].by_key()['color']
        motion_view = self.motion_buffer.view(self.motion_dtype)

        self.plot_widget.addLegend(labelTextSize='6pt')

        self.curves = []
        # for i in range(motion_view.shape[1]):
        for i in range(3):
            pen = pg.mkPen(color=colours[i%len(colours)], width=1)
            curve = self.plot_widget.plot(self.xdata, motion_view[:, i], pen=pen, name='p{:d}'.format(i))
            self.curves.append(curve)

    def start_motion_timer(self):
        self.timer.start(20)

    def stop_motion_timer(self):
        if self.timer.isActive():
            self.timer.stop()

    def update_motion_plot(self):
        motion_view = self.motion_buffer.view(self.motion_dtype)
        for i, curve in enumerate(self.curves):
            # curve.setData(self.xdata, motion_view[:, i])
            curve.setData(self.xdata, motion_view[:, i+1 ])

    def set_motion_data(self, motion):
        self.motion_buffer[self.counter, :] = motion
        self.counter = (self.counter + 1) % self.buffer_length

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.plot_widget.rect())

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.overlay.setVisible(not enabled)

    def setDisabled(self, disabled):
        super().setDisabled(disabled)
        self.overlay.setVisible(disabled)

    def eventFilter(self, source, event):
        if source == self.plot_widget and event.type() == QtCore.QEvent.Resize:
            self.overlay.setGeometry(self.plot_widget.rect())
        return super().eventFilter(source, event)


class PlayerLedWidget(QtWidgets.QWidget):
    stateChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setToolTip('Player LEDs')

        self.setStyleSheet("""
            QCheckBox::indicator {
                width: 6px;
                height: 6px;
                border: 1px solid #444;
                background-color: #111;
            }
            QCheckBox::indicator:checked {
                background-color: #8CFB05;
                border: 1px solid #0a0;
                box-shadow: 0 0 5px #0f0;
            }
        """)

        self.checkboxes = []

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        for i in range(4):
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(lambda: self.stateChanged.emit(self.get_state()))
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

    def set_state(self, state):
        for i in range(len(self.checkboxes)):
            self.checkboxes[i].setChecked((state >> i) & 1)

        self.stateChanged.emit(state & 0xf)

    def get_state(self):
        state = 0
        for i in range(len(self.checkboxes)):
            state |= self.checkboxes[i].isChecked() << i

        return state


class BatteryWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.input_handle = None

        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.voltage_label = QtWidgets.QLabel('- V')
        self.voltage_label.setToolTip('Battery Voltage')

        self.current_label = QtWidgets.QLabel('- mA')
        self.current_label.setToolTip('Battery Current')

        self.status_label = QtWidgets.QLabel('-')
        self.status_label.setToolTip('Charge Status')

        layout.addWidget(self.voltage_label)
        layout.addWidget(self.current_label)
        layout.addWidget(self.status_label)

    def configure_input_format(self, input_handle):
        self.input_handle = input_handle

    def update_state(self, report):
        if self.input_handle == 0x000A:
            voltage = struct.unpack('<H', report[0x1f:0x21])[0]
            current = struct.unpack('<H', report[0x22:0x24])[0]
            charge_status = struct.unpack('<B', report[0x21:0x22])[0]
            self.voltage_label.setText('{:.3f} V'.format(voltage / 1000))
            if current > 0:
                self.current_label.setText('{:.02f} mA'.format(current / 100))
            else:
                self.current_label.setText('--.-- mA')
            self.status_label.setText('0x{:02X}'.format(charge_status))
        else:
            self.voltage_label.setText('')
            self.current_label.setText('')
            self.status_label.setText('')


class InputWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QLabel{font-size:9px;}")

        self.input_format = 0
        self.device_type = 0

        self.primary_stick_calibration = None
        self.secondary_stick_calibration = None
        self.motion_calibration = None

        self.setup_ui()

    def setup_ui(self):
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(10)

        # Editor to display incoming hid data
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setFont(font)
        self.text_edit.setMaximumHeight(100)
        self.text_edit.setReadOnly(True)

        # Create button grid widget
        self.button_grid_widget = ButtonGridWidget()

        # Create primary stick widget
        self.primary_stick_widget = StickWidget()
        primary_stick_label = QtWidgets.QLabel('Primary Stick')
        primary_stick_label.setAlignment(QtCore.Qt.AlignCenter)
        primary_stick_layout = QtWidgets.QVBoxLayout()
        primary_stick_layout.setContentsMargins(0, 0, 0, 0)
        primary_stick_layout.addWidget(primary_stick_label)
        primary_stick_layout.addWidget(self.primary_stick_widget)

        # Create secondary stick widget
        self.secondary_stick_widget = StickWidget()
        secondary_stick_label = QtWidgets.QLabel('Secondary Stick')
        secondary_stick_label.setAlignment(QtCore.Qt.AlignCenter)
        secondary_stick_layout = QtWidgets.QVBoxLayout()
        secondary_stick_layout.setContentsMargins(0, 0, 0, 0)
        secondary_stick_layout.addWidget(secondary_stick_label)
        secondary_stick_layout.addWidget(self.secondary_stick_widget)

        sticks_layout = QtWidgets.QHBoxLayout()
        # sticks_layout.setContentsMargins(0, 0, 0, 0)
        sticks_layout.addLayout(primary_stick_layout)
        sticks_layout.addLayout(secondary_stick_layout)

        self.triggers_widget = TriggersWidget()
        self.triggers_widget.setHidden(True)

        self.mouse_widget = MouseWidget()
        self.mouse_widget.setHidden(True)

        # Plot for motion data
        self.motion_plot_widget = MotionPlotWidget()

        self.input_layout = QtWidgets.QHBoxLayout()
        self.input_layout.addWidget(self.button_grid_widget)
        self.input_layout.addLayout(sticks_layout)
        self.input_layout.addWidget(self.triggers_widget)
        self.input_layout.addWidget(self.mouse_widget)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(self.input_layout)
        main_layout.addWidget(self.motion_plot_widget)

    def configure_input_format(self, input_handle, device_type):
        self.device_type = device_type

        if input_handle == 0x000A:
            self.input_format = 0
        else:
            if device_type == 0x2066:
                self.input_format = 1
            elif device_type == 0x2067:
                self.input_format = 2
            else:
                self.input_format = 3

        # Swap in new button grid widget
        button_grid_widget = ButtonGridWidget(self.input_format)
        self.input_layout.replaceWidget(self.button_grid_widget, button_grid_widget)
        old_widget = self.button_grid_widget
        self.button_grid_widget = button_grid_widget
        old_widget.deleteLater()

        # Reconfigure motion widget
        self.motion_plot_widget.configure_motion_plot(self.input_format)

        self.mouse_widget.configure_input_format(input_handle)

        # Hide unused widgets
        if device_type in [0x2066, 0x2067]:
            self.primary_stick_widget.setHidden(False)
            self.secondary_stick_widget.setHidden(True)
            self.triggers_widget.setHidden(True)
            self.mouse_widget.setHidden(False)
        else:
            self.primary_stick_widget.setHidden(False)
            self.secondary_stick_widget.setHidden(False)
            self.mouse_widget.setHidden(True)
            self.triggers_widget.setHidden(device_type != 0x2073)

    def set_primary_stick_calibration(self, calibration):
        self.primary_stick_widget.set_calibration(calibration)

    def set_secondary_stick_calibration(self, calibration):
        self.secondary_stick_widget.set_calibration(calibration)

    def set_gc_trigger_calibration(self, calibration):
        self.triggers_widget.set_calibration(calibration)

    def start_motion_timer(self):
        self.motion_plot_widget.start_motion_timer()

    def stop_motion_timer(self):
        self.motion_plot_widget.stop_motion_timer()

    def update_state(self, report):
        self.text_edit.setPlainText(hexdump(report))

        # Extract raw values from report
        if self.input_format == 0:
            buttons = report[0x4:0x8]
            stick1 = report[0xA:0xD]
            stick2 = report[0xD:0x10]
            motion = report[0x2E:0x3C]
            mouse = report[0x10:0x18]
            triggers = report[0x3C:0x3E]
        elif self.input_format == 3:
            buttons = report[0x2:0x5]
            stick1 = report[0x5:0x8]
            stick2 = report[0x8:0xB]
            motion = report[0xF:0x37]
            mouse = None
            triggers = report[0xC:0xE]
        else:
            buttons = report[0x2:0x4]
            stick1 = report[0x5:0x8]
            stick2 = None
            motion = report[0x10:0x38]
            mouse = report[0x9:0xE]
            triggers = None

        # Update buttons
        self.button_grid_widget.set_button_state(buttons)

        # Update sticks
        if self.input_format == 0 and self.device_type == 0x2066:
            x2, y2 = unpack_12bit_triplet(stick2)
            self.primary_stick_widget.set_position(x2, y2)
        else:
            x1, y1 = unpack_12bit_triplet(stick1)
            self.primary_stick_widget.set_position(x1, y1)
            if self.input_format not in [1, 2]:
                x2, y2 = unpack_12bit_triplet(stick2)
                self.secondary_stick_widget.set_position(x2, y2)

        # Update analog triggers
        self.triggers_widget.set_trigger_state(triggers)

        # Update mouse data
        self.mouse_widget.set_mouse_state(mouse)

        # Update motion
        self.motion_plot_widget.set_motion_data(motion)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.button_grid_widget.setEnabled(enabled)
        self.motion_plot_widget.setEnabled(enabled)

    def setDisabled(self, disabled):
        super().setDisabled(disabled)
        self.button_grid_widget.setDisabled(disabled)
        self.motion_plot_widget.setDisabled(disabled)


class ReportRateWidget(QtWidgets.QWidget):
    BUFFER_SIZE = 200

    def __init__(self):
        super().__init__()
        self.setToolTip('Report Rate')

        self.counter = 0
        self.timestamp_buffer = np.zeros(ReportRateWidget.BUFFER_SIZE)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel('- Hz')
        layout.addWidget(self.label)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_report_rate)
        self.timer.start(1000)

    def add_timestamp(self):
        self.timestamp_buffer[self.counter] = time.time()
        self.counter = (self.counter + 1) % ReportRateWidget.BUFFER_SIZE

    def update_report_rate(self):
        dt = np.median(np.diff(self.timestamp_buffer))
        if dt > 0:
            freq = 1.0 / dt
            if freq > 1.0:
                self.label.setText('{:.03f} Hz'.format(freq))


class ColourGrid(QtWidgets.QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)

        self.colors = [QtGui.QColor(int.from_bytes(c, byteorder="big")) for c in colors]

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width() // 2
        h = self.height() // 2

        positions = [
            QtCore.QRect(0, 0, w, h),  # Top-left
            QtCore.QRect(w, 0, w, h),  # Top-right
            QtCore.QRect(0, h, w, h),  # Bottom-left
            QtCore.QRect(w, h, w, h)   # Bottom-right
        ]

        # Draw each square
        for rect, color in zip(positions, self.colors):
            painter.fillRect(rect, color)
            painter.drawRect(rect)  # Draw border


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Switch 2 BLE Input Viewer')

        self.input_handle = INPUT_HANDLES[0] - 1

        self.command_handle = COMMAND_HANDLES[0] - 1
        self.command_response_handle = COMMAND_RESPONSE_HANDLES[0] - 1
        self.command_buffer = bytearray(0x60)
        self.command_event = asyncio.Event()

        self.vibration_handle = 0x0012 -1
        self.vibration_counter = 0

        self.current_flags = 0x00

        self.device_info = {}

        self.client = None

        self.setup_ui()

        self.loop = asyncio.get_event_loop()
        self.start()

    def setup_ui(self):
        # Configuration
        input_handle_combo = QtWidgets.QComboBox()
        input_handle_combo.addItems(['0x{:04X}'.format(h) for h in INPUT_HANDLES])
        input_handle_combo.currentIndexChanged.connect(self.on_input_handle_combo_change)

        command_handle_combo = QtWidgets.QComboBox()
        command_handle_combo.addItems(['0x{:04X}'.format(h) for h in COMMAND_HANDLES])
        command_handle_combo.currentIndexChanged.connect(self.on_command_handle_combo_change)

        command_response_handle_combo = QtWidgets.QComboBox()
        command_response_handle_combo.addItems(['0x{:04X}'.format(h) for h in COMMAND_RESPONSE_HANDLES])
        command_response_handle_combo.currentIndexChanged.connect(self.on_command_response_handle_combo_change)

        handle_groupbox = QtWidgets.QGroupBox('GATT Attribute Handles')
        handle_groupbox_layout = QtWidgets.QFormLayout(handle_groupbox)
        handle_groupbox_layout.setSpacing(5)
        handle_groupbox_layout.addRow('Input Notification:', input_handle_combo)
        handle_groupbox_layout.addRow('Command:', command_handle_combo)
        handle_groupbox_layout.addRow('Command Response Notification:', command_response_handle_combo)

        self.feature_flags_widget = FeatureFlagWidget()
        self.feature_flags_widget.set_state(DEFAULT_FEATURE_FLAGS)
        feature_groupbox = QtWidgets.QGroupBox('Feature Flags')
        feature_groupbox_layout = QtWidgets.QVBoxLayout(feature_groupbox)
        feature_groupbox_layout.addWidget(self.feature_flags_widget)

        config_groupbox = QtWidgets.QGroupBox('Configuration')
        config_groupbox_layout = QtWidgets.QHBoxLayout(config_groupbox)
        config_groupbox_layout.addWidget(handle_groupbox)
        config_groupbox_layout.addWidget(feature_groupbox)

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(10)

        # Top menu
        menu_bar = self.menuBar()

        self.file_menu = menu_bar.addMenu('File')
        self.tools_menu = menu_bar.addMenu('Tools')

        exit_action = QtWidgets.QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        info_action = QtWidgets.QAction('Controller Info...', self)
        info_action.triggered.connect(self.display_controller_info)
        self.tools_menu.addAction(info_action)

        pair_action = QtWidgets.QAction('Pair Controller...', self)
        pair_action.triggered.connect(self.pair_device)
        pair_action.setDisabled(True)
        self.tools_menu.addAction(pair_action)

        dump_action = QtWidgets.QAction('Dump Memory...', self)
        dump_action.triggered.connect(self.dump_memory)
        self.tools_menu.addAction(dump_action)

        save_action = QtWidgets.QAction('Save Motion Buffer...', self)
        save_action.triggered.connect(self.save_motion_buffer)
        self.tools_menu.addAction(save_action)

        vibration_action = QtWidgets.QAction('Test Vibratrion...', self)
        vibration_action.triggered.connect(self.test_vibration)
        self.tools_menu.addAction(vibration_action)

        # self.tools_menu.setDisabled(True)

        # Editor to display commands and responses
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setFont(font)
        self.text_edit.setReadOnly(True)

        # Line edit for entering hex commands
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText('Enter command...')
        hex_regex = QtCore.QRegExp("[0-9A-Fa-f ]*")
        validator = QtGui.QRegExpValidator(hex_regex)
        self.line_edit.setValidator(validator)
        self.line_edit.returnPressed.connect(self.on_command_button_click)

        # Button to send hex commands
        self.command_button = QtWidgets.QPushButton('Send Command')
        self.command_button.clicked.connect(self.on_command_button_click)

        # Add line edit and button to their own layout
        command_layout = QtWidgets.QHBoxLayout()
        command_layout.addWidget(self.line_edit)
        command_layout.addWidget(self.command_button)

        # Groupbox for command widgets
        self.command_groupbox = QtWidgets.QGroupBox('Commands')
        command_groupbox_layout = QtWidgets.QVBoxLayout()
        command_groupbox_layout.addWidget(self.text_edit)
        command_groupbox_layout.addLayout(command_layout)
        self.command_groupbox.setLayout(command_groupbox_layout)

        self.input_widget = InputWidget()

        self.input_groupbox = QtWidgets.QGroupBox('Inputs')
        input_groupbox_layout = QtWidgets.QVBoxLayout()
        input_groupbox_layout.setContentsMargins(0, 0, 0, 0)
        input_groupbox_layout.addWidget(self.input_widget)
        self.input_groupbox.setLayout(input_groupbox_layout)

        # Create a central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        # Add grouped widgets to the main layout
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.addWidget(config_groupbox)
        main_layout.addWidget(self.command_groupbox)
        main_layout.addWidget(self.input_groupbox)

        # Set groups initially disabled
        self.command_groupbox.setEnabled(False)
        self.input_widget.setEnabled(False)

        # Add battery level indicator to status bar
        self.battery_widget = BatteryWidget()
        self.battery_widget.setHidden(True)
        self.statusBar().addPermanentWidget(self.battery_widget)

        # Add report rate indicator to status bar
        self.report_rate_widget = ReportRateWidget()
        self.report_rate_widget.setHidden(True)
        self.statusBar().addPermanentWidget(self.report_rate_widget)

        # Add player LED widget to status bar
        self.player_led_widget = PlayerLedWidget()
        self.player_led_widget.setHidden(True)
        self.statusBar().addPermanentWidget(self.player_led_widget)

    def closeEvent(self, event):
        if self.client and self.client.is_connected:
            self.client.disconnect()
            self.input_widget.stop_motion_timer()

        event.accept()

    def display_controller_info(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle("Controller Information")

        device_groupbox = QtWidgets.QGroupBox("Device")
        device_layout = QtWidgets.QFormLayout(device_groupbox)
        device_layout.addRow('Name:', QtWidgets.QLabel(self.device_info['remote_name'].decode()))
        device_layout.addRow('Hardware ID:', QtWidgets.QLabel('{:04X}:{:04X}'.format(self.device_info['vendor_id'], self.device_info['product_id'])))
        device_layout.addRow('Address:', QtWidgets.QLabel(self.device_info['remote_address']))
        device_layout.addRow('Serial:', QtWidgets.QLabel(self.device_info['serial'].decode()))
        device_layout.addRow('Firmware:', QtWidgets.QLabel(self.device_info['firmware_version']))
        device_layout.addRow('Colours:', ColourGrid(self.device_info['colours']))

        pairing_groupbox = QtWidgets.QGroupBox("Pairing")
        pairing_layout = QtWidgets.QFormLayout(pairing_groupbox)
        pairing_layout.addRow('Host Address:', QtWidgets.QLabel(':'.join('{:02X}'.format(c) for c in self.device_info['host_address1'])))
        pairing_layout.addRow('LTK:', QtWidgets.QLabel(self.device_info['ltk'].hex()))

        stick_calibration_groupbox = QtWidgets.QGroupBox("Analog Stick")
        stick_calibration_layout = QtWidgets.QHBoxLayout(stick_calibration_groupbox)
        if self.device_info['factory_primary_stick_calibration']:
            primary_stick_calibration_groupbox = QtWidgets.QGroupBox("Primary")
            primary_stick_calibration_layout = QtWidgets.QFormLayout(primary_stick_calibration_groupbox)
            primary_stick_calibration_layout.addRow('X Center:', QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][0], self.device_info['factory_primary_stick_calibration'][0])))
            primary_stick_calibration_layout.addRow('Y Center:', QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][1], self.device_info['factory_primary_stick_calibration'][1])))
            primary_stick_calibration_layout.addRow('X Max:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][0]+self.device_info['factory_primary_stick_calibration'][2], self.device_info['factory_primary_stick_calibration'][2])))
            primary_stick_calibration_layout.addRow('Y Max:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][1]+self.device_info['factory_primary_stick_calibration'][3], self.device_info['factory_primary_stick_calibration'][3])))
            primary_stick_calibration_layout.addRow('X Min:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][0]-self.device_info['factory_primary_stick_calibration'][4], self.device_info['factory_primary_stick_calibration'][4])))
            primary_stick_calibration_layout.addRow('Y Min:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_primary_stick_calibration'][1]-self.device_info['factory_primary_stick_calibration'][5], self.device_info['factory_primary_stick_calibration'][5])))
            stick_calibration_layout.addWidget(primary_stick_calibration_groupbox)

        if self.device_info['factory_secondary_stick_calibration']:
            secondary_stick_calibration_groupbox = QtWidgets.QGroupBox("Secondary")
            secondary_stick_calibration_layout = QtWidgets.QFormLayout(secondary_stick_calibration_groupbox)
            secondary_stick_calibration_layout.addRow('X Center:', QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][0], self.device_info['factory_secondary_stick_calibration'][0])))
            secondary_stick_calibration_layout.addRow('Y Center:', QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][1], self.device_info['factory_secondary_stick_calibration'][1])))
            secondary_stick_calibration_layout.addRow('X Max:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][0]+self.device_info['factory_secondary_stick_calibration'][2], self.device_info['factory_secondary_stick_calibration'][2])))
            secondary_stick_calibration_layout.addRow('Y Max:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][1]+self.device_info['factory_secondary_stick_calibration'][3], self.device_info['factory_secondary_stick_calibration'][3])))
            secondary_stick_calibration_layout.addRow('X Min:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][0]-self.device_info['factory_secondary_stick_calibration'][4], self.device_info['factory_secondary_stick_calibration'][4])))
            secondary_stick_calibration_layout.addRow('Y Min:',    QtWidgets.QLabel('{:d} ({:d})'.format(self.device_info['factory_secondary_stick_calibration'][1]-self.device_info['factory_secondary_stick_calibration'][5], self.device_info['factory_secondary_stick_calibration'][5])))
            stick_calibration_layout.addWidget(secondary_stick_calibration_groupbox)

        motion_calibration_groupbox = QtWidgets.QGroupBox("Motion Controls")
        motion_calibration_layout = QtWidgets.QFormLayout(motion_calibration_groupbox)
        motion_calibration_layout.addRow('Temperature:', QtWidgets.QLabel('{:f}'.format(self.device_info['motion_calibration_temperature'])))
        motion_calibration_layout.addRow('Accelerometer Bias:', QtWidgets.QLabel('{:f}, {:f}, {:f}'.format(*self.device_info['accelerometer_bias'])))
        motion_calibration_layout.addRow('Gyroscope Bias:', QtWidgets.QLabel('{:f}, {:f}, {:f}'.format(*self.device_info['gyro_bias'])))
        motion_calibration_layout.addRow('Magnetometer Bias:', QtWidgets.QLabel('{:f}, {:f}, {:f}'.format(*self.device_info['magnetometer_bias'])))

        factory_calibration_groupbox = QtWidgets.QGroupBox("Factory Calibration")
        factory_calibration_layout = QtWidgets.QVBoxLayout(factory_calibration_groupbox)
        factory_calibration_layout.addWidget(stick_calibration_groupbox)
        factory_calibration_layout.addWidget(motion_calibration_groupbox)

        main_layout = QtWidgets.QVBoxLayout(dialog)
        main_layout.addWidget(device_groupbox)
        main_layout.addWidget(pairing_groupbox)
        main_layout.addWidget(factory_calibration_groupbox)

        dialog.exec_()

    def pair_device(self):
        pass

    @qasync.asyncSlot()
    async def dump_memory(self):
        await self.client.stop_notify(self.input_handle)

        max_read_size = 0x4f
        total_bytes = 0x200000
        buffer = np.zeros(total_bytes, dtype=np.uint8)

        dialog = QtWidgets.QProgressDialog( "Dumping controller memory...", "Cancel", 0, total_bytes, self)
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle("Memory Dump Progress")
        dialog.setMinimumDuration(0)

        num_chunks, remaining = divmod(total_bytes, max_read_size)
        read_address = 0
        for i in range(num_chunks):
            if dialog.wasCanceled():
                await self.client.start_notify(self.input_handle, self.handle_input_report_notification)
                return

            # Read next memory chunk from controller
            data = await self.read_spi_memory(read_address, max_read_size)

            # Add data to buffer
            buffer[read_address:read_address+max_read_size] = data

            read_address += max_read_size

            dialog.setValue(read_address)

        # Read remaining bytes
        data = await self.read_spi_memory(read_address, remaining)

        # Add data to buffer
        buffer[read_address:read_address+remaining] = data

        dialog.setValue(total_bytes)

        with open('controller_memory.bin', 'wb') as f:
            f.write(buffer)

        QtWidgets.QMessageBox.information(self, "Done", "Memory dump completed successfully.")

        await self.client.start_notify(self.input_handle, self.handle_input_report_notification)

    def save_motion_buffer(self):
        # Store a copy of the current buffer
        buffer = self.input_widget.motion_plot_widget.motion_buffer.copy()

        # Default directory and filename
        default_dir = os.path.expanduser("~")  # Home directory
        default_filename = "motion_buffer.pkl"
        default_path = os.path.join(default_dir, default_filename)

        # Open file save dialog
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Save Motion Buffer", default_path, "Pickle Files (*.pkl);;All Files (*)" )
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    pickle.dump(buffer, f)

                QtWidgets.QMessageBox.information(self, "Success", f"Motion buffer saved to:\n{file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Could not save array:\n{e}")

    def test_vibration(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle("Vibration Test")

        notification_groupbox = QtWidgets.QGroupBox("Vibration Notifications")
        layout = QtWidgets.QGridLayout(notification_groupbox)
        layout.setHorizontalSpacing(2)
        layout.setVerticalSpacing(2)
        layout.setSpacing(2)

        for i in range(7):
            row, col = divmod(i, 4)
            button = QtWidgets.QPushButton("Notification #{}".format(i+1))
            button.clicked.connect(lambda checked, x=i+1: self.play_vibration_sample(x))
            layout.addWidget(button, row, col)

        custom_groupbox = QtWidgets.QGroupBox("Custom Vibration")
        layout = QtWidgets.QVBoxLayout(custom_groupbox)
        option_layout = QtWidgets.QHBoxLayout()
        value_layout = QtWidgets.QHBoxLayout()
        left_motor_groupbox = QtWidgets.QGroupBox("Left Motor")
        left_motor_groupbox_layout = QtWidgets.QFormLayout(left_motor_groupbox)
        left_sliders = {}
        for key in ['freq_0', 'amp_0', 'freq_1', 'amp_1']:
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 1023)
            slider.setValue(512)
            slider.setSingleStep(1)
            label = QtWidgets.QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda value, l=label: l.setText(str(value)))

            left_sliders[key] = slider
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(slider)
            row_layout.addWidget(label)
            left_motor_groupbox_layout.addRow(key, row_layout)

        right_motor_groupbox = QtWidgets.QGroupBox("Right Motor")
        right_motor_groupbox_layout = QtWidgets.QFormLayout(right_motor_groupbox)
        right_sliders = {}
        for key in ['freq_0', 'amp_0', 'freq_1', 'amp_1']:
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 1023)
            slider.setValue(512)
            slider.setSingleStep(1)
            label = QtWidgets.QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda value, l=label: l.setText(str(value)))

            right_sliders[key] = slider
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(slider)
            row_layout.addWidget(label)
            right_motor_groupbox_layout.addRow(key, row_layout)

        value_layout.addWidget(left_motor_groupbox)
        value_layout.addWidget(right_motor_groupbox)
        layout.addLayout(option_layout)
        layout.addLayout(value_layout)
        combo = QtWidgets.QComboBox()
        combo.addItems(["Dual Motors", "Left Motor Only", "Right Motor Only"])

        def on_combo_index_change(index):
            if index == 0:
                left_motor_groupbox.setEnabled(True)
                right_motor_groupbox.setEnabled(True)
            elif index == 1:
                left_motor_groupbox.setEnabled(True)
                right_motor_groupbox.setEnabled(False)
            elif index == 2:
                left_motor_groupbox.setEnabled(False)
                right_motor_groupbox.setEnabled(True)

        combo.currentIndexChanged.connect(on_combo_index_change)

        button = QtWidgets.QPushButton("Test Vibration")

        @qasync.asyncSlot(bool)
        async def on_test_vibration_button_clicked(checked):
            combo_index = combo.currentIndex()

            if combo_index != 2:
                left_motor = {}
                for key, slider in left_sliders.items():
                    left_motor[key] = slider.value()
            else:
                left_motor = None

            if combo_index != 1:
                right_motor = {}
                for key, slider in right_sliders.items():
                    right_motor[key] = slider.value()
            else:
                right_motor = None

            await self.send_vibration(left_motor, right_motor)

        button.clicked.connect(on_test_vibration_button_clicked)

        option_layout.addWidget(combo)
        option_layout.addWidget(button)

        main_layout = QtWidgets.QVBoxLayout(dialog)
        main_layout.addWidget(notification_groupbox)
        main_layout.addWidget(custom_groupbox)

        dialog.exec_()

    @qasync.asyncSlot()
    async def start(self):
        try:
            # Search for an advertising device
            device = await self.scan_devices()

            # Connect our discovered device
            self.client = await self.connect_device(device)

            self.device_info['remote_address'] = self.client.address
            self.device_info['remote_name'] = await self.client.read_gatt_char('2a00')

            # Locate the UUID of the attributes we care about
            print('Remote attributes:')
            for serv in self.client.services:
                print(serv.uuid, '0x{:04X}'.format(serv.handle))
                for char in serv.characteristics:
                    print('  ' + char.uuid, '0x{:04X}'.format(char.handle))
                    for desc in char.descriptors:
                        print('    ' + desc.uuid, '0x{:04X}'.format(desc.handle))

            # data = await self.client.read_gatt_char(0x0003- 1)
            # hexdump(data)

            data = bytearray.fromhex('0100')
            await self.client.write_gatt_char(0x0005 - 1, data, True)

            # Activate notifications for hid command replies
            await self.client.start_notify(self.command_response_handle, self.handle_command_reply_notification)

            # data = bytearray.fromhex('0791010100000000')
            # await self.send_command(data)

            # Read device information
            await self.read_spi_memory(0x13000, 0x40)

            # data = bytearray.fromhex('1691010100000000')
            # await self.send_command(data)

            # Play pre-defined connection vibration
            await self.play_vibration_sample(0x03)

            # Set player LEDs
            led_state = DEFAULT_LED_PATTERN
            await self.set_player_leds(led_state)
            self.player_led_widget.set_state(led_state)

            # Configure feature
            self.current_flags = self.feature_flags_widget.get_state()

            # await self.configure_features(current_feature_flags)
            await self.configure_features(0xFF)

            # Read primary stick factory configuration
            await self.read_spi_memory(0x13080, 0x40)

            # Read secondary stick factory configuration
            await self.read_spi_memory(0x130C0, 0x40)

            # Read user calibrations
            await self.read_spi_memory(0x1FC040, 0x40)

            # Read gyro calibration?
            await self.read_spi_memory(0x13040, 0x10)

            # Read accelerometer/magnetometer calibration?
            await self.read_spi_memory(0x13100, 0x18)

            # Read Gamecube specific data
            if self.device_info['product_id'] == 0x2073:
                # Read analog trigger calibration
                await self.read_spi_memory(0x13140, 0x2)
                # Read some other calibration?
                await self.read_spi_memory(0x13160, 0x20)

            # Read pairing data
            await self.read_spi_memory(0x1FA000, 0x40)

            # Enable features
            await self.enable_features(self.current_flags)

            # Get firmware version info
            await self.get_version_info()

            # Write report rate
            data = bytearray.fromhex('8500')
            await self.client.write_gatt_descriptor(self.input_handle+3, data)
            print('writing {} to 0x{:04x}'.format(data.hex(), self.input_handle+3))

            # Set better connection parameters on Windows 11 where the API supports it
            if platform.system() == 'Windows':
                version = platform.version()
                build_number = int(version.split('.')[-1])
                if build_number >= 22000:
                    from bleak.backends.winrt.client import BleakClientWinRT
                    from winrt.windows.devices.bluetooth import BluetoothLEPreferredConnectionParameters
                    backend = self.client._backend
                    if isinstance(backend, BleakClientWinRT):
                        backend._requester.request_preferred_connection_parameters(BluetoothLEPreferredConnectionParameters.throughput_optimized)

            # Activate hid input reports
            await self.client.start_notify(self.input_handle, self.handle_input_report_notification)

            # Start motion plot update timer
            self.input_widget.start_motion_timer()

            # Connect stateChanged signals
            self.feature_flags_widget.stateChanged.connect(lambda state: self.update_feature_flags(state))
            self.player_led_widget.stateChanged.connect(lambda state: self.set_player_leds(state))

            # Loop until we exit
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print('Exiting...')

    async def scan_devices(self):
        self.statusBar().showMessage('Scanning for devices...')

        found = None
        stop_event = asyncio.Event()

        def callback(device, adv_data):
            nonlocal found

            manu_data = adv_data.manufacturer_data.get(0x0553)
            if manu_data:
                vid = struct.unpack('<H', manu_data[3:5])[0]
                pid = struct.unpack('<H', manu_data[5:7])[0]
                adv = manu_data[12] == 0
                if vid == 0x057E and pid in [0x2066, 0x2067, 0x2069, 0x2073] and adv:
                    found = device
                    stop_event.set()
                    self.statusBar().showMessage('Found device {:04X}:{:04X} {}'.format(vid, pid, device.address))

        async with BleakScanner(callback) as scanner:
            await stop_event.wait()

        return found

    async def connect_device(self, device):
        client = BleakClient(device, disconnected_callback=self.handle_disconnect)
        await client.connect()
        self.tools_menu.setEnabled(True)
        self.statusBar().showMessage(f"Connected to {device.address}")
        self.command_groupbox.setEnabled(True)
        self.input_widget.setEnabled(True)
        self.battery_widget.configure_input_format(INPUT_HANDLES[0])
        self.battery_widget.setHidden(False)
        self.report_rate_widget.setHidden(False)
        self.player_led_widget.setHidden(False)
        return client

    def handle_disconnect(self, client):
        self.tools_menu.setDisabled(True)
        self.statusBar().showMessage("Disconnected")
        self.command_groupbox.setEnabled(False)
        self.input_widget.setEnabled(False)
        self.battery_widget.setHidden(True)
        self.report_rate_widget.setHidden(True)
        self.player_led_widget.setHidden(True)
        self.client = None

    async def handle_input_report_notification(self, sender, data):
        # Add timestamp for report rate estimation
        self.report_rate_widget.add_timestamp()

        self.input_widget.update_state(data)
        self.battery_widget.update_state(data)

    async def handle_command_reply_notification(self, sender, data):
        self.text_edit.appendPlainText('[0x{:04x}] <- : {}'.format(sender.handle+1, data.hex()))
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        if self.command_response_handle+1 == 0x001E:
            response = data[14:]
        else:
            response = data

        self.command_buffer[:len(data)] = response
        self.command_event.set()

    async def handle_read_response(self, response):
        read_address = struct.unpack('<I', response[12:16])[0]
        data_len = response[8]
        data = response[16:16+data_len]
        if read_address == 0x13000:
            self.device_info['serial'] = struct.unpack('16s', data[0x2:0x12])[0]
            self.device_info['vendor_id'] = struct.unpack('<H', data[0x12:0x14])[0]
            self.device_info['product_id'] = struct.unpack('<H', data[0x14:0x16])[0]
            self.device_info['colours'] = [data[0x19:0x1C], data[0x1C:0x1F], data[0x1F:0x22], data[0x22:0x25]]

            self.input_widget.configure_input_format(self.input_handle+1, self.device_info['product_id'])

        elif read_address == 0x13080:
            self.device_info['factory_primary_stick_calibration'] = unpack_12bit_sequence(data[0x28:0x31])
            self.input_widget.set_primary_stick_calibration(self.device_info['factory_primary_stick_calibration'])

        elif read_address == 0x130C0:
            self.device_info['factory_secondary_stick_calibration'] = unpack_12bit_sequence(data[0x28:0x31])
            self.input_widget.set_secondary_stick_calibration(self.device_info['factory_secondary_stick_calibration'])

        elif read_address == 0x13040:
            self.device_info['motion_calibration_temperature'] = struct.unpack('f', data[0:4])[0]
            self.device_info['gyro_bias'] = struct.unpack('3f', data[4:16])

        elif read_address == 0x13100:
            self.device_info['magnetometer_bias'] = struct.unpack('3f', data[0:12])
            self.device_info['accelerometer_bias'] = struct.unpack('3f', data[12:24])

        elif read_address == 0x13140:
            self.device_info['gc_analog_trigger_calibration'] = data[0x0:0x2]
            print('gc_analog_trigger_calibration:', self.device_info['gc_analog_trigger_calibration'])
            self.input_widget.set_gc_trigger_calibration(self.device_info['gc_analog_trigger_calibration'])

        elif read_address == 0x1FC040:
            self.device_info['user_primary_stick_calibration'] = unpack_12bit_sequence(data[0x2:0xB]) if data[0x0:0x2] == b'\xa2\xb2' else None
            self.device_info['user_secondary_stick_calibration'] = unpack_12bit_sequence(data[0x22:0x2B]) if data[0x20:0x22] == b'\xa2\xb2' else None

            print('user_primary_stick_calibration:', self.device_info['user_primary_stick_calibration'])
            print('user_secondary_stick_calibration:', self.device_info['user_secondary_stick_calibration'])

            if self.device_info['user_primary_stick_calibration']:
                self.input_widget.set_primary_stick_calibration(self.device_info['user_primary_stick_calibration'])

            if self.device_info['user_secondary_stick_calibration']:
                self.input_widget.set_secondary_stick_calibration(self.device_info['user_secondary_stick_calibration'])

        elif read_address == 0x1FA000:
            self.device_info['host_address1'] = data[0x8:0xE]
            self.device_info['host_address2'] = data[0x30:0x36]
            self.device_info['ltk'] = data[0x1A:0x2A][::-1]

            print('host address #1:', self.device_info['host_address1'].hex())
            print('host address #2:', self.device_info['host_address2'].hex())
            print('LTK:', self.device_info['ltk'].hex())

    @qasync.asyncSlot(int)
    async def update_feature_flags(self, flags):
        disabled = self.current_flags & ~flags
        if disabled:
            await self.disable_features(disabled)

        enabled = ~self.current_flags & flags
        if enabled:
            await self.enable_features(enabled)

        self.current_flags = flags

    @qasync.asyncSlot()
    async def on_command_button_click(self):
        command = bytearray.fromhex(self.line_edit.text().strip())
        await self.send_command(command)

    @qasync.asyncSlot(int)
    async def on_input_handle_combo_change(self, index):
        if self.client:
            await self.client.stop_notify(self.input_handle)

        self.input_handle = INPUT_HANDLES[index] - 1
        self.input_widget.configure_input_format(INPUT_HANDLES[index], self.device_info['product_id'])
        self.battery_widget.configure_input_format(INPUT_HANDLES[index])

        if self.client:
            await self.client.start_notify(self.input_handle, self.handle_input_report_notification)

    @qasync.asyncSlot(int)
    async def on_command_handle_combo_change(self, index):
        self.command_handle = COMMAND_HANDLES[index] - 1

    @qasync.asyncSlot(int)
    async def on_command_response_handle_combo_change(self, index):
        if self.client:
            await self.client.stop_notify(self.command_response_handle)

        self.command_response_handle = COMMAND_RESPONSE_HANDLES[index] - 1

        if self.client:
            await self.client.start_notify(self.command_response_handle, self.handle_command_reply_notification)

    @qasync.asyncSlot(bytearray)
    async def send_command(self, command):
        if self.command_handle+1 == 0x0016:
            #command = b'\x00'*17 + command
            command = b'\x00'*33 + command

        self.text_edit.appendPlainText('[0x{:04x}] -> : {}'.format(self.command_handle+1, command.hex()))
        await self.client.write_gatt_char(self.command_handle, command, response=False)
        await self.command_event.wait()
        response = self.command_buffer.copy()
        self.command_event.clear()
        return response

    @qasync.asyncSlot(dict, dict)
    async def send_vibration(self, left_motor=None, right_motor=None):
        left_vibration_data = bytearray(0x10)
        if left_motor is not None:
            packed = (
                    ((left_motor['amp_1'] & 0x3FF) << 30) |
                    ((left_motor['freq_1'] & 0x3FF) << 20) |
                    ((left_motor['amp_0'] & 0x3FF) << 10) |
                    ((left_motor['freq_0'] & 0x3FF))
            )
            left_vibration_data[0] = (0x05 << 4) | self.vibration_counter
            left_vibration_data[1:6] = packed.to_bytes(5, byteorder='little')

        right_vibration_data = bytearray(0x10)
        if right_motor is not None:
            packed = (
                    ((right_motor['amp_1'] & 0x3FF) << 30) |
                    ((right_motor['freq_1'] & 0x3FF) << 20) |
                    ((right_motor['amp_0'] & 0x3FF) << 10) |
                    ((right_motor['freq_0'] & 0x3FF))
            )
            right_vibration_data[0] = (0x05 << 4) | self.vibration_counter
            right_vibration_data[1:6] = packed.to_bytes(5, byteorder='little')

        vibration_data = bytearray(0x1) + left_vibration_data + right_vibration_data + bytearray(0x9)

        print(hexdump(vibration_data, 16))

        await self.client.write_gatt_char(self.vibration_handle, vibration_data, response=False)

        self.vibration_counter = (self.vibration_counter + 1) & 0xf

    @qasync.asyncSlot(int, int)
    async def read_spi_memory(self, address, size):
        read_command = bytearray( [0x02, 0x91, 0x01, 0x04, 0x00, 0x08, 0x00, 0x00, size, 0x7E, 0x00, 0x00, address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF, (address >> 24) & 0xFF])
        response = await self.send_command(read_command)
        await self.handle_read_response(response)
        return response[0x10:0x10+response[8]]

    # @qasync.asyncSlot(int, int)
    async def write_spi_memory(self, address, data):
        write_command = bytearray( [0x02, 0x91, 0x01, 0x04, 0x00, 0x08+len(data), 0x00, 0x00, len(data), 0x7E, 0x00, 0x00, address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF, (address >> 24) & 0xFF]) + data
        await self.send_command(write_command)

    @qasync.asyncSlot(int)
    async def set_player_leds(self, led_mask):
        led_command = bytearray([0x09, 0x91, 0x01, 0x07, 0x00, 0x08, 0x00, 0x00, led_mask, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.send_command(led_command)

    @qasync.asyncSlot(int)
    async def play_vibration_sample(self, index):
        vibration_command = bytearray([0x0a, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, index, 0x00, 0x00, 0x00])
        await self.send_command(vibration_command)

    @qasync.asyncSlot(int, int)
    async def configure_features(self, flags):
        feature_command = bytearray([0x0c, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, flags, 0x00, 0x00, 0x00])
        await self.send_command(feature_command)

    @qasync.asyncSlot(int, int)
    async def enable_features(self, flags):
        feature_command = bytearray([0x0c, 0x91, 0x01, 0x04, 0x00, 0x04, 0x00, 0x00, flags, 0x00, 0x00, 0x00])
        await self.send_command(feature_command)

    @qasync.asyncSlot(int, int)
    async def disable_features(self, flags):
        feature_command = bytearray([0x0c, 0x91, 0x01, 0x05, 0x00, 0x04, 0x00, 0x00, flags, 0x00, 0x00, 0x00])
        await self.send_command(feature_command)

    async def get_version_info(self):
        cmd = bytearray([0x10, 0x91, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00])
        response = await self.send_command(cmd)
        response_data = response[8:20]

        fw_type_prefixes = ['OJL','OJR', 'OFK', 'LG']
        fw_str = '{}.{:02d}.{:02d}.{:02d}'.format(fw_type_prefixes[response_data[3]], response_data[0], response_data[1], response_data[2])
        if response_data[3] in [1, 2]:
            fw_str += '-{:02d}'.format(response_data[4]+1)
        if int.from_bytes(response_data[8:], byteorder='big') != 0xffffffff:
            fw_str += '-{:02d}.{:02d}.{:02d}'.format(response_data[8], response_data[9], response_data[10])

        self.device_info['firmware_version'] = fw_str


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.setFixedSize(800, 800)
    window.show()

    with loop:
        loop.run_forever()