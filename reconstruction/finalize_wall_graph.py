import json
import math
import os


INPUT = "outputs/geometry/split_wall_segments.json"

OUTPUT = "outputs/geometry/final_wall_segments.json"


SNAP_DISTANCE = 25


def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )


def snap_point(point, points):

    for p in points:

        if distance(point,p) < SNAP_DISTANCE:
            return p

    points.append(point)
    return point



with open(INPUT) as f:
    walls=json.load(f)



nodes=[]


new_walls=[]


for w in walls:

    s=snap_point(
        w["start"],
        nodes
    )

    e=snap_point(
        w["end"],
        nodes
    )


    if distance(s,e) > 5:

        new_walls.append(
            {
                "start":s,
                "end":e,
                "orientation":w["orientation"],
                "thickness":w["thickness"]
            }
        )



print("Original segments:",len(walls))
print("Final segments:",len(new_walls))


os.makedirs(
    "outputs/geometry",
    exist_ok=True
)


with open(OUTPUT,"w") as f:

    json.dump(
        new_walls,
        f,
        indent=4
    )


print("Saved:",OUTPUT)