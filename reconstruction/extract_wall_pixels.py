import cv2
import json
import numpy as np
import os

IMAGE_PATH = "test.png"
BOXES_PATH = "outputs/geometry/walls.json"
OUTPUT = "outputs/reconstruction/wall_pixels.png"

os.makedirs("outputs/reconstruction", exist_ok=True)

img = cv2.imread(IMAGE_PATH)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

mask = np.zeros(gray.shape, dtype=np.uint8)

with open(BOXES_PATH) as f:
    walls = json.load(f)

for wall in walls:

    x1 = int(wall["bbox"]["x1"])
    y1 = int(wall["bbox"]["y1"])
    x2 = int(wall["bbox"]["x2"])
    y2 = int(wall["bbox"]["y2"])

    roi = gray[y1:y2, x1:x2]

    # Extract dark pixels (walls)
    _, binary = cv2.threshold(
        roi,
        180,
        255,
        cv2.THRESH_BINARY_INV
    )

    mask[y1:y2, x1:x2] = cv2.bitwise_or(
        mask[y1:y2, x1:x2],
        binary
    )

cv2.imwrite(OUTPUT, mask)

print("Saved:", OUTPUT)