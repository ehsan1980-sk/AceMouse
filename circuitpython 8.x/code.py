import time
import board
import digitalio  # Import missing digitalio module
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from busio import I2C
import json
import storage
import simpleio 
from adafruit_hid.mouse import Mouse

import adafruit_ble
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_ble.services.standard.device_info import DeviceInfoService


#  rounding algorhythm used for mouse movement
#  as used in the HID mouse CircuitPython example
mouse_min = -9
mouse_max = 9
step = (mouse_max - mouse_min) / 20.0

def steps(axis):
    return round((axis - mouse_min) / step)

#  time.monotonic() variable
clock = 0


last_movement_time = time.monotonic()
sleep_threshold = 300  # 5 minutes of inactivity

def enter_sleep_mode():
    print("Entering sleep mode")
    # Implement the sleep functionality
    # For nRF52840, you might use machine.lightsleep()
    machine.lightsleep()
    

def load_calibration_data():
    try:
        with open("/calibration_data.json", "r") as file:
            return json.load(file)
    except (OSError, ValueError):
        # Default calibration data if file not found or invalid
        return {
            "forward": [0.0, 0.0, 0.0],
            "left": [0.0, 0.0, 0.0],
            "right": [0.0, 0.0, 0.0],
            "down": [0.0, 0.0, 0.0]
        }

def save_calibration_data(calibration_data):
    # Mount the filesystem
    storage.remount("/", readonly=False)

    # Save the calibration data to a file
    with open("/calibration_data.json", "w") as file:
        json.dump(calibration_data, file)

    # Remount the filesystem as read-only
    storage.remount("/", readonly=True)

# Turn on IMU and wait 50 ms
imu_pwr = digitalio.DigitalInOut(board.IMU_PWR)
imu_pwr.direction = digitalio.Direction.OUTPUT
imu_pwr.value = True
time.sleep(0.05)

# Set up I2C bus and initialize IMU
i2c_bus = I2C(board.IMU_SCL, board.IMU_SDA)
sensor = LSM6DS3(i2c_bus)

# Assuming a button is connected to pin A1 for entering calibration mode
button = digitalio.DigitalInOut(board.A1)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# Filter and scaling parameters

# Filter Tuning: The alpha value in the complementary filter determines the balance between the accelerometer and gyroscope data. An alpha closer to 1.0 gives more weight to the gyroscope, while a value closer to 0.0 gives more weight to the accelerometer. This value may need tuning based on the responsiveness and stability you desire.

alpha = 0.5  # Filter smoothing factor, adjust as needed
scale_factor = 5  # Scale factor for mouse movement, adjust based on testing

last_x, last_y = 0, 0  # Keep track of the last position


def calibrate_sensor():
    print("Calibration mode. Follow the instructions...")

    # Forward movement
    print("Now move forward")
    time.sleep(2)  # Wait for the user to move
    forward_data = list(sensor.acceleration)
    print("Forward data captured:", forward_data)

    # Left movement
    print("Now move left")
    time.sleep(2)
    left_data = list(sensor.acceleration)
    print("Left data captured:", left_data)

    # Right movement
    print("Now move right")
    time.sleep(2)
    right_data = list(sensor.acceleration)
    print("Right data captured:", right_data)

    # Downward movement
    print("Now move down")
    time.sleep(2)
    down_data = list(sensor.acceleration)
    print("Down data captured:", down_data)

    # Process and store calibration data
    calibration_data = {
        "forward": forward_data,
        "left": left_data,
        "right": right_data,
        "down": down_data
    }

    # Save the data
    save_calibration_data(calibration_data)

    print("Calibration complete.")


def significant_movement_detected(x, y):
    # Define the threshold in terms of the normalized range
    movement_threshold = 2  # Adjust this value based on testing
    normalized_x = steps(x)
    normalized_y = steps(y)
    return abs(normalized_x) > movement_threshold or abs(normalized_y) > movement_threshold

    

#  setup for HID and BLE
hid = HIDService()

device_info = DeviceInfoService(software_revision=adafruit_ble.__version__,
                                manufacturer="Adafruit Industries")
advertisement = ProvideServicesAdvertisement(hid)
advertisement.appearance = 961
scan_response = Advertisement()
scan_response.complete_name = "CircuitPython HID"

ble = adafruit_ble.BLERadio()

if not ble.connected:
    print("advertising")
    ble.start_advertising(advertisement, scan_response)
else:
    print("already connected")
    print(ble.connections)
    
# Load calibration data or use default
calibration_data = load_calibration_data()

# Initialize variables for the complementary filter
filtered_x, filtered_y = 0, 0
last_time = time.monotonic()

#  setup for mouse
mouse = Mouse(hid.devices)

while True:
    if not ble.connected:
        print("Waiting for connection...")
        ble.start_advertising(advertisement)

    while ble.connected:
        # Check button state inside the BLE connected loop
        if not button.value:
            print("Button pressed, starting calibration.")
            calibrate_sensor()
            # After calibration, you might want to reset the last movement time
            last_movement_time = time.monotonic()
            
        # Read acceleration and gyro data
        accel_x, accel_y, accel_z = sensor.acceleration
        gyro_x, gyro_y, gyro_z = sensor.gyro

        # Apply calibration data here (if necessary)

        # Complementary filter
        current_time = time.monotonic()
        dt = current_time - last_time
        last_time = current_time

        # Adjust these factors based on your testing
        filtered_x = alpha * (filtered_x + gyro_x * dt) + (1 - alpha) * accel_x
        filtered_y = alpha * (filtered_y + gyro_y * dt) + (1 - alpha) * accel_y
        rounded_x = steps(filtered_x)
        rounded_y = steps(filtered_y)
        
        # Check for significant movement
        if significant_movement_detected(filtered_x, filtered_y):
            last_movement_time = time.monotonic()

        # Check if the sleep threshold has been exceeded
        if time.monotonic() - last_movement_time > sleep_threshold:
            enter_sleep_mode()
            # Reset the last movement time after waking up
            last_movement_time = time.monotonic()

        # Map and scale the filtered data to mouse movements
        horizontal_mov = simpleio.map_range(steps(filtered_x), 1.0, 20.0, -15.0, 15.0)
        vertical_mov = simpleio.map_range(steps(filtered_y), 20.0, 1.0, -15.0, 15.0)

        # Combine mouse movements into a single call
        mouse.move(x=int(horizontal_mov), y=int(vertical_mov))

        # Debugging prints
        if (clock + 2) < time.monotonic():
            print("Filtered x", steps(filtered_x))
            print("Filtered y", steps(filtered_y))
            clock = time.monotonic()

ble.start_advertising(advertisement)




