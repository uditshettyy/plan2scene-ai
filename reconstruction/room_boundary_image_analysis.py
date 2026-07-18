import json
import cv2
import numpy as np
import os


ROOMS_PATH = "outputs/geometry/rooms.json"

IMAGE_PATH = "test.png"

OUTPUT_IMAGE = "outputs/reconstruction/room_boundary_analysis.png"

OUTPUT_JSON = "outputs/reconstruction/room_boundary_report.json"


CONF_THRESHOLD = 0.5

SEARCH_DISTANCE = 40



def check_region(img, x1, y1, x2, y2):

    h,w = img.shape

    x1=max(0,int(x1))
    y1=max(0,int(y1))
    x2=min(w,int(x2))
    y2=min(h,int(y2))


    crop = img[y1:y2,x1:x2]

    if crop.size == 0:
        return 0


    # dark pixels represent walls/lines
    dark = np.sum(crop < 100)

    total = crop.size


    return round(
        dark / total,
        4
    )



def analyze_room(room,img):

    b=room["bbox"]

    x1=b["x1"]
    y1=b["y1"]
    x2=b["x2"]
    y2=b["y2"]


    checks={}


    # top
    checks["top"] = check_region(
        img,
        x1,
        y1-SEARCH_DISTANCE,
        x2,
        y1+SEARCH_DISTANCE
    )


    # bottom
    checks["bottom"] = check_region(
        img,
        x1,
        y2-SEARCH_DISTANCE,
        x2,
        y2+SEARCH_DISTANCE
    )


    # left
    checks["left"] = check_region(
        img,
        x1-SEARCH_DISTANCE,
        y1,
        x1+SEARCH_DISTANCE,
        y2
    )


    # right
    checks["right"] = check_region(
        img,
        x2-SEARCH_DISTANCE,
        y1,
        x2+SEARCH_DISTANCE,
        y2
    )


    return checks



def draw_debug(img,room_id,room):

    b=room["bbox"]

    cv2.rectangle(
        img,
        (
            int(b["x1"]),
            int(b["y1"])
        ),
        (
            int(b["x2"]),
            int(b["y2"])
        ),
        (0,0,255),
        4
    )


    cv2.putText(
        img,
        f"R{room_id}",
        (
            int(b["x1"]),
            int(b["y1"])-10
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0,0,255),
        4
    )



def main():

    with open(ROOMS_PATH) as f:
        rooms=json.load(f)


    img=cv2.imread(
        IMAGE_PATH,
        0
    )


    debug=cv2.cvtColor(
        img,
        cv2.COLOR_GRAY2BGR
    )


    report=[]


    for i,room in enumerate(rooms):

        if room["confidence"] < CONF_THRESHOLD:
            continue


        result=analyze_room(
            room,
            img
        )


        print(
            "Room",
            i+1,
            result
        )


        report.append(
            {
                "id":i+1,
                "confidence":room["confidence"],
                "boundary_dark_ratio":result
            }
        )


        draw_debug(
            debug,
            i+1,
            room
        )


    os.makedirs(
        "outputs/reconstruction",
        exist_ok=True
    )


    with open(
        OUTPUT_JSON,
        "w"
    ) as f:
        json.dump(
            report,
            f,
            indent=4
        )


    cv2.imwrite(
        OUTPUT_IMAGE,
        debug
    )


    print()
    print("Saved:")
    print(OUTPUT_JSON)
    print(OUTPUT_IMAGE)



if __name__=="__main__":
    main()