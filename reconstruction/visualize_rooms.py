import cv2
import json
import numpy as np
import random


IMAGE_PATH = "test.png"

ROOM_PATH = "outputs/reconstruction/valid_rooms.json"

OUTPUT_PATH = "outputs/reconstruction/rooms_overlay.png"



def main():

    img = cv2.imread(
        IMAGE_PATH
    )


    with open(ROOM_PATH) as f:
        rooms=json.load(f)



    overlay = img.copy()


    for room in rooms:

        points=np.array(
            room["polygon"],
            np.int32
        )

        points=points.reshape(
            (-1,1,2)
        )


        color=(
            random.randint(50,255),
            random.randint(50,255),
            random.randint(50,255)
        )


        cv2.polylines(
            overlay,
            [points],
            True,
            color,
            8
        )


        x,y=room["polygon"][0]


        cv2.putText(
            overlay,
            f"R{room['id']}",
            (x,y),
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            color,
            5
        )


    cv2.imwrite(
        OUTPUT_PATH,
        overlay
    )


    print("Saved:",OUTPUT_PATH)



if __name__=="__main__":
    main()