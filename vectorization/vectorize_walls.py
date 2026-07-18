import cv2
import numpy as np
import json
import os


INPUT = "outputs/reconstruction/wall_pixels.png"
OUTPUT = "outputs/geometry/wall_vectors.json"


os.makedirs("outputs/geometry", exist_ok=True)


# Load image
img = cv2.imread(INPUT, cv2.IMREAD_GRAYSCALE)


# Clean noise
kernel = np.ones((3,3), np.uint8)

clean = cv2.morphologyEx(
    img,
    cv2.MORPH_CLOSE,
    kernel,
    iterations=2
)


# Detect lines
lines = cv2.HoughLinesP(
    clean,
    rho=1,
    theta=np.pi/180,
    threshold=80,
    minLineLength=50,
    maxLineGap=15
)


walls = []


if lines is not None:

    for line in lines:

        x1, y1, x2, y2 = line

        dx = abs(x2-x1)
        dy = abs(y2-y1)


        if dx > dy:
            orientation = "horizontal"
        else:
            orientation = "vertical"


        walls.append(
            {
                "start":[int(x1),int(y1)],
                "end":[int(x2),int(y2)],
                "orientation":orientation
            }
        )


with open(OUTPUT,"w") as f:
    json.dump(
        walls,
        f,
        indent=4
    )


print("Detected walls:",len(walls))
print("Saved:",OUTPUT)