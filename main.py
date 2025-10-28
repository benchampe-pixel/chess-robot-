import pygame
import cv2
import time
import numpy as np

from config import SERIAL_PORT, BAUD_RATE
from chess import board_to_fen, piece_to_fen, pieces
from cam import get_square_centers, click_event, find_and_draw_markers
from joystick import JoystickController, get_inputs
from robot import send_command, close_serial

def main():
    # --- CAMERA CALIBRATION ---
    try:
        data = np.load("utils/camera_calibration.npz")
        mtx = data["cameraMatrix"]
        dist = data["distCoeffs"]
    except FileNotFoundError:
        print("Camera calibration file not found. Please run the calibration script first.")
        return

    # --- CAMERA SETUP ---
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise RuntimeError("Webcam not detected.")

    # --- BOARD CORNER SELECTION ---
    board_corners = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        undistored = cv2.undistort(frame, mtx, dist, None, mtx)

        temp = undistored.copy()
        for i, (x, y) in enumerate(board_corners):
            cv2.circle(temp, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(temp, str(i+1), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        cv2.imshow("Select Corners", temp)
        cv2.setMouseCallback("Select Corners", lambda event, x, y, flags, param: click_event(event, x, y, flags, param, board_corners, undistored))

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):   # reset
            board_corners = []
            print("Corners reset.")
        elif key == ord('q'):  # quit
            break

    if len(board_corners) != 4:
        print("Board corner selection was not completed. Exiting.")
        return

    square_centers = get_square_centers(board_corners)

    # --- JOYSTICK SETUP ---
    pygame.init()
    pygame.joystick.init()
    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print("Controller connected:", joystick.get_name())
        jsc = JoystickController()
    except pygame.error:
        print("Joystick not found.")
        jsc = None

    # --- MAIN LOOP ---
    try:
        print("Press 'q' to quit")
        while True:
            pygame.event.pump()

            if jsc:
                hor_servo, shoulder, elbow = jsc.update(get_inputs(joystick))
                send_command(hor_servo, shoulder, elbow)

            ret, frame = cap.read()
            if not ret:
                break

            find_and_draw_markers(frame, mtx, dist, square_centers)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.02)  # ~50 Hz loop

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        close_serial()
        pygame.quit()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
