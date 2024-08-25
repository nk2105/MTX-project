import sys
import os
import configparser
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QSlider
from PyQt6.QtCore import Qt
import subprocess

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Load the configuration file. Raise an error if values are missing."""
        if not os.path.isfile(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        self.config.read(self.config_file)
        
        # Ensure required sections and keys are present
        if 'ExtruderSettings' not in self.config:
            raise KeyError("Missing 'ExtruderSettings' section in configuration file.")
        if 'SpeedPercentage' not in self.config['ExtruderSettings']:
            raise KeyError("Missing 'SpeedPercentage' in 'ExtruderSettings'.")
        if 'InfillLayerHeight' not in self.config['ExtruderSettings']:
            raise KeyError("Missing 'InfillLayerHeight' in 'ExtruderSettings'.")

    def get_speed_percentage(self):
        """Get the speed percentage from the config file."""
        return self.get_config_value('SpeedPercentage')

    def set_speed_percentage(self, value):
        """Set the speed percentage in the config file."""
        self.set_config_value('SpeedPercentage', value)

    def get_infill_layer(self):
        """Get the infill layer height from the config file."""
        return self.get_config_value('InfillLayerHeight')

    def set_infill_layer(self, value):
        """Set the infill layer height in the config file."""
        self.set_config_value('InfillLayerHeight', value)

    def get_config_value(self, key):
        """Retrieve a configuration value, raising an error if missing or invalid."""
        try:
            return int(self.config['ExtruderSettings'][key])
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid or missing value for '{key}' in configuration file.") from e

    def set_config_value(self, key, value):
        """Set a configuration value and save it to the file."""
        if 'ExtruderSettings' not in self.config:
            self.config['ExtruderSettings'] = {}
        self.config['ExtruderSettings'][key] = str(value)
        self.save_config()

    def save_config(self):
        """Save the configuration to the file."""
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

class ExtruderGUI(QWidget):
    def __init__(self):
        super().__init__()
        # Construct the path to the config file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'motoman_hd10_config.cfg')
        self.config_manager = ConfigManager(config_path)
        
        self.selected_file = ""
        self.sliced = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Extruder GUI')
        self.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout(self)

        # Add file selection, model validation, and slicing button
        layout.addWidget(self.createButton("Select file, Validate Model and Slice to G-code", self.validate_and_slice))

        # Add material selection combo box
        layout.addWidget(self.createComboBox("Select Material:", ["Material A", "Material B", "Material C"], self.choose_material))

        # Add origin input fields
        layout.addWidget(self.createLabel("Origin X:"))
        self.origin_x_edit = self.createLineEdit("0")
        layout.addWidget(self.origin_x_edit)
        
        layout.addWidget(self.createLabel("Origin Y:"))
        self.origin_y_edit = self.createLineEdit("0")
        layout.addWidget(self.origin_y_edit)

        # Add speed percentage slider and label
        try:
            initial_speed = self.config_manager.get_speed_percentage()
            self.speed_label = QLabel(f"Speed Percentage: {initial_speed}%")
            layout.addWidget(self.speed_label)
            layout.addWidget(self.createSlider("Speed Percentage:", 0, 100, 10, self.speedChanged, initial_speed))
        except ValueError as e:
            layout.addWidget(QLabel(f"Error loading speed percentage: {str(e)}"))

        # Add layer height slider and label
        try:
            initial_layer = self.config_manager.get_infill_layer()
            self.layer_label = QLabel(f"Layer Height: {initial_layer}mm")
            layout.addWidget(self.layer_label)
            layout.addWidget(self.createSlider("Layer Height:", 0, 100, 2, self.layerChanged, initial_layer))
        except ValueError as e:
            layout.addWidget(QLabel(f"Error loading layer height: {str(e)}"))

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
        return QLabel(text)

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
        # Handle material selection logic here
        pass

    def speedChanged(self, value):
        self.speed_label.setText(f"Speed Percentage: {value}%")
        self.config_manager.set_speed_percentage(value)

    def layerChanged(self, value):
        self.layer_label.setText(f"Layer Height: {value}mm")
        self.config_manager.set_infill_layer(value)

    def validate_and_slice(self):
        selected_file, _ = QFileDialog.getOpenFileName(self, 'Choose File')
        if selected_file:
            try:
                subprocess.run(["mandoline", selected_file], check=True, stderr=subprocess.PIPE)
                self.selected_file = selected_file
                if not self.sliced:
                    self.slice_to_gcode()
                    self.sliced = True
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
