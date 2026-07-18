import json
import os
import math


INPUT = "outputs/geometry/clean_wall_vectors.json"
OUTPUT = "outputs/geometry/snapped_walls.json"


os.makedirs("outputs/geometry", exist_ok=True)


with open(INPUT) as f:
    walls = json.load(f)


SNAP_DISTANCE = 15


def snap(value, step=5):
    return round(value / step) * step


def close(a, b, threshold):
    return abs(a - b) <= threshold


snapped = []


for wall in walls:

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    if wall["orientation"] == "horizontal":

        # align y coordinate
        y = snap(y1)

        snapped.append(
            {
                "start":[
                    x1,
                    y
                ],
                "end":[
                    x2,
                    y
                ],
                "orientation":"horizontal"
            }
        )


    else:

        # align x coordinate
        x = snap(x1)

        snapped.append(
            {
                "start":[
                    x,
                    y1
                ],
                "end":[
                    x,
                    y2
                ],
                "orientation":"vertical"
            }
        )



# Merge touching walls

merged = []

used = [False] * len(snapped)


for i, wall in enumerate(snapped):

    if used[i]:
        continue

    current = wall
    used[i] = True


    for j in range(i+1, len(snapped)):

        if used[j]:
            continue

        other = snapped[j]


        if current["orientation"] != other["orientation"]:
            continue


        # horizontal merge
        if current["orientation"] == "horizontal":

            if close(
                current["start"][1],
                other["start"][1],
                SNAP_DISTANCE
            ):

                if not (
                    current["end"][0] < other["start"][0]
                    or
                    other["end"][0] < current["start"][0]
                ):

                    current["start"][0] = min(
                        current["start"][0],
                        other["start"][0]
                    )

                    current["end"][0] = max(
                        current["end"][0],
                        other["end"][0]
                    )

                    used[j] = True



        # vertical merge
        else:

            if close(
                current["start"][0],
                other["start"][0],
                SNAP_DISTANCE
            ):

                if not (
                    current["end"][1] < other["start"][1]
                    or
                    other["end"][1] < current["start"][1]
                ):

                    current["start"][1] = min(
                        current["start"][1],
                        other["start"][1]
                    )

                    current["end"][1] = max(
                        current["end"][1],
                        other["end"][1]
                    )

                    used[j] = True



    merged.append(current)



with open(OUTPUT,"w") as f:
    json.dump(
        merged,
        f,
        indent=4
    )


print("Input walls :",len(walls))
print("Snapped walls:",len(merged))
print("Saved:",OUTPUT)