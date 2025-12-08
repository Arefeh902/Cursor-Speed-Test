import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from models import Data, ScreenDimensions
from config import INPUT_FILE_PATH
from pages.form_page import FormPage
from pages.test_page import TestPage, PageManager
from pages.rest_page import RestPage
from pathlib import Path
import os

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		# Initialize screen dimensions
		self.dimensions = ScreenDimensions(QApplication.instance())
		self.setWindowTitle("Main Window")
		self.setGeometry(0, 0, self.dimensions.WINDOW_WIDTH_PIXELS, self.dimensions.WINDOW_HEIGHT_PIXELS)

		self.input_dir: str | None = None
		self.target_dir: str | None = None

		self.folders: list | None = None
		self.folder_index: int = 0

		# self.folders = [os.path.join(self.input_dir, folder) for folder in os.listdir(self.input_dir) if os.path.isdir(os.path.join(self.input_dir, folder))]
		# self.folders = sorted(self.folders, key=lambda x: int(os.path.basename(x)))
		# print(self.folders)

		# Display the initial FormPage
		self.show_form_page()
		self.form_page.form_submitted.connect(self.create_manager)
	
	def create_manager(self):
		input_file = 'input.csv'

		# create_input_file_from_excel(self.folders[self.folder_index], input_file)
		# self.folder_index += 1

		self.manager = PageManager(input_file)
		self.manager.start_test_signal.connect(self.show_test_page)
		self.manager.finished_signal.connect(self.on_tests_complete)
		self.manager.start_tests()
		
	def show_form_page(self) -> None:
		"""Display the form page."""
		self.form_page = FormPage(self)
		self.set_central_widget(self.form_page)

	def show_rest_page(self) -> None:
		"""Display the form page."""
		self.rest_page = RestPage(self)
		self.set_central_widget(self.rest_page)

	def show_test_page(self, data: Data) -> None:
		"""Display the test page with the given data."""
		test_page = TestPage(data, self.target_dir, "", self.manager)
		self.set_central_widget(test_page)

	def on_tests_complete(self) -> None:
		"""Handle actions when all tests are completed."""
		print("Test Completed!")	
		self.close()

	def set_central_widget(self, widget: QWidget) -> None:
		"""Safely replace the central widget."""
		if (current_widget := self.centralWidget()) is not None:
			current_widget.deleteLater()  # Clean up the old widget
		self.setCentralWidget(widget)


def main() -> None:
	"""Main entry point of the application."""
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
