import cv2
import cv2.aruco as aruco
import os

# Use a dictionary large enough for 12 unique markers
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)

# Polyglot piece names by index
pieces = [
    "WP", "WN", "WB", "WR", "WQ", "WK",
    "BP", "BN", "BB", "BR", "BQ", "BK"
]

# Create output directory
os.makedirs("aruco_chess_pieces", exist_ok=True)

# Generate each tag using its Polyglot index as the ID
for idx, name in enumerate(pieces):
    tag_img = aruco.generateImageMarker(aruco_dict, idx, 400)

    border = 80
    tag_with_border = cv2.copyMakeBorder(
        tag_img, border, border, border, border,
        cv2.BORDER_CONSTANT, value=255
    )

    filename = f"aruco_chess_pieces/{idx:02d}_{name}.png"
    cv2.imwrite(filename, tag_with_border)
    
    print(f"Saved {filename}")

print("All ArUco chess piece tags generated successfully.")
