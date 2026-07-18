import cv2
import json
import numpy as np
import os


IMAGE_PATH = "test.png"
ROOMS_PATH = "outputs/geometry/rooms.json"

OUTPUT_IMAGE = "outputs/reconstruction/wall_candidates_debug.png"


CONF_THRESHOLD = 0.5

# search area around room boundary
SEARCH = 40


def load_rooms():

    with open(ROOMS_PATH) as f:
        rooms = json.load(f)

    return [
        r for r in rooms
        if r["confidence"] >= CONF_THRESHOLD
    ]



def find_horizontal_line(gray, x1, x2, y):

    h, w = gray.shape

    y1=max(0, int(y-SEARCH))
    y2=min(h, int(y+SEARCH))

    x1=max(0,int(x1))
    x2=min(w,int(x2))


    region = gray[y1:y2, x1:x2]


    if region.size == 0:
        return None


    edges=cv2.Canny(
        region,
        50,
        150
    )


    score=np.sum(edges>0)/edges.size


    if score > 0.08:
        return score


    return None



def find_vertical_line(gray, y1, y2, x):

    h,w=gray.shape


    x1=max(0,int(x-SEARCH))
    x2=min(w,int(x+SEARCH))

    y1=max(0,int(y1))
    y2=min(h,int(y2))


    region=gray[y1:y2,x1:x2]


    if region.size==0:
        return None


    edges=cv2.Canny(
        region,
        50,
        150
    )


    score=np.sum(edges>0)/edges.size


    if score > 0.08:
        return score


    return None



def main():

    gray=cv2.imread(
        IMAGE_PATH,
        0
    )


    debug=cv2.cvtColor(
        gray,
        cv2.COLOR_GRAY2BGR
    )


    rooms=load_rooms()


    candidates=[]


    for i,room in enumerate(rooms):

        b=room["bbox"]


        x1=b["x1"]
        y1=b["y1"]
        x2=b["x2"]
        y2=b["y2"]


        sides={}


        sides["top"]=find_horizontal_line(
            gray,
            x1,
            x2,
            y1
        )

        sides["bottom"]=find_horizontal_line(
            gray,
            x1,
            x2,
            y2
        )


        sides["left"]=find_vertical_line(
            gray,
            y1,
            y2,
            x1
        )


        sides["right"]=find_vertical_line(
            gray,
            y1,
            y2,
            x2
        )


        print(
            "Room",
            i+1,
            sides
        )


        candidates.append(
            {
                "room_id":i+1,
                "bbox":b,
                "candidates":sides
            }
        )


        # draw bbox

        cv2.rectangle(
            debug,
            (int(x1),int(y1)),
            (int(x2),int(y2)),
            (255,0,0),
            2
        )


    os.makedirs(
        "outputs/reconstruction",
        exist_ok=True
    )


    with open(
        "outputs/reconstruction/wall_candidates.json",
        "w"
    ) as f:

        json.dump(
            candidates,
            f,
            indent=4
        )


    cv2.imwrite(
        OUTPUT_IMAGE,
        debug
    )


    print()
    print("Saved:")
    print(OUTPUT_IMAGE)
    print("outputs/reconstruction/wall_candidates.json")



if __name__=="__main__":
    main()