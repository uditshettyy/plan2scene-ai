import cv2
import numpy as np
import json
import os


INPUT_PATH = "outputs/reconstruction/aligned_wall_mask.png"
OUTPUT_PATH = "outputs/reconstruction/generated_rooms.json"

DEBUG_PATH = "outputs/reconstruction/room_segmentation_debug.png"


# -----------------------------
# Parameters
# -----------------------------

# increase if walls have gaps
DILATION_SIZE = 15

# remove tiny regions
MIN_ROOM_AREA = 1000



def load_wall_mask():

    img = cv2.imread(
        INPUT_PATH,
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise FileNotFoundError(INPUT_PATH)

    return img



def close_wall_gaps(mask):

    kernel = np.ones(
        (DILATION_SIZE, DILATION_SIZE),
        np.uint8
    )


    closed = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=3
    )


    # slightly thicken walls
    closed = cv2.dilate(
        closed,
        kernel,
        iterations=2
    )


    return closed



def remove_outside(mask):

    """
    Find the outside empty region.
    Remaining empty regions are rooms.
    """


    # invert

    empty = cv2.bitwise_not(mask)


    h, w = empty.shape


    flood = empty.copy()


    flood_mask = np.zeros(
        (h+2,w+2),
        np.uint8
    )


    # start from corners
    cv2.floodFill(
        flood,
        flood_mask,
        (0,0),
        128
    )


    # outside pixels become 128

    rooms = np.where(
        flood == 0,
        255,
        0
    ).astype(np.uint8)


    return rooms



def extract_rooms(room_mask):

    contours, _ = cv2.findContours(
        room_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    rooms=[]


    for c in contours:

        area=cv2.contourArea(c)


        if area < MIN_ROOM_AREA:
            continue


        epsilon = 0.01 * cv2.arcLength(
            c,
            True
        )


        polygon=cv2.approxPolyDP(
            c,
            epsilon,
            True
        )


        points=[]

        for p in polygon:
            x,y=p[0]
            points.append(
                [
                    int(x),
                    int(y)
                ]
            )


        rooms.append(
            {
                "area":int(area),
                "polygon":points
            }
        )


    return rooms



def main():

    wall_mask=load_wall_mask()


    print("Loaded wall mask")


    repaired=close_wall_gaps(
        wall_mask
    )


    print("Walls repaired")


    room_mask=remove_outside(
        repaired
    )


    print("Outside removed")


    rooms=extract_rooms(
        room_mask
    )


    print(
        "Rooms detected:",
        len(rooms)
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
            rooms,
            f,
            indent=4
        )


    # debug image

    debug=cv2.cvtColor(
        room_mask,
        cv2.COLOR_GRAY2BGR
    )


    cv2.imwrite(
        DEBUG_PATH,
        debug
    )


    print("Saved:")
    print(OUTPUT_PATH)

    print(DEBUG_PATH)



if __name__=="__main__":
    main()