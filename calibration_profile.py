import cv2
import numpy as np
import glob

# --- Calibration settings ---
CHECKERBOARD = (8, 6)  # inner corners
square_size = 25.0     # mm (matches printed pattern)

# --- Prepare world coordinates for points like (0,0,0), (1,0,0) ...
objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
objp *= square_size

objpoints, imgpoints = [], []
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,1080)

print("📸 Press SPACE to capture, ESC when done.")

while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if found:
        cv2.drawChessboardCorners(frame, CHECKERBOARD, corners, found)
    cv2.imshow("Calibration", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break
    elif key == 32 and found:  # SPACE
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1),
                                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.001))
        imgpoints.append(corners2)
        print(f"✅ Captured image {len(objpoints)}")

cap.release()
cv2.destroyAllWindows()

if len(objpoints) >= 5:
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    np.savez("camera_calibration.npz", cameraMatrix=mtx, distCoeffs=dist)
    print("🎯 Calibration complete. Saved to camera_calibration.npz")
else:
    print("⚠️ Not enough captures. Take at least 5–10 views from different angles.")
