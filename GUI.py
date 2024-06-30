
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QSlider
from PyQt6.QtCore import Qt
import subprocess
import configparser

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        self.config.read(self.config_file)

    def get_speed_percentage(self):
        try:
            return int(self.config['ExtruderSettings']['SpeedPercentage'])
        except (KeyError, ValueError):
            # Handle cases where key is missing or value cannot be converted to int
            # Provide a default value here
            return 50  # Default value, adjust as needed

    def set_speed_percentage(self, value):
        if 'ExtruderSettings' not in self.config:
            self.config['ExtruderSettings'] = {}
        self.config['ExtruderSettings']['SpeedPercentage'] = str(value)
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

class ExtruderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager('motoman_hd10_config.cfg')  # Adjust the filename as necessary
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Extruder GUI')
        self.setGeometry(200, 200, 600, 400)
        self.setupUI()
        self.selected_file = ""
        self.sliced = False

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.createButton("Select file, Validate Model and Slice to G-code", self.validate_and_slice))
        layout.addWidget(self.createComboBox("Select Material:", ["Material A", "Material B", "Material C"], self.choose_material))
        layout.addWidget(self.createLabel("Origin X:"))
        layout.addWidget(self.createLineEdit("0"))
        layout.addWidget(self.createLabel("Origin Y:"))
        layout.addWidget(self.createLineEdit("0"))

        initial_speed = self.config_manager.get_speed_percentage()
        self.speed_label = QLabel(f"Speed Percentage: {initial_speed}%")
        layout.addWidget(self.speed_label)
        layout.addWidget(self.createSlider("Speed Percentage:", 0, 100, 10, self.speedChanged, initial_speed))

    def createButton(self, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        return button

    def createComboBox(self, label, options, callback):
        combo = QComboBox()
        combo.addItems(options)
        combo.currentTextChanged.connect(callback)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(combo)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def createLabel(self, text):
        label = QLabel(text)
        return label

    def createLineEdit(self, text):
        line_edit = QLineEdit()
        line_edit.setText(text)
        return line_edit

    def createSlider(self, label, min_val, max_val, tick_interval, callback, initial_value=0):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setTickInterval(tick_interval)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(slider)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def choose_material(self, material):
        print("Selected material:", material)

    def speedChanged(self, value):
        self.speed_label.setText(f"Speed Percentage: {value}%")
        self.config_manager.set_speed_percentage(value)

    def validate_and_slice(self):
        selected_file, _ = QFileDialog.getOpenFileName(self, 'Choose File')
        if selected_file:
            try:
                subprocess.run(["mandoline", selected_file], check=True, stderr=subprocess.PIPE)
                print("Model validation successful!")
                self.selected_file = selected_file
                if not self.sliced:
                    self.slice_to_gcode()
                    self.sliced = True
                else:
                    print("Model already sliced.")
            except subprocess.CalledProcessError as e:
                print("Error occurred during model validation:", e.stderr.decode())
        else:
            print("No file selected.")

    def slice_to_gcode(self):
        if self.selected_file:
            output_gcode, _ = QFileDialog.getSaveFileName(self, 'Save G-code File', self.selected_file.split('.')[0] + ".gcode", "G-code Files (*.gcode)")
            if output_gcode:
                try:
                    subprocess.run(["mandoline", "-o", output_gcode, self.selected_file], check=True)
                    print("Slice to G-code successful!")
                except subprocess.CalledProcessError as e:
                    print("Error occurred during slicing:", e.stderr.decode())
        else:
            print("No file selected.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ExtruderGUI()
    ex.show()
    sys.exit(app.exec())
