import json
import os
import math


INPUT = "outputs/geometry/wall_vectors.json"
OUTPUT = "outputs/geometry/clean_wall_vectors.json"


os.makedirs("outputs/geometry", exist_ok=True)


with open(INPUT) as f:
    walls = json.load(f)


merged = []

DISTANCE_THRESHOLD = 8


def distance(a, b):
    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )


used = [False] * len(walls)


for i, wall in enumerate(walls):

    if used[i]:
        continue

    x1,y1 = wall["start"]
    x2,y2 = wall["end"]

    group = [wall]
    used[i] = True


    for j in range(i+1, len(walls)):

        if used[j]:
            continue

        other = walls[j]

        # same orientation only
        if wall["orientation"] != other["orientation"]:
            continue


        ox1,oy1 = other["start"]
        ox2,oy2 = other["end"]


        # check if lines are close
        if (
            distance(
                [x1,y1],
                [ox1,oy1]
            ) < DISTANCE_THRESHOLD
            or
            distance(
                [x2,y2],
                [ox2,oy2]
            ) < DISTANCE_THRESHOLD
        ):
            group.append(other)
            used[j] = True



    # average the grouped lines
    xs=[]
    ys=[]

    for g in group:
        xs.extend([
            g["start"][0],
            g["end"][0]
        ])

        ys.extend([
            g["start"][1],
            g["end"][1]
        ])


    if wall["orientation"] == "horizontal":

        y = int(sum(ys)/len(ys))

        merged.append(
            {
                "start":[min(xs),y],
                "end":[max(xs),y],
                "orientation":"horizontal"
            }
        )

    else:

        x = int(sum(xs)/len(xs))

        merged.append(
            {
                "start":[x,min(ys)],
                "end":[x,max(ys)],
                "orientation":"vertical"
            }
        )


with open(OUTPUT,"w") as f:
    json.dump(
        merged,
        f,
        indent=4
    )


print("Original lines:",len(walls))
print("Merged walls:",len(merged))
print("Saved:",OUTPUT)