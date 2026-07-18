import json
import os
import math


INPUT_PATH = "outputs/reconstruction/generated_rooms.json"

OUTPUT_PATH = "outputs/reconstruction/clean_rooms.json"


# minimum area to keep
MIN_AREA = 3000


# -----------------------------
# Geometry helpers
# -----------------------------

def distance(a, b):
    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )


def polygon_area(points):

    area = 0

    n = len(points)

    for i in range(n):
        x1,y1 = points[i]
        x2,y2 = points[(i+1)%n]

        area += (
            x1*y2 -
            x2*y1
        )

    return abs(area)/2



def remove_close_points(points, threshold=20):

    cleaned=[]

    for p in points:

        if not cleaned:
            cleaned.append(p)
            continue


        if distance(
            p,
            cleaned[-1]
        ) > threshold:

            cleaned.append(p)


    return cleaned



def simplify_collinear(points):

    if len(points) < 3:
        return points


    result=[]


    n=len(points)


    for i in range(n):

        prev = points[i-1]
        curr = points[i]
        nxt = points[(i+1)%n]


        # vectors

        v1=(
            curr[0]-prev[0],
            curr[1]-prev[1]
        )

        v2=(
            nxt[0]-curr[0],
            nxt[1]-curr[1]
        )


        cross = (
            v1[0]*v2[1] -
            v1[1]*v2[0]
        )


        # keep corners only

        if abs(cross) > 5:

            result.append(curr)


    return result



# -----------------------------
# Main
# -----------------------------

def main():

    with open(INPUT_PATH) as f:
        rooms=json.load(f)


    cleaned_rooms=[]


    for idx,room in enumerate(rooms):

        polygon = room["polygon"]


        # remove noisy close points

        polygon = remove_close_points(
            polygon
        )


        # remove straight line points

        polygon = simplify_collinear(
            polygon
        )


        area = polygon_area(
            polygon
        )


        if area < MIN_AREA:
            continue


        cleaned_rooms.append(
            {
                "id": idx+1,
                "area": int(area),
                "polygon": polygon
            }
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
            cleaned_rooms,
            f,
            indent=4
        )


    print("Original rooms:",len(rooms))
    print("Clean rooms:",len(cleaned_rooms))

    print(
        "Saved:",
        OUTPUT_PATH
    )


if __name__=="__main__":
    main()