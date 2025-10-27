import pygame
import serial
import time
import cv2
import cv2.aruco as aruco
# --- DOWNLOAD PIP PACKAGES ---
import subprocess
import sys

def install_missing_requirements(requirements_file="requirements.txt"):
    """Check each package in requirements.txt and install if missing."""
    with open(requirements_file, "r") as f:
        packages = [
            line.strip() for line in f 
            if line.strip() and not line.startswith("#")
        ]

    for pkg in packages:
        try:
            __import__(pkg.split("==")[0].split(">=")[0].split("<=")[0])
            print(f"{pkg} already installed.")
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# --- END PIP DOWNLOAD ---

# --- ARUCO SETUP ---
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

# Polyglot piece names by index
pieces = [
    "WP", "WN", "WB", "WR", "WQ", "WK",
    "BP", "BN", "BB", "BR", "BQ", "BK"
]

# --- CAMERA SETUP ---
cap = cv2.VideoCapture(1)
if not cap.isOpened():
    raise RuntimeError("Webcam not detected.")

# --- CONFIG ---
SERIAL_PORT = 'COM5'      # ESP32 port
BAUD_RATE = 115200
MAX_SPEED = 3.0           # degrees per update
DEADZONE = 0.1            # joystick deadzone

horizontal_value = 90
shoulder_value = 90
elbow_value = 0

# --- SETUP SERIAL ---
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

# --- SETUP CONTROLLER ---
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print("Controller connected:", joystick.get_name())

def trigger_value(raw):
    """Map trigger axis from [-1, 1] to [0, 1]"""
    return (raw + 1) / 2

class JoystickInput:
    lt_raw = 0
    rt_raw = 0
    left_y = 0
    right_y = 0

class JoystickController:
    def __init__(self, jsi: JoystickInput):
        self.horServo = jsi.lt_raw - jsi.rt_raw * MAX_SPEED
        self.shoulder = jsi.left_y * MAX_SPEED
        self.elbow = jsi.right_y * MAX_SPEED

    def update(self, jsi: JoystickInput):
        lt = trigger_value(jsi.lt_raw)
        rt = trigger_value(jsi.rt_raw)

        self.horServo = (lt - rt) * MAX_SPEED

        if abs(jsi.left_y) < DEADZONE:
            jsi.left_y = 0
        self.shoulder = jsi.left_y * MAX_SPEED

        if abs(jsi.right_y) < DEADZONE:
            jsi.right_y = 0
        self.elbow = jsi.right_y * MAX_SPEED

    def send(self):
        global horizontal_value
        global shoulder_value
        global elbow_value

        horizontal_value += self.horServo
        shoulder_value += self.shoulder
        elbow_value += self.elbow
        
        ser.write(f"{self.horServo:.2f},{self.shoulder:.2f},{self.elbow:.2f}\n".encode('utf-8'))

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_Y = 1
RIGHT_Y = 3

def get_inputs(joystick):
    jsi = JoystickInput
    jsi.lt_raw = joystick.get_axis(LEFT_TRIGGER)
    jsi.rt_raw = joystick.get_axis(RIGHT_TRIGGER)
    jsi.left_y = joystick.get_axis(LEFT_Y)
    jsi.right_y = joystick.get_axis(RIGHT_Y)

    return jsi

try:
    jsc = JoystickController(get_inputs(joystick))

    print("Press 'q' to quit")

    while True:
        pygame.event.pump()

        jsc.update(get_inputs(joystick))
        jsc.send()

        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)

        if ids is not None:
            for corner, marker_id in zip(corners, ids.flatten()):
                pts = corner.reshape((4, 2))
                for j in range(4):
                    cv2.line(frame, tuple(pts[j].astype(int)), tuple(pts[(j + 1) % 4].astype(int)), (0, 255, 0), 2)

                # Label each tag with its ID or chess piece name
                label = pieces[marker_id] if marker_id < len(pieces) else f"ID {marker_id}"
                cv2.putText(frame, label, tuple(pts[0].astype(int) - [0, 10]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("ArUco Chess Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.02)  # ~50 Hz loop

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    ser.close()
    pygame.quit()
    cap.release()
    cv2.destroyAllWindows()
