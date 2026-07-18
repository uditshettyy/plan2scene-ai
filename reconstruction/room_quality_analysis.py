import json
import cv2
import numpy as np
import os


ROOMS_PATH = "outputs/geometry/rooms.json"

WALL_MASK_PATH = "outputs/geometry/wall_mask.png"

OUTPUT_PATH = "outputs/reconstruction/room_quality_report.json"


CONF_THRESHOLD = 0.3

# How many pixels around room boundary to check
BOUNDARY_WIDTH = 15



def load_data():

    with open(ROOMS_PATH) as f:
        rooms = json.load(f)

    wall_mask = cv2.imread(
        WALL_MASK_PATH,
        0
    )

    return rooms, wall_mask



def create_room_mask(room, shape):

    mask = np.zeros(
        shape,
        dtype=np.uint8
    )

    b = room["bbox"]

    x1=int(b["x1"])
    y1=int(b["y1"])
    x2=int(b["x2"])
    y2=int(b["y2"])


    cv2.rectangle(
        mask,
        (x1,y1),
        (x2,y2),
        255,
        -1
    )

    return mask



def boundary_from_mask(mask):

    kernel=np.ones(
        (3,3),
        np.uint8
    )

    erosion=cv2.erode(
        mask,
        kernel,
        iterations=1
    )

    boundary = mask - erosion

    return boundary



def calculate_wall_support(room_mask, wall_mask):

    boundary = boundary_from_mask(
        room_mask
    )


    # expand boundary area

    kernel=cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            BOUNDARY_WIDTH,
            BOUNDARY_WIDTH
        )
    )


    search_area=cv2.dilate(
        boundary,
        kernel
    )


    wall_pixels=np.sum(
        wall_mask > 0
    )


    if wall_pixels == 0:
        return 0


    matched=np.sum(
        (search_area > 0)
        &
        (wall_mask > 0)
    )


    boundary_pixels=np.sum(
        search_area > 0
    )


    return round(
        matched / boundary_pixels,
        3
    )



def main():

    rooms, wall_mask = load_data()


    report=[]


    for i,room in enumerate(rooms):

        if room["confidence"] < CONF_THRESHOLD:
            continue


        room_mask=create_room_mask(
            room,
            wall_mask.shape
        )


        score=calculate_wall_support(
            room_mask,
            wall_mask
        )


        report.append(
            {
                "id":i+1,

                "confidence":
                    room["confidence"],

                "wall_support":
                    score,

                "bbox":
                    room["bbox"]
            }
        )


        print(
            "Room",
            i+1,
            "| confidence:",
            room["confidence"],
            "| wall support:",
            score
        )



    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            report,
            f,
            indent=4
        )


    print()
    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()