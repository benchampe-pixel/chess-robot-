import pygame
import cv2
import time
import numpy as np
import math
import threading

from config import SERIAL_PORT, BAUD_RATE
from chess import board_to_fen, piece_to_fen, pieces
from cam import get_square_centers, click_event, find_and_draw_markers
from joystick import JoystickController, get_inputs
from robot import send_command, close_serial, go_to_point

# ---- IK SIMULATION ----

# arm segment lengths (mm)
L1 = 226.149
L2 = 151.13

# window setup
W, H = 800, 600
scale = 1.0  # mm per pixel
origin = (W // 2, H - 50)  # shoulder base in window

target = [L1 + L2 - 10, 0]  # initial target (x,z)

def draw_arm(img, x, z):
    # inverse kinematics for drawing
    d = math.sqrt(x**2 + z**2)
    d = min(max(d, 1e-6), L1 + L2)

    cos_elbow = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
    cos_elbow = max(-1.0, min(1.0, cos_elbow))
    elbow_angle = (3.14159) - math.acos(cos_elbow)

    cos_shoulder = (d**2 + L1**2 - L2**2) / (2 * d * L1)
    cos_shoulder = max(-1.0, min(1.0, cos_shoulder))
    shoulder_angle = math.atan2(z, x) + math.acos(cos_shoulder)

    # joint positions
    shoulder = origin
    elbow = (
        int(shoulder[0] + L1 * math.cos(shoulder_angle) / scale),
        int(shoulder[1] - L1 * math.sin(shoulder_angle) / scale),
    )
    end = (
        int(elbow[0] + L2 * math.cos(shoulder_angle - elbow_angle) / scale),
        int(elbow[1] - L2 * math.sin(shoulder_angle - elbow_angle) / scale),
    )

    # draw
    cv2.line(img, shoulder, elbow, (255, 255, 255), 3)
    cv2.line(img, elbow, end, (200, 200, 200), 3)
    cv2.circle(img, shoulder, 6, (0, 0, 255), -1)
    cv2.circle(img, elbow, 6, (0, 255, 0), -1)
    cv2.circle(img, end, 6, (255, 0, 0), -1)
    cv2.circle(img, (int(origin[0] + x / scale), int(origin[1] - z / scale)), 4, (0, 255, 255), -1)

def mouse_callback(event, x, y, flags, param):
    global target
    if event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
        # map mouse coords to arm coordinates
        arm_x = (x - origin[0]) * scale
        arm_z = (origin[1] - y) * scale
        target = [arm_x, arm_z]
        # go_to_point(arm_x, 0, arm_z)
        threading.Thread(target=go_to_point, args=(arm_x, 0, arm_z), daemon=True).start()

cv2.namedWindow("Arm Control")
cv2.setMouseCallback("Arm Control", mouse_callback)

while True:
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    draw_arm(frame, *target)
    cv2.putText(frame, f"Target: X={target[0]:.1f}mm Z={target[1]:.1f}mm",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Arm Control", frame)

    time.sleep(0.02)

    if cv2.waitKey(20) & 0xFF == 27:  # ESC to exit
        break
    
cv2.destroyAllWindows()
close_serial()

# ---- END IK SIMULATION ----

# def main():
#     # --- CAMERA CALIBRATION ---
#     try:
#         data = np.load("utils/camera_calibration.npz")
#         mtx = data["cameraMatrix"]
#         dist = data["distCoeffs"]
#     except FileNotFoundError:
#         print("Camera calibration file not found. Please run the calibration script first.")
#         return

#     # --- CAMERA SETUP ---
#     cap = cv2.VideoCapture(1)
#     if not cap.isOpened():
#         raise RuntimeError("Webcam not detected.")

#     # --- BOARD CORNER SELECTION ---
#     # board_corners = []
#     # while True:
#     #     ret, frame = cap.read()
#     #     if not ret:
#     #         break
        
#     #     undistored = cv2.undistort(frame, mtx, dist, None, mtx)

#     #     temp = undistored.copy()
#     #     for i, (x, y) in enumerate(board_corners):
#     #         cv2.circle(temp, (x, y), 5, (0, 0, 255), -1)
#     #         cv2.putText(temp, str(i+1), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

#     #     cv2.imshow("Select Corners", temp)
#     #     cv2.setMouseCallback("Select Corners", lambda event, x, y, flags, param: click_event(event, x, y, flags, param, board_corners, undistored))

#     #     key = cv2.waitKey(1) & 0xFF
#     #     if key == ord('r'):   # reset
#     #         board_corners = []
#     #         print("Corners reset.")
#     #     elif key == ord('q'):  # quit
#     #         break

#     # if len(board_corners) != 4:
#     #     print("Board corner selection was not completed. Exiting.")
#     #     return

#     square_centers = get_square_centers([(289, 96), (834, 104), (825, 640), (263, 609)])

#     cv2.destroyAllWindows()

#     # --- JOYSTICK SETUP ---
#     pygame.init()
#     pygame.joystick.init()
#     try:
#         joystick = pygame.joystick.Joystick(0)
#         joystick.init()
#         print("Controller connected:", joystick.get_name())
#         jsc = JoystickController()
#     except pygame.error:
#         print("Joystick not found.")
#         jsc = None

#     # --- MAIN LOOP ---
#     try:
#         print("Press 'q' to quit")
#         while True:
#             pygame.event.pump()

#             if jsc:
#                 # hor_servo, shoulder, elbow = jsc.update(get_inputs(joystick))
#                 # send_command(hor_servo, shoulder, elbow)
#                 #           x   y    Vert
#                 go_to_point(50, 50, -100)

#             ret, frame = cap.read()
#             if not ret:
#                 break

#             find_and_draw_markers(frame, mtx, dist, square_centers)

#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#             time.sleep(0.02)  # ~50 Hz loop

#     except KeyboardInterrupt:
#         print("\nExiting...")
#     finally:
#         close_serial()
#         pygame.quit()
#         cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()
