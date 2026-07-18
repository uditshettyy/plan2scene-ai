import json
import os
import math


ROOMS_PATH = "outputs/geometry/rooms.json"
WALLS_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/refined_room_polygons.json"


CONF_THRESHOLD = 0.5

SNAP_DISTANCE = 80



def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )



def nearest_horizontal(y, x1, x2, walls):

    best=None
    best_dist=9999


    for w in walls:

        if w["orientation"]!="horizontal":
            continue


        wy=w["start"][1]

        wx1=w["start"][0]
        wx2=w["end"][0]


        overlap = not (
            x2 < wx1 or
            x1 > wx2
        )

        if not overlap:
            continue


        d=abs(y-wy)


        if d < best_dist:

            best_dist=d
            best=wy


    if best_dist < SNAP_DISTANCE:
        return best


    return y



def nearest_vertical(x, y1, y2, walls):

    best=None
    best_dist=9999


    for w in walls:

        if w["orientation"]!="vertical":
            continue


        wx=w["start"][0]

        wy1=w["start"][1]
        wy2=w["end"][1]


        overlap=not(
            y2 < wy1 or
            y1 > wy2
        )


        if not overlap:
            continue


        d=abs(x-wx)


        if d < best_dist:

            best_dist=d
            best=wx



    if best_dist < SNAP_DISTANCE:
        return best


    return x



def refine_room(room,walls):

    b=room["bbox"]


    x1=b["x1"]
    y1=b["y1"]

    x2=b["x2"]
    y2=b["y2"]



    # snap boundaries

    top = nearest_horizontal(
        y1,
        x1,
        x2,
        walls
    )


    bottom = nearest_horizontal(
        y2,
        x1,
        x2,
        walls
    )


    left = nearest_vertical(
        x1,
        y1,
        y2,
        walls
    )


    right = nearest_vertical(
        x2,
        y1,
        y2,
        walls
    )



    polygon=[
        [round(left),round(top)],
        [round(right),round(top)],
        [round(right),round(bottom)],
        [round(left),round(bottom)]
    ]


    return polygon



def main():


    with open(ROOMS_PATH) as f:
        rooms=json.load(f)


    with open(WALLS_PATH) as f:
        walls=json.load(f)



    refined=[]


    count=1


    for room in rooms:


        if room["confidence"] < CONF_THRESHOLD:
            continue



        poly=refine_room(
            room,
            walls
        )


        refined.append(
            {
                "id":count,
                "confidence":room["confidence"],
                "polygon":poly
            }
        )


        count+=1



    os.makedirs(
        "outputs/reconstruction",
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            refined,
            f,
            indent=4
        )


    print(
        "Rooms created:",
        len(refined)
    )

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()