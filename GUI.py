import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QSlider
from PyQt6.QtCore import Qt
import subprocess

class ExtruderGUI(QWidget):
    def __init__(self):
        super().__init__()
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
        self.speed_label = QLabel("Speed Percentage: 0%")
        layout.addWidget(self.speed_label)
        layout.addWidget(self.createSlider("Speed Percentage:", 0, 100, 10, self.speedChanged))
        self.temperature_label = QLabel("Temperature: 0°C")
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.createSlider("Temperature (°C):", 0, 300, 50, self.tempChanged))
        self.infill_label = QLabel("Infill: 0mm")
        layout.addWidget(self.infill_label)
        layout.addWidget(self.createSlider("Infill Layer Height (mm):", 10, 50, 1, self.infillChanged))

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

    def createSlider(self, label, min_val, max_val, tick_interval, callback):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setTickInterval(tick_interval)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
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
        print("Speed changed:", value)

    def tempChanged(self, value):
        self.temperature_label.setText(f"Temperature: {value}°C")
        print("Temperature changed:", value)

    def infillChanged(self, value):
        self.infill_label.setText(f"Infill: {value}mm")
        print("Infill changed:", value)

    def validate_and_slice(self):
        # Open a file dialog to let the user choose a file
        selected_file, _ = QFileDialog.getOpenFileName(self, 'Choose File')
        
        # Check if a file was selected
        if selected_file:
            try:
                # Run Mandoline Slicer with the selected file
                # Set check=True to raise an error if Mandoline returns a non-zero exit status
                # Redirect stderr to subprocess.PIPE to capture any error messages
                subprocess.run(["mandoline", selected_file], check=True, stderr=subprocess.PIPE)
                
                # Print a success message if the model validation was successful
                print("Model validation successful!")
                
                # Store the selected file
                self.selected_file = selected_file
                
                # Slice to G-code if not already sliced
                if not self.sliced:
                    self.slice_to_gcode()
                    self.sliced = True
                else:
                    print("Model already sliced.")
                
            except subprocess.CalledProcessError as e:
                # If an error occurs during model validation, print the error message
                print("Error occurred during model validation:", e.stderr.decode())
        else:
            print("No file selected.")

    def slice_to_gcode(self):
        # Check if a file is selected
        if self.selected_file:
            # Prompt the user to choose a location to save the output G-code file
            # Use the selected file's name (without extension) as the default output file name
            output_gcode, _ = QFileDialog.getSaveFileName(self, 'Save G-code File', self.selected_file.split('.')[0] + ".gcode", "G-code Files (*.gcode)")
            
            # Check if a location for saving the output file was selected
            if output_gcode:
                try:
                    # Run Mandoline Slicer to slice the selected STL file into G-code
                    # Specify the output file location using the -o argument
                    subprocess.run(["mandoline", "-o", output_gcode, self.selected_file], check=True)
                    
                    # Print a success message if slicing to G-code was successful
                    print("Slice to G-code successful!")
                except subprocess.CalledProcessError as e:
                    # If an error occurs during slicing, print the error message
                    print("Error occurred during slicing:", e.stderr.decode())
        else:
            print("No file selected.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ExtruderGUI()
    ex.show()
    sys.exit(app.exec())
