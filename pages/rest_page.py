from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QLabel, QWidget


class RestPage(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        
        # Create layout
        layout = QVBoxLayout()

        # Label
        label = QLabel("Rest up")
        label.setStyleSheet("font-size: 24px; font-weight: bold; text-align: center;")
        layout.addWidget(label)

        # Button
        button = QPushButton("Continue")
        button.setStyleSheet("font-size: 18px; padding: 10px;")
        button.clicked.connect(self.main_window.create_manager)
        layout.addWidget(button)

        # Set layout
        self.setLayout(layout)