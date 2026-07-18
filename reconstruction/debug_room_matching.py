import json
import cv2
import numpy as np


IMG="test.png"

YOLO_PATH="outputs/geometry/rooms.json"

FACE_PATH="outputs/reconstruction/final_room_faces.json"

OUT="outputs/reconstruction/room_matching_debug.png"



img=cv2.imread(IMG)



with open(YOLO_PATH) as f:
    yolo=json.load(f)


with open(FACE_PATH) as f:
    faces=json.load(f)



# draw geometry faces

for i,face in enumerate(faces):

    pts=np.array(
        face["polygon"],
        dtype=np.int32
    )


    cv2.polylines(
        img,
        [pts],
        True,
        (0,255,0),
        5
    )


    cx=int(np.mean(pts[:,0]))
    cy=int(np.mean(pts[:,1]))


    cv2.putText(
        img,
        f"F{i+1}",
        (cx,cy),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0,0,255),
        4
    )



# draw YOLO rooms

for i,r in enumerate(yolo):

    if r["confidence"] < 0.5:
        continue


    b=r["bbox"]

    p1=(
        int(b["x1"]),
        int(b["y1"])
    )

    p2=(
        int(b["x2"]),
        int(b["y2"])
    )


    cv2.rectangle(
        img,
        p1,
        p2,
        (255,0,0),
        3
    )


    cv2.putText(
        img,
        f"Y{i+1}",
        p1,
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255,0,0),
        3
    )


cv2.imwrite(
    OUT,
    img
)


print("Saved:",OUT)