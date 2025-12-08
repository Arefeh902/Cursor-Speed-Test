import time
import threading
import csv
import matplotlib.pyplot as plt
from queue import Queue
from pathlib import Path
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QEvent
from PyQt6.QtGui import QCursor, QPainter, QColor, QPen, QTabletEvent
from PyQt6.QtWidgets import QWidget
from models import Data, TabletData, TabletArea
from config import (
	BACKGROUND_COLOR, SOURCE_CIRCLE_COLOR, DESTINATION_CIRCLE_COLOR, RECT_COLOR,
	SUCCESS_PATH_COLOR, RECT_HIT_PATH_COLOR, START_FREQUENCY, START_DURATION_MS,
	SUCCESS_FREQUENCY, SUCCESS_DURATION_MS, FAILURE_FREQUENCY, FAILURE_DURATION_MS, 
	DELAY_BETWEEN_TESTS, MAX_SPEED_OVERSHOOT_COEFFICIENT, NUM_OF_POINTS_WITH_LESS_THAN_MAX_SPEED,
	PERCENT_OF_POINTS_TO_PROCESS_FOR_OVERSHOOT_AND_UNDERSHOOT
)
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
import sounddevice as sd
import numpy as np
import os
from evdev import InputDevice, ecodes


######################################################################################
#                                                                                    #
#                                Manager Page                                        #
#                                                                                    #
######################################################################################

class PageManager(QObject):
	"""Manages the test progression and navigation between pages."""
	start_test_signal = pyqtSignal(Data)
	finished_signal = pyqtSignal()

	def __init__(self, file_path: str):
		super().__init__()
		self.file_path = file_path
		self.test_number = -1
		self.data_generator = self._data_generator_function()
		self.tablet_x_pixels = 65024
		self.tablet_y_pixels = 40640
		self.tablet_area = TabletArea(self.tablet_x_pixels, self.tablet_y_pixels)
		self.total_time_sec = None	


	def _data_generator_function(self):
		"""Generator function to read test data from a CSV file."""
		with open(self.file_path, 'r') as file:
			csv_reader = csv.reader(file)
			for row in csv_reader:
				# parse the general test params
				if self.test_number == -1:
					self._parse_first_row(row)
					self.test_number += 1
					continue
				self.test_number += 1
				yield self._parse_row(row)


	def _parse_first_row(self, row: list) -> None:
		data = [int(x) for x in row]

		self.total_time_sec = data[0]	
		self.num_of_tests = data[1]

		self.show_line = data[2]
		self.show_speed_ratio = data[3]
		self.show_time = data[4]


	def _parse_row(self, row: list) -> Data:
		"""Parses a row of CSV data into a Data object."""
		data = [float(x) for x in row]
		circle_size = 3
		rectangle_size = 4

		curser_speed_ratio = data[0]
		data_collection_rate = data[1]

		source_circle = tuple(data[2: 2+circle_size])
		dest_circle = tuple(data[2+circle_size:2 + 2 * circle_size])

		index = 2 + 2 * circle_size
		if len(data) >= index:
			num_rectangles = int(data[index])
			rectangles = [
				tuple(data[i:i + rectangle_size])
				for i in range(index + 1, index + 1 + num_rectangles * rectangle_size, rectangle_size)
			]

		return Data(curser_speed_ratio, source_circle, dest_circle, rectangles, rate=data_collection_rate)

	def start_tests(self):
		"""Starts the test sequence."""
		self.all_tests_start_time = time.perf_counter_ns()

		data = next(self.data_generator)
		self.start_test_signal.emit(data)

	def next_test(self):
		try:
			if time.perf_counter_ns() - self.all_tests_start_time > self.total_time_sec * 1e9:
				print("time ended!")
				self.finished_signal.emit()
			
			data = next(self.data_generator)
			self.start_test_signal.emit(data)
		except StopIteration:
			self.finished_signal.emit()



def play_beep(frequency: float, duration: float):
	# Generate a sine wave
	sample_rate = 44100  # Samples per second (standard for audio)
	t = np.linspace(0, duration, int(sample_rate * duration), False)
	audio = np.sin(2 * np.pi * frequency * t)

	# Play the audio
	sd.play(audio, samplerate=sample_rate)
	sd.wait()


class TestPage(QWidget):
	"""Handles a single test, managing input, drawing, and logic."""
	def __init__(self, data: Data, target_dir: str, target_file_prefix: str, manager: PageManager):
		super().__init__()
		self.data = data
		self.state = self.data.state
		self.manager = manager
		self.target_dir = target_dir
		self.target_file_prefix = target_file_prefix
		self.is_running = False

		self.manager.tablet_area.set_area_based_on_speed_ratio(self.data.speed_ratio_x, self.data.speed_ratio_y)

		self.sampling_rate_ms = 1000 / self.data.rate
		self.read_queue = Queue(maxsize=10000)
		self.tablet_data_times = []

		self.start_time = 0
		self.tablet_data = None
		self.pen_up_signal = None
		self.pen_up_time = None
		
		self.tablet_connected = False
		self.path_color = SUCCESS_PATH_COLOR
		self.show_path_flag = True

		self.setFixedSize(self.data.dimensions.WINDOW_WIDTH_PIXELS, self.data.dimensions.WINDOW_HEIGHT_PIXELS)
		self.setWindowTitle("Display")
		
		self.init_ui()
		
		self.reading_thread = threading.Thread(target=self.read_data)
		self.processing_thread = threading.Thread(target=self.process_data)
  
		self.start_beep_thread = threading.Thread(target=play_beep, args=(START_FREQUENCY, START_DURATION_MS))
		self.success_beep_thread = threading.Thread(target=play_beep, args=(SUCCESS_FREQUENCY, SUCCESS_DURATION_MS))
		self.failure_beep_thread = threading.Thread(target=play_beep, args=(FAILURE_FREQUENCY, FAILURE_DURATION_MS))
	
	def init_ui(self):
		layout = QVBoxLayout()
		layout.addStretch()

		# Create a QLabel for the test number at the bottom
		self.test_number_label = QLabel(f"Test Number: {self.manager.test_number}")
		self.test_number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

		# Style the label to make it small and subtle
		self.test_number_label.setStyleSheet("""
			font-size: 20px;
			color: #555555;
			padding: 5px;
		""")

		layout.addWidget(self.test_number_label, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
		self.setLayout(layout)
		
	def tabletEvent(self, event: QTabletEvent):
		"""Handles tablet input events."""
		# threading.Thread(target=self.tablet_, args=(event, time.perf_counter_ns())).start()
		# current_time = time.perf_counter_ns()
		self.tablet_data = [
			event.position().x(),
			event.position().y(),
			event.pressure(),
			event.xTilt(),
			event.yTilt(),
			event.rotation(),
			event.timestamp()
		]
		
		if not self.start_time and event.type() == QEvent.Type.TabletPress and self.data.source_circle.check_hit(event.position().x(), event.position().y()):
			self.tablet_connected = True
			self.start_tracking()

		if event.type() == QEvent.Type.TabletRelease:
			self.pen_up_time = time.perf_counter_ns() - self.start_time
			self.pen_up_signal = True

		
			

	def mousePressEvent(self, event):
		"""Handles mouse press events."""
		if not self.start_time and self.data.source_circle.check_hit(event.position().x(), event.position().y()):
			self.start_tracking()


	def start_tracking(self):
		"""Starts tracking user input."""
		self.start_time = time.perf_counter_ns()
		self.is_running = True

		self.reading_thread.start()
		self.processing_thread.start()
		self.start_beep_thread.start()
		

	def read_data(self):
		"""Reads input data from the mouse or tablet at regular intervals."""
		last_sample_time = self.start_time
		while self.is_running:
			current_time = time.perf_counter_ns()
			if current_time - last_sample_time >= self.sampling_rate_ms * 1e6:
				last_sample_time = current_time
				if self.tablet_connected:
					data = self.tablet_data.copy()
				else:
					pos = self.mapFromGlobal(QCursor.pos())
					data = [pos.x(), pos.y(), None, None, None, None, None]
				elapsed_time = (current_time - self.start_time) / 1e6
				self.read_queue.put((data, elapsed_time))


	def process_data(self):
		"""Processes the sampled input data."""
		while self.is_running:
			if not self.read_queue.empty():
				data, t = self.read_queue.get()
				x, y = data[0], data[1]
				self.data.process_input_data(data, t)

				if self.pen_up_signal and self.pen_up_time <= t * 1e6:
					self.start_stop_thread(t)
					break


	def start_stop_thread(self, t):
		self.is_running = False
		self.stop_thread = threading.Thread(target=self.stop_tracking, args=(t,))
		self.stop_thread.start()
			
	def post_process_data(self):
		# calc max speed
		self.data.max_speed = -1
		points_len = len(self.data.state.points)

		unique_points = [self.data.state.points[0]]
		unique_points_acceleration = [0, 0]
		for i in range(1, points_len):
			if self.data.state.points[i][-2] != self.data.state.points[i-1][-2]:
				unique_points.append(self.data.state.points[i])

		unique_points_len = len(unique_points)
		for i in range(2, unique_points_len):
			p1 = unique_points[i-2]
			p2 = unique_points[i-1]
			p3 = unique_points[i]
			x1, y1, t1 = *p1[:2], p1[-2]
			x2, y2, t2 = *p2[:2], p2[-2]
			x3, y3, t3 = *p3[:2], p3[-2]
			acceleration = self.data.calc_acceleration(x1, y1, t1, x2, y2, t2, x3, y3, t3)
			unique_points_acceleration.append(acceleration)
			if acceleration > self.data.max_acceleration:
				self.data.max_acceleration = acceleration
		
		low_speed_count = 0
		for i in range(int(unique_points_len*PERCENT_OF_POINTS_TO_PROCESS_FOR_OVERSHOOT_AND_UNDERSHOOT), unique_points_len):
			if unique_points_acceleration[i] < self.data.max_acceleration * MAX_SPEED_OVERSHOOT_COEFFICIENT:
				low_speed_count += 1
				if low_speed_count == NUM_OF_POINTS_WITH_LESS_THAN_MAX_SPEED:
					unique_points = unique_points[:i+1]
					unique_points_acceleration = unique_points_acceleration[:i+1]
					self.data.state.unique_points = unique_points
					self.data.state.unique_points_acceleration = unique_points_acceleration
					break
			else:
				low_speed_count = 0


	# TODO
	def stop_tracking(self, t):
		print("Tracking stopped!")
		self.data.state.time = t

		if self.reading_thread.is_alive():
			self.reading_thread.join() 
		if self.processing_thread.is_alive():
			self.processing_thread.join()

		self.post_process_data()
		self.state.success_status = self.determine_status()

		# 0 is rect hit
		# 1 is sucess
		# 2 is overshoot
		# 3 is undershoot
		# make it an enum 
		# TODO
		path_colors = []
		self.path_color = SUCCESS_PATH_COLOR 


		if self.state.success_status == 1:
			self.success_beep_thread.start()
		else:
			self.failure_beep_thread.start()

		self.show_path_flag = True
		self.update()

		QTimer.singleShot(DELAY_BETWEEN_TESTS, self.manager.next_test)
  
		self.save_data()
		self.plot()

	def plot(self):
		# self.plot_with_moving_average(self.data.state.unique_points_acceleration, 5)
		pass

	def plot_with_moving_average(self, data, n):
		"""
		Plot a list of numbers and its moving average over n points.

		Parameters:
			data (list[float]): The data to plot.
			n (int): Number of points for the moving average.
		"""

		# --- compute moving average ---
		if n < 1:
			raise ValueError("n must be >= 1")

		moving_avg = []
		for i in range(len(data)):
			start = max(0, i - n + 1)
			window = data[start : i + 1]
			moving_avg.append(sum(window) / len(window))

		# --- plot ---
		plt.figure(figsize=(10, 4))
		plt.plot(data, label="Data")
		plt.plot(moving_avg, label=f"{n}-point Moving Average")
		plt.legend()
		plt.xlabel("Index")
		plt.ylabel("Value")
		plt.title("Data and Moving Average")
		plt.show()



	# TODO
	def determine_status(self) -> bool:
		"""Determines the success status of the test."""
		dest = self.data.dest_circle
		x, y = self.data.reverse_process_x_and_y_for_record(self.state.points[-1][0], self.state.points[-1][1])

		if x > (dest.x + dest.rx):
			self.data.state.overshoot = 1
			return False
		if x < (dest.x - dest.rx):
			self.data.state.undershoot = 1
			return False

		if not self.data.state.dest_hit:
			return False

		if any(self.data.state.rects_hit):
			return False

		return True


	def generate_header_and_first_row(self):
		"""Generates the header and first row for the CSV file."""
		header = ['x', 'y', 'pressure', 'x_tilt', 'y_tilt', 'rotation', 'tablet_time', 'time', 'success', 'overshoot', 'undershoot']
		header += [f"rect_{i + 1}_hit" for i in range(len(self.data.state.rects_hit))]
		header += [f'distance of last point from center of dest']

		first_row = [
			*self.data.state.points[0], self.data.state.points_speeds[0],
			int(self.data.state.success_status),
			self.data.state.overshoot,
			self.data.state.undershoot,
			*self.data.state.rects_hit,
			self.data.dest_circle.calc_dist_to_center(self.data, self.data.state.points[-1][0], self.data.state.points[-1][1])
		]
		return header, first_row


	def save_data(self):
		print('saving data...')
		"""Saves the test data to a CSV file."""
		output_path = Path(self.target_dir) / f"{self.target_file_prefix}_{self.manager.test_number}.csv"
		with output_path.open(mode="w", newline="") as file:
			writer = csv.writer(file)
			header, first_row = self.generate_header_and_first_row()
			writer.writerow(header)
			writer.writerow(first_row)
			writer.writerows(zip(self.data.state.points[1:], self.data.state.points_speeds[1:]))


	def paintEvent(self, event):
		"""Handles custom painting of the test elements."""
		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor(*BACKGROUND_COLOR))

		# Draw source, destination, and middle circles
		self.data.source_circle.draw(painter)
		self.data.dest_circle.draw(painter)

		# Draw rectangles
		for rect in self.data.rects:
			rect.draw(painter)

		# Draw path if the flag is set
		if self.show_path_flag:
			pen = QPen(QColor(*self.path_color), 2)
			painter.setPen(pen)
			for i in range(len(self.data.state.unique_points) - 1):
				x1, y1 = self.data.state.unique_points[i][:2]
				x1, y1 = self.data.reverse_process_x_and_y_for_record(x1, y1) 
				x2, y2 = self.data.state.unique_points[i+1][:2]
				x2, y2 = self.data.reverse_process_x_and_y_for_record(x2, y2) 
				painter.drawLine(
					int(x1), int(y1),
					int(x2), int(y2)
				)

