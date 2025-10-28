import cv2
import cv2.aruco as aruco
import numpy as np
from chess import pieces, piece_to_fen, board_to_fen

# --- ARUCO SETUP ---
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

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

def click_event(event, x, y, flags, param, board_corners, frame):
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(board_corners) < 4:
            board_corners.append((x, y))
            print(f"Corner {len(board_corners)}: {x}, {y}")
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Select Corners", frame)
        if len(board_corners) == 4:
            print("Corners selected:")
            print(board_corners)

def find_and_draw_markers(frame, mtx, dist, square_centers):
    undistored = cv2.undistort(frame, mtx, dist, None, mtx)
    gray = cv2.cvtColor(undistored, cv2.COLOR_BGR2GRAY)
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

            label = pieces[marker_id] if marker_id < len(pieces) else f"ID {marker_id}"
            fen_piece = piece_to_fen(label)
            board[pos[0]][pos[1]] = fen_piece
            
            cv2.putText(undistored, label, tuple(pts[0].astype(int) - [0, 10]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    fen = board_to_fen(board)
    print(f"FEN: {fen}")
    
    cv2.imshow("ArUco Chess Detector", undistored)