import cv2
import json
import numpy as np
import os


IMAGE_PATH = "test.png"

ROOM_PATH = "outputs/reconstruction/final_room_faces.json"

OUTPUT_PATH = "outputs/reconstruction/final_rooms_overlay.png"



def main():

    img=cv2.imread(
        IMAGE_PATH
    )


    with open(ROOM_PATH) as f:
        rooms=json.load(f)


    overlay=img.copy()


    for room in rooms:

        pts=np.array(
            room["polygon"],
            dtype=np.int32
        )


        cv2.polylines(
            overlay,
            [pts],
            True,
            (0,255,0),
            5
        )


        cx=int(
            np.mean(pts[:,0])
        )

        cy=int(
            np.mean(pts[:,1])
        )


        cv2.putText(
            overlay,
            f"R{room['id']}",
            (cx,cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (0,0,255),
            5
        )


    cv2.imwrite(
        OUTPUT_PATH,
        overlay
    )


    print(
        "Saved:",
        OUTPUT_PATH
    )


if __name__=="__main__":
    main()