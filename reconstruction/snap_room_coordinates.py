import json
import os
from collections import defaultdict


INPUT_PATH = "outputs/reconstruction/orthogonal_rooms.json"

OUTPUT_PATH = "outputs/reconstruction/final_rooms.json"


# pixels within this distance are considered the same line
SNAP_DISTANCE = 10



def cluster_values(values):

    values = sorted(values)

    clusters = []

    current = [values[0]]


    for v in values[1:]:

        if abs(v - current[-1]) <= SNAP_DISTANCE:
            current.append(v)

        else:
            clusters.append(current)
            current = [v]


    clusters.append(current)


    # replace cluster by average

    mapping = {}

    for cluster in clusters:

        avg = round(
            sum(cluster) / len(cluster)
        )

        for value in cluster:
            mapping[value] = avg


    return mapping



def main():

    with open(INPUT_PATH) as f:
        rooms=json.load(f)


    x_values=[]
    y_values=[]


    # collect all coordinates

    for room in rooms:

        for x,y in room["polygon"]:

            x_values.append(x)
            y_values.append(y)


    x_map = cluster_values(x_values)
    y_map = cluster_values(y_values)



    output=[]


    for room in rooms:

        new_polygon=[]


        for x,y in room["polygon"]:

            new_polygon.append(
                [
                    x_map[x],
                    y_map[y]
                ]
            )


        output.append(
            {
                "id": room["id"],
                "area": room["area"],
                "polygon": new_polygon
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
            output,
            f,
            indent=4
        )


    print("Rooms processed:",len(output))
    print("Saved:",OUTPUT_PATH)



if __name__=="__main__":
    main()