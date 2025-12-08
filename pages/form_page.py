from PyQt6.QtWidgets import (
	QApplication, QWidget, QLabel, QLineEdit, QComboBox, QSpinBox,
	QRadioButton, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QButtonGroup, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal
from config import FORM_OPTIONS_TYPES, DATA_DIRECTORY

######################################################################################
#                                                                                    #
#                                   FORM Page                                        #
#                                                                                    #
######################################################################################

class FormPage(QWidget):
	form_submitted = pyqtSignal()

	def __init__(self, main_window):
		super().__init__()
		self.main_window = main_window
		self.dimensions = main_window.dimensions
		self.dimensions.WINDOW_HEIGHT_PIXELS -= 100
		self.setWindowTitle("Form Page")
		self.setFixedSize(self.dimensions.WINDOW_WIDTH_PIXELS, self.dimensions.WINDOW_HEIGHT_PIXELS)
		# self.setGeometry(0, 0, self.dimensions.WINDOW_WIDTH_PIXELS, self.dimensions.WINDOW_HEIGHT_PIXELS)

		# Create form fields
		self.first_name_label = QLabel("First Name:")
		self.first_name_input = QLineEdit()

		self.last_name_label = QLabel("Last Name:")
		self.last_name_input = QLineEdit()

		self.phone_label = QLabel("Phone Number:")
		self.phone_input = QLineEdit()

		self.age_label = QLabel("Age:")
		self.age_input = QSpinBox()

		self.dominant_hand_label = QLabel("Dominant Hand:")
		self.dominant_hand_left = QRadioButton("Left")
		self.dominant_hand_right = QRadioButton("Right")

		self.vision_label = QLabel("Normal or Corrected Vision (Wearing Glasses):")
		self.vision_normal = QRadioButton("Normal")
		self.vision_corrected = QRadioButton("Corrected")

		self.test_type_label = QLabel("Test Type:")
		self.test_type_combo = QComboBox()
		self.test_type_combo.addItems(FORM_OPTIONS_TYPES) 
  
		self.extra_info_label = QLabel("Additional Information (Optional):")
		self.extra_info_input = QTextEdit()

		# Submit Button
		self.submit_button = QPushButton("Submit")
		self.submit_button.clicked.connect(self.submit_form)

		# Layout
		self.layout = QVBoxLayout()

		self.layout.addWidget(self.first_name_label)
		self.layout.addWidget(self.first_name_input)

		self.layout.addWidget(self.last_name_label)
		self.layout.addWidget(self.last_name_input)

		self.layout.addWidget(self.phone_label)
		self.layout.addWidget(self.phone_input)

		self.layout.addWidget(self.age_label)
		self.layout.addWidget(self.age_input)

		self.layout.addWidget(self.dominant_hand_label)
		dominant_hand_group = QButtonGroup(self)
		dominant_hand_group.addButton(self.dominant_hand_left)
		dominant_hand_group.addButton(self.dominant_hand_right)
		self.layout.addWidget(self.dominant_hand_left)
		self.layout.addWidget(self.dominant_hand_right)

		self.layout.addWidget(self.vision_label)
		vision_group = QButtonGroup(self)
		vision_group.addButton(self.vision_normal)
		vision_group.addButton(self.vision_corrected)
		self.layout.addWidget(self.vision_normal)
		self.layout.addWidget(self.vision_corrected)

		self.layout.addWidget(self.test_type_label)
		self.layout.addWidget(self.test_type_combo)

		self.layout.addWidget(self.extra_info_label)
		self.layout.addWidget(self.extra_info_input)

		# Add spacer to push submit button down
		spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		self.layout.addItem(spacer)

		self.layout.addWidget(self.submit_button)

		self.setLayout(self.layout)

	def submit_form(self):
		# Gather data from the form
		name = self.first_name_input.text()
		last_name = self.last_name_input.text()
		phone_number = self.phone_input.text()
		age = self.age_input.value()
		dominant_hand = "Left" if self.dominant_hand_left.isChecked() else "Right"
		vision = "Normal" if self.vision_normal.isChecked() else "Corrected"
		test_type = self.test_type_combo.currentText()
		additional_info = self.extra_info_input.toPlainText()

		# Ensure the base directory exists
		from config import OUTPUT_DIR
		from pathlib import Path

		base_path = Path(OUTPUT_DIR)
		# Construct the target directory name based on form input
		target_name = f"{name}_{last_name}_{phone_number}"  
		target_dir = base_path / target_name / test_type

		if not target_dir.exists():
			print(f"Base directory '{target_dir}' does not exist. Creating it...")
			target_dir.mkdir(parents=True)

		self.main_window.target_dir = str(target_dir)

		# create base info file
		file_name = 'info.txt'
		file_path = target_dir / file_name

		# Create a list of lines to write to the file
		lines = [
			f"Name: {name}",
			f"Last Name: {last_name}",
			f"Phone Number: {phone_number}",
			f"Age: {age}",
			f"Dominant Hand: {dominant_hand}",
			f"Vision: {vision}",
			f"Test Type: {test_type}",
			f"Additional Info: {additional_info}",
		]

		# Write to the file
		with open(file_path, "w") as file:
			file.write("\n".join(lines))

		# call the function for reading input files and stuff!
		self.main_window.input_dir = f'{DATA_DIRECTORY}/{test_type}'
		self.form_submitted.emit()
