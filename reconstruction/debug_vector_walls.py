import cv2
import json
import numpy as np


IMAGE="test.png"

WALLS="outputs/reconstruction/completed_vector_walls.json"

OUTPUT="outputs/reconstruction/vector_wall_overlay.png"


img=cv2.imread(IMAGE)


with open(WALLS) as f:
    walls=json.load(f)


for w in walls:

    p1=tuple(w["start"])
    p2=tuple(w["end"])

    cv2.line(
        img,
        p1,
        p2,
        (0,0,255),
        6
    )


cv2.imwrite(
    OUTPUT,
    img
)

print("Saved:",OUTPUT)