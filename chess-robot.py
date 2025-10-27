import pygame
import serial
import time
import cv2
import cv2.aruco as aruco
import numpy as np


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

data = np.load("camera_calibration.npz")
mtx = data["cameraMatrix"]
dist = data["distCoeffs"]

# --- ARUCO SETUP ---
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

# Polyglot piece names by index
pieces = [
    "BN", "WN", "BB", "WB", "BQ", "WQ",
    "BK", "WK", "BR", "WR", "BP", "WP"
]
def piece_to_fen(name):
    mapping = {
        "WP": "P", "WN": "N", "WB": "B", "WR": "R", "WQ": "Q", "WK": "K",
        "BP": "p", "BN": "n", "BB": "b", "BR": "r", "BQ": "q", "BK": "k",
    }
    return mapping.get(name, "?")

def board_to_fen(board):
    fen_rows = []
    for row in board:
        fen_row = ""
        empty = 0
        for cell in row:
            if cell == "":
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += cell
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    return "/".join(fen_rows)

def get_square_centers(corners):
    # corners: list of 4 board corners (tl, tr, br, bl)
    tl, tr, br, bl = [np.array(p, dtype=float) for p in corners]
    centers = []
    for i in range(8):
        row = []
        for j in range(8):
            x = (tl[0]*(7-j)/7 + tr[0]*j/7)*(7-i)/7 + (bl[0]*(7-j)/7 + br[0]*j/7)*i/7
            y = (tl[1]*(7-j)/7 + tr[1]*j/7)*(7-i)/7 + (bl[1]*(7-j)/7 + br[1]*j/7)*i/7
            row.append((x, y))
        centers.append(row)
    return centers

board_corners = []

def click_event(event, x, y, flags, param):
    global corners
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(corners) < 4:
            corners.append((x, y))
            print(f"Corner {len(corners)}: {x}, {y}")
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Select Corners", frame)
        if len(corners) == 4:
            print("Corners selected:")
            print(corners)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    temp = frame.copy()
    for i, (x, y) in enumerate(corners):
        cv2.circle(temp, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(temp, str(i+1), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    cv2.imshow("Select Corners", temp)
    cv2.setMouseCallback("Select Corners", click_event)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('r'):   # reset
        corners = []
        print("Corners reset.")
    elif key == ord('q'):  # quit
        break

square_centers = get_square_centers(board_corners)

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
elbow_value = 90

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
        
        ser.write(f"{horizontal_value:.2f},{shoulder_value:.2f},{elbow_value:.2f}\n".encode('utf-8'))

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

        board = [["" for _ in range(8)] for _ in range(8)]

        if ids is not None:
            for corner, marker_id in zip(corners, ids.flatten()):
                pts = corner.reshape((4, 2))
                cx, cy = np.mean(pts, axis=0)

                min_d, pos = 1e9, (0, 0)
                for i in range(8):
                    for j in range(8):
                        d = np.hypot(square_centers[i][j][0] - cx, square_centers[i][j][1] - cy)
                        if d < min_d:
                            min_d = d
                            pos = (i, j)

                for j in range(4):
                    cv2.line(frame, tuple(pts[j].astype(int)), tuple(pts[(j + 1) % 4].astype(int)), (0, 255, 0), 2)

                # Label each tag with its ID or chess piece name
                label = pieces[marker_id] if marker_id < len(pieces) else f"ID {marker_id}"
                fen_piece = piece_to_fen(label)
                board[pos[0]][pos[1]] = fen_piece
                
                cv2.putText(frame, label, tuple(pts[0].astype(int) - [0, 10]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        fen = board_to_fen(board)
        print(f"FEN: {fen}")
        
        undistored = cv2.undistort(frame, mtx, dist, None, mtx)
        cv2.imshow("ArUco Chess Detector", undistored)
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
