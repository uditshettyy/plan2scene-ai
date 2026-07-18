import json
import cv2
import numpy as np
import math
import os


ROOMS_PATH = "outputs/geometry/rooms.json"

WALLS_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/room_wall_distance_report.json"


CONF_THRESHOLD = 0.3


def point_to_segment_distance(px, py, x1, y1, x2, y2):

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt(
            (px-x1)**2 +
            (py-y1)**2
        )

    t = (
        (px-x1)*dx +
        (py-y1)*dy
    ) / (
        dx*dx +
        dy*dy
    )


    t=max(0,min(1,t))


    nx=x1+t*dx
    ny=y1+t*dy


    return math.sqrt(
        (px-nx)**2 +
        (py-ny)**2
    )



def distance_to_walls(point, walls):

    px,py=point

    minimum=float("inf")


    for wall in walls:

        x1,y1=wall["start"]
        x2,y2=wall["end"]


        d=point_to_segment_distance(
            px,
            py,
            x1,
            y1,
            x2,
            y2
        )


        minimum=min(
            minimum,
            d
        )


    return round(minimum,2)



def analyze_room(room,walls):

    b=room["bbox"]

    points=[
        ("top",
         ((b["x1"]+b["x2"])/2,
          b["y1"])),

        ("bottom",
         ((b["x1"]+b["x2"])/2,
          b["y2"])),

        ("left",
         (b["x1"],
          (b["y1"]+b["y2"])/2)),

        ("right",
         (b["x2"],
          (b["y1"]+b["y2"])/2))
    ]


    result={}


    for name,p in points:

        result[name]=distance_to_walls(
            p,
            walls
        )


    return result



def main():

    with open(ROOMS_PATH) as f:
        rooms=json.load(f)


    with open(WALLS_PATH) as f:
        walls=json.load(f)



    report=[]


    for i,room in enumerate(rooms):

        if room["confidence"] < CONF_THRESHOLD:
            continue


        distances=analyze_room(
            room,
            walls
        )


        item={

            "id":i+1,

            "confidence":
                room["confidence"],

            "distances":
                distances,

            "bbox":
                room["bbox"]

        }


        report.append(item)


        print(
            "Room",
            i+1,
            "|",
            distances
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