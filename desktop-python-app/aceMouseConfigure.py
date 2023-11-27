import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
import serial
import serial.tools.list_ports

class SerialApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.initUI()
		self.serial_port = self.find_nrf_serial_port()

	def find_nrf_serial_port(self):
		nrfVID = '239A'
		nrfPIDs = ['8029', '810B', '8051']
		for port in serial.tools.list_ports.comports():
			if port.vid and port.pid:
				vid = format(port.vid, 'x').upper()
				pid = format(port.pid, 'x').upper()
				if vid == nrfVID and pid in nrfPIDs:
					return serial.Serial(port.device, 9600, timeout=1)
		return None

	def initUI(self):
		self.setGeometry(300, 300, 300, 200)
		self.setWindowTitle('Calibration App')

		self.calibrate_button = QPushButton('Calibrate', self)
		self.calibrate_button.move(50, 50)
		self.calibrate_button.clicked.connect(self.start_calibration)

	def start_calibration(self):
		if self.serial_port:
			self.serial_port.write(b'calibrate')
			calibration_data = self.receive_calibration_data()
			if calibration_data:
				self.save_calibration_data(calibration_data)
			else:
				print("nRF52840 device not found.")

	def receive_calibration_data(self):
		raw_data = self.serial_port.read_until(b'\n')  # Read until newline character
		try:
			return json.loads(raw_data.decode('utf-8'))
		except json.JSONDecodeError:
			print("Error decoding calibration data")
			return None

	def find_circuitpython_drive(self):
		base_paths = {
			'Windows': 'C:\\',	# Change as needed
			'Darwin': '/Volumes/',	# macOS
			'Linux': '/mnt/'  # Or '/media/', depending on the distribution
		}
		os_type = platform.system()
		base_path = base_paths.get(os_type, '/mnt/')  # Default to Linux-like path

		for root, dirs, files in os.walk(base_path):
			for name in dirs:
				if 'CIRCUITPY' in name:
					return os.path.join(root, name)
		return None

	def save_calibration_data(self, data):
		circuitpy_drive = self.find_circuitpython_drive()
		if circuitpy_drive:
			calibration_file = os.path.join(circuitpy_drive, 'calibration_data.json')
			with open(calibration_file, 'w') as file:
				json.dump(data, file)
			print("Calibration data saved to CircuitPython drive.")
		else:
			print("CircuitPython drive not found.")

def main():
	app = QApplication(sys.argv)
	ex = SerialApp()
	ex.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
