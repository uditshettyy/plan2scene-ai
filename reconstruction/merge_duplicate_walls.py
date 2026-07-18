import json
import math
import os


INPUT = "outputs/geometry/wall_segments.json"

OUTPUT = "outputs/geometry/merged_wall_segments.json"


DIST_THRESHOLD = 30


def distance(a,b):
    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )


def same_orientation(a,b):

    return a["orientation"] == b["orientation"]



def similar_wall(a,b):

    if not same_orientation(a,b):
        return False


    if a["orientation"]=="horizontal":

        return (
            abs(a["start"][1]-b["start"][1]) < DIST_THRESHOLD
            and
            abs(a["end"][1]-b["end"][1]) < DIST_THRESHOLD
        )


    else:

        return (
            abs(a["start"][0]-b["start"][0]) < DIST_THRESHOLD
            and
            abs(a["end"][0]-b["end"][0]) < DIST_THRESHOLD
        )



def merge_wall(a,b):

    points=[
        a["start"],
        a["end"],
        b["start"],
        b["end"]
    ]


    if a["orientation"]=="horizontal":

        points.sort(key=lambda p:p[0])

    else:

        points.sort(key=lambda p:p[1])


    return {
        "orientation":a["orientation"],
        "start":points[0],
        "end":points[-1],
        "thickness":max(
            a["thickness"],
            b["thickness"]
        )
    }



with open(INPUT) as f:
    walls=json.load(f)



merged=[]


for wall in walls:

    found=False

    for i,m in enumerate(merged):

        if similar_wall(wall,m):

            merged[i]=merge_wall(
                wall,
                m
            )

            found=True
            break


    if not found:
        merged.append(wall)



print("Original walls:",len(walls))
print("Merged walls:",len(merged))


os.makedirs(
    "outputs/geometry",
    exist_ok=True
)


with open(OUTPUT,"w") as f:

    json.dump(
        merged,
        f,
        indent=4
    )


print("Saved:",OUTPUT)