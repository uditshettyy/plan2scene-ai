import cv2
import json
import numpy as np


IMAGE = "test.png"

ROOMS = "outputs/reconstruction/valid_room_polygons.json"

OUTPUT = "outputs/reconstruction/valid_rooms_overlay.png"


with open(ROOMS) as f:
    rooms=json.load(f)


img=cv2.imread(IMAGE)


for room in rooms:

    pts=np.array(
        room["polygon"],
        np.int32
    )

    pts=pts.reshape((-1,1,2))


    cv2.polylines(
        img,
        [pts],
        True,
        (0,0,255),
        4
    )


    x,y=room["polygon"][0]


    cv2.putText(
        img,
        f"R{room['id']}",
        (x,y-10),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255,0,0),
        4
    )


cv2.imwrite(
    OUTPUT,
    img
)


print("Saved:",OUTPUT)