import json
import os
import cv2
import numpy as np

INPUT_FILE = "outputs/geometry/connected_walls.json"
OUTPUT_IMAGE = "outputs/geometry/wall_mask.png"

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

# Find image size
min_x = float("inf")
min_y = float("inf")
max_x = float("-inf")
max_y = float("-inf")

for wall in walls:
    sx, sy = wall["start"]
    ex, ey = wall["end"]

    min_x = min(min_x, sx, ex)
    min_y = min(min_y, sy, ey)
    max_x = max(max_x, sx, ex)
    max_y = max(max_y, sy, ey)

padding = 50

width = int(max_x - min_x + 2 * padding)
height = int(max_y - min_y + 2 * padding)

canvas = np.zeros((height, width), dtype=np.uint8)

for wall in walls:

    sx, sy = wall["start"]
    ex, ey = wall["end"]

    sx = int(sx - min_x + padding)
    sy = int(sy - min_y + padding)

    ex = int(ex - min_x + padding)
    ey = int(ey - min_y + padding)

    thickness = max(2, int(wall["thickness"]))

    cv2.line(
        canvas,
        (sx, sy),
        (ex, ey),
        255,
        thickness
    )

os.makedirs("outputs/geometry", exist_ok=True)

cv2.imwrite(OUTPUT_IMAGE, canvas)

print("Wall mask saved ->", OUTPUT_IMAGE)